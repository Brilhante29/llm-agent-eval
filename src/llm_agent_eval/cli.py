import argparse
import json
import math
import platform
import sys
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_TASKS = "data/fixtures/tasks.jsonl"
DEFAULT_TRACES = "data/fixtures/traces.jsonl"
DEFAULT_OUTPUT = "benchmarks/results/agent-eval-baseline.json"
COMMAND = (
    "python -m llm_agent_eval benchmark --tasks data/fixtures/tasks.jsonl "
    "--traces data/fixtures/traces.jsonl "
    "--output benchmarks/results/agent-eval-baseline.json"
)


class TraceValidationError(ValueError):
    """Raised when supplied evaluation evidence is incomplete or malformed."""


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TraceValidationError(f"{path}:{line_number}: invalid JSON") from exc
        if not isinstance(value, dict):
            raise TraceValidationError(f"{path}:{line_number}: expected an object")
        records.append(value)
    if not records:
        raise TraceValidationError(f"{path}: expected at least one record")
    return records


def _require_exact_keys(
    record: dict[str, Any], required: set[str], label: str
) -> None:
    missing = required - record.keys()
    extra = record.keys() - required
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing {sorted(missing)}")
        if extra:
            details.append(f"unexpected {sorted(extra)}")
        raise TraceValidationError(f"{label}: {', '.join(details)}")


def _non_negative_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TraceValidationError(f"{label}: expected a number")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise TraceValidationError(f"{label}: expected a finite non-negative number")
    return number


def validate_tasks(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    seen: set[str] = set()
    required = {"id", "expected_output", "expected_tool_calls"}
    for index, task in enumerate(records, start=1):
        label = f"task[{index}]"
        _require_exact_keys(task, required, label)
        task_id = task["id"]
        if not isinstance(task_id, str) or not task_id.strip() or task_id in seen:
            raise TraceValidationError(f"{label}.id: expected a unique non-empty string")
        if not isinstance(task["expected_output"], str):
            raise TraceValidationError(f"{label}.expected_output: expected a string")
        expected_tools = task["expected_tool_calls"]
        if not isinstance(expected_tools, list) or not all(
            isinstance(name, str) and name.strip() for name in expected_tools
        ):
            raise TraceValidationError(
                f"{label}.expected_tool_calls: expected a list of tool names"
            )
        seen.add(task_id)
        tasks.append(task)
    return tasks


def validate_traces(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    traces: list[dict[str, Any]] = []
    seen: set[str] = set()
    required = {"task_id", "output", "tool_calls", "latency_ms", "cost_usd"}
    tool_required = {"name"}
    for index, trace in enumerate(records, start=1):
        label = f"trace[{index}]"
        _require_exact_keys(trace, required, label)
        task_id = trace["task_id"]
        if not isinstance(task_id, str) or not task_id.strip() or task_id in seen:
            raise TraceValidationError(
                f"{label}.task_id: expected a unique non-empty string"
            )
        if not isinstance(trace["output"], str):
            raise TraceValidationError(f"{label}.output: expected a string")
        tool_calls = trace["tool_calls"]
        if not isinstance(tool_calls, list):
            raise TraceValidationError(f"{label}.tool_calls: expected a list")
        for tool_index, call in enumerate(tool_calls, start=1):
            if not isinstance(call, dict):
                raise TraceValidationError(
                    f"{label}.tool_calls[{tool_index}]: expected an object"
                )
            _require_exact_keys(call, tool_required, f"{label}.tool_calls[{tool_index}]")
            if not isinstance(call["name"], str) or not call["name"].strip():
                raise TraceValidationError(
                    f"{label}.tool_calls[{tool_index}].name: expected a tool name"
                )
        normalized = dict(trace)
        normalized["latency_ms"] = _non_negative_number(
            trace["latency_ms"], f"{label}.latency_ms"
        )
        normalized["cost_usd"] = _non_negative_number(
            trace["cost_usd"], f"{label}.cost_usd"
        )
        seen.add(task_id)
        traces.append(normalized)
    return traces


def _normalized_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    rank = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[rank]


def evaluate(
    tasks_path: str | Path = DEFAULT_TASKS,
    traces_path: str | Path = DEFAULT_TRACES,
) -> dict[str, Any]:
    tasks = validate_tasks(load_jsonl(tasks_path))
    traces = validate_traces(load_jsonl(traces_path))
    trace_by_task = {trace["task_id"]: trace for trace in traces}
    task_ids = {task["id"] for task in tasks}
    trace_ids = set(trace_by_task)
    if task_ids != trace_ids:
        missing = sorted(task_ids - trace_ids)
        unknown = sorted(trace_ids - task_ids)
        raise TraceValidationError(
            f"trace/task mismatch: missing={missing}, unknown={unknown}"
        )

    rows: list[dict[str, Any]] = []
    latency_samples: list[float] = []
    cost_samples: list[float] = []
    for task in tasks:
        trace = trace_by_task[task["id"]]
        observed_tools = [call["name"] for call in trace["tool_calls"]]
        outcome_success = _normalized_text(trace["output"]) == _normalized_text(
            task["expected_output"]
        )
        tool_selection_success = observed_tools == task["expected_tool_calls"]
        latency_samples.append(trace["latency_ms"])
        cost_samples.append(trace["cost_usd"])
        rows.append(
            {
                "task_id": task["id"],
                "outcome_success": outcome_success,
                "tool_selection_success": tool_selection_success,
                "expected_tool_calls": task["expected_tool_calls"],
                "observed_tool_calls": observed_tools,
                "latency_ms": trace["latency_ms"],
                "cost_usd": trace["cost_usd"],
            }
        )

    task_samples = [1.0 if row["outcome_success"] else 0.0 for row in rows]
    tool_samples = [
        1.0 if row["tool_selection_success"] else 0.0 for row in rows
    ]
    task_success = sum(task_samples) / len(task_samples)
    tool_accuracy = sum(tool_samples) / len(tool_samples)
    total_cost = sum(cost_samples)
    return {
        "project": "llm-agent-eval",
        "metric": "task_success_rate",
        "value": round(task_success, 4),
        "unit": "ratio",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": COMMAND,
        "repeat": len(rows),
        "samples": task_samples,
        "summary": {
            "task_count": len(rows),
            "task_success_rate": round(task_success, 4),
            "tool_selection_accuracy": round(tool_accuracy, 4),
            "average_latency_ms": round(sum(latency_samples) / len(rows), 4),
            "p95_latency_ms": round(_percentile(latency_samples, 0.95), 4),
            "total_cost_usd": round(total_cost, 8),
            "average_cost_usd": round(total_cost / len(rows), 8),
            "malformed_trace_count": 0,
        },
        "environment": {
            "runtime": f"python-{platform.python_version()}",
            "mode": "offline-supplied-trace-evaluation",
            "tasks_source": str(tasks_path),
            "traces_source": str(traces_path),
        },
        "tasks": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate supplied agent execution traces; this command does not run an agent."
    )
    parser.add_argument("command", choices=["benchmark"], nargs="?", default="benchmark")
    parser.add_argument("--tasks", default=DEFAULT_TASKS)
    parser.add_argument("--traces", default=DEFAULT_TRACES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        result = evaluate(args.tasks, args.traces)
    except (OSError, TraceValidationError) as exc:
        print(f"evaluation failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
