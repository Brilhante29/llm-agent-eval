from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class AgentRunError(ValueError):
    pass


OpenUrl = Callable[[Request, float], Any]


def _open(request: Request, timeout: float) -> Any:
    return urlopen(request, timeout=timeout)


def _sha256(path: str | Path) -> str:
    return f"sha256:{hashlib.sha256(Path(path).read_bytes()).hexdigest()}"


def load_agent_inputs(path: str | Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    seen: set[str] = set()
    for line_number, line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AgentRunError(f"{path}:{line_number}: invalid JSON") from exc
        if not isinstance(record, dict) or set(record) != {"id", "instruction"}:
            raise AgentRunError(f"{path}:{line_number}: expected id and instruction")
        if not all(isinstance(record[key], str) and record[key].strip() for key in record):
            raise AgentRunError(f"{path}:{line_number}: fields must be non-empty text")
        if record["id"] in seen:
            raise AgentRunError(f"{path}:{line_number}: duplicate ID")
        seen.add(record["id"])
        records.append(record)
    if not records:
        raise AgentRunError(f"{path}: expected at least one task")
    return records


class OpenAICompatiblePlanner:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        model_digest: str,
        timeout_seconds: float,
        provider_id: str = "openai-compatible-http",
        api_key: str | None = None,
        opener: OpenUrl = _open,
    ) -> None:
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise AgentRunError("base URL must be HTTP(S)")
        if parsed.username or parsed.password:
            raise AgentRunError("base URL must not contain credentials")
        if re.fullmatch(r"sha256:[0-9a-f]{64}", model_digest) is None:
            raise AgentRunError("a full sha256 model digest is required")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.model_digest = model_digest
        self.timeout_seconds = timeout_seconds
        self.provider_id = provider_id
        self.api_key = api_key
        self._opener = opener

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] | None = None,
        *,
        opener: OpenUrl = _open,
    ) -> "OpenAICompatiblePlanner":
        values = os.environ if environment is None else environment
        required = ("AGENT_BASE_URL", "AGENT_MODEL", "AGENT_MODEL_DIGEST")
        missing = [key for key in required if not values.get(key)]
        if missing:
            raise AgentRunError("missing environment: " + ", ".join(missing))
        return cls(
            base_url=values["AGENT_BASE_URL"],
            model=values["AGENT_MODEL"],
            model_digest=values["AGENT_MODEL_DIGEST"],
            timeout_seconds=float(values.get("AGENT_TIMEOUT_SECONDS", "30")),
            provider_id=values.get("AGENT_PROVIDER_ID", "openai-compatible-http"),
            api_key=values.get("AGENT_API_KEY") or None,
            opener=opener,
        )

    def plan(self, instruction: str) -> tuple[str, dict[str, int]]:
        endpoint = self.base_url
        if not endpoint.endswith("/chat/completions"):
            endpoint += "/chat/completions"
        system = (
            "Route the task to exactly one tool. Available tools: "
            "calculator for arithmetic; retriever for knowledge lookup; "
            "formatter for converting a decimal to percent. Return JSON only: "
            '{"tool":"tool_name","argument":"value passed to the tool"}.'
        )
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": instruction},
                ],
                "temperature": 0,
                "max_tokens": 48,
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(endpoint, data=payload, headers=headers, method="POST")
        with self._opener(request, self.timeout_seconds) as response:
            document = json.loads(response.read().decode("utf-8"))
        try:
            content = document["choices"][0]["message"]["content"]
            usage = document["usage"]
            tokens = {
                "prompt": int(usage["prompt_tokens"]),
                "completion": int(usage["completion_tokens"]),
            }
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            raise AgentRunError("provider response lacks content or token usage") from exc
        if not isinstance(content, str) or not content.strip():
            raise AgentRunError("provider returned empty content")
        return content, tokens


def parse_decision(content: str) -> tuple[str, str]:
    start = content.find("{")
    end = content.rfind("}")
    if start < 0 or end <= start:
        raise AgentRunError("planner did not return a JSON object")
    try:
        decision = json.loads(content[start : end + 1])
    except json.JSONDecodeError as exc:
        raise AgentRunError("planner returned invalid JSON") from exc
    if not isinstance(decision, dict) or set(decision) != {"tool", "argument"}:
        raise AgentRunError("planner decision must contain tool and argument")
    if not all(isinstance(decision[key], str) and decision[key].strip() for key in decision):
        raise AgentRunError("planner decision fields must be non-empty text")
    return decision["tool"], decision["argument"]


def execute_tool(name: str, argument: str) -> str:
    if name == "calculator":
        match = re.fullmatch(
            r"\s*(-?\d+(?:\.\d+)?)\s*([+\-*/])\s*(-?\d+(?:\.\d+)?)\s*",
            argument,
        )
        if match is None:
            raise AgentRunError("calculator expects one binary expression")
        left, operator, right = float(match[1]), match[2], float(match[3])
        operations = {
            "+": lambda: left + right,
            "-": lambda: left - right,
            "*": lambda: left * right,
            "/": lambda: left / right,
        }
        value = operations[operator]()
        return str(int(value)) if value.is_integer() else str(value)
    if name == "formatter":
        match = re.search(r"-?\d+(?:\.\d+)?", argument)
        if match is None:
            raise AgentRunError("formatter expects a decimal")
        value = float(match.group()) * 100
        text = f"{value:.6f}".rstrip("0").rstrip(".")
        return f"{text}%"
    if name == "retriever":
        tokens = set(re.findall(r"[a-z0-9]+", argument.casefold()))
        corpus = {
            "recall_at_k": {"retrieval", "relevant", "documents", "top", "metric"},
            "kumo": {"local", "cloud", "aws", "emulator"},
            "outbox_pattern": {"transactional", "message", "event", "delivery", "pattern"},
        }
        return max(corpus, key=lambda key: len(tokens & corpus[key]))
    raise AgentRunError(f"unknown tool: {name}")


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def run_agent(
    *,
    planner: OpenAICompatiblePlanner,
    inputs_path: str | Path,
    traces_path: str | Path,
    provenance_path: str | Path,
    producer_source_commit: str = "unverified",
    producer_image_digest: str = "unverified",
) -> dict[str, Any]:
    inputs = load_agent_inputs(inputs_path)
    traces: list[dict[str, Any]] = []
    latencies: list[float] = []
    prompt_tokens = completion_tokens = decision_failures = tool_failures = 0
    for task in inputs:
        started = time.perf_counter_ns()
        content, usage = planner.plan(task["instruction"])
        prompt_tokens += usage["prompt"]
        completion_tokens += usage["completion"]
        calls: list[dict[str, str]] = []
        output = ""
        try:
            tool, argument = parse_decision(content)
            calls = [{"name": tool}]
        except AgentRunError:
            decision_failures += 1
        else:
            try:
                output = execute_tool(tool, argument)
            except (AgentRunError, ZeroDivisionError):
                tool_failures += 1
        latency = (time.perf_counter_ns() - started) / 1_000_000
        latencies.append(latency)
        traces.append(
            {
                "task_id": task["id"],
                "output": output,
                "tool_calls": calls,
                "latency_ms": round(latency, 6),
                "cost_usd": 0.0,
            }
        )

    trace_output = Path(traces_path)
    trace_output.parent.mkdir(parents=True, exist_ok=True)
    trace_output.write_text(
        "".join(json.dumps(trace, separators=(",", ":")) + "\n" for trace in traces),
        encoding="utf-8",
    )
    provenance = {
        "schema_version": 1,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "graph": ["planner_model", "tool_executor", "trace_evaluator"],
        "provider": {
            "id": planner.provider_id,
            "interface": "openai-compatible-chat-completions",
            "model": planner.model,
            "model_digest": planner.model_digest,
        },
        "producer": {
            "source_commit": producer_source_commit,
            "image_digest": producer_image_digest,
        },
        "execution": {
            "measured_tasks": len(inputs),
            "decision_failures": decision_failures,
            "tool_failures": tool_failures,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "latency_ms": {
                "mean": round(sum(latencies) / len(latencies), 6),
                "p95": round(_p95(latencies), 6),
            },
            "cost_usd": 0.0,
        },
        "artifacts": {
            "inputs_sha256": _sha256(inputs_path),
            "traces_sha256": _sha256(trace_output),
        },
    }
    output = Path(provenance_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    return provenance
