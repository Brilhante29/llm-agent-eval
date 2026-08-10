from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "benchmarks" / "results" / "agent-eval-baseline.json"
V2_PATH = ROOT / "benchmarks" / "publication" / "agent-eval-baseline-v2.json"
SCHEMA_PATH = ROOT / ".portfolio" / "contracts" / "benchmark-result-v2.schema.json"
CONFIG_PATH = ROOT / "benchmarks" / "config" / "agent-eval-baseline-v2.json"
FIXTURE_PATH = ROOT / "data" / "fixtures"
INPUTS_PATH = FIXTURE_PATH / "agent-inputs.jsonl"
TRACES_PATH = FIXTURE_PATH / "traces.jsonl"
TRACE_PROVENANCE_PATH = FIXTURE_PATH / "traces.provenance.json"
LOCK_PATH = ROOT / "requirements-validation.lock"
PRODUCER_PATH = ROOT / "tools" / "generate-publication-benchmark.py"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must contain an object")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256_file(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def load_producer() -> Any:
    spec = importlib.util.spec_from_file_location("publication_benchmark", PRODUCER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load publication producer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git_has_commit(commit: str) -> bool:
    completed = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={ROOT}",
            "-C",
            str(ROOT),
            "cat-file",
            "-e",
            f"{commit}^{{commit}}",
        ],
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-git", action="store_true")
    args = parser.parse_args()

    manifest = (ROOT / "project.yaml").read_text(encoding="utf-8")
    published = re.search(r"(?m)^status:\s*published\s*$", manifest) is not None
    lock = LOCK_PATH.read_text(encoding="utf-8")
    require("jsonschema==4.26.0" in lock, "jsonschema is not pinned")
    config = read_json(CONFIG_PATH)
    require(config["measured_tasks"] == 8, "publication config task count mismatch")
    require(config["concurrency"] == 1, "publication config concurrency mismatch")
    if not V2_PATH.is_file():
        require(not published, "published project requires V2 evidence")
        print("publication_evidence=not-applicable")
        return

    import jsonschema

    v1 = read_json(V1_PATH)
    v2 = read_json(V2_PATH)
    schema = read_json(SCHEMA_PATH)
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    ).validate(v2)

    require(v1.get("project") == "llm-agent-eval", "unexpected V1 project")
    require(v2.get("project") == "llm-agent-eval", "unexpected V2 project")
    require(
        v2.get("benchmark_id") == "local-llm-tool-agent-v2",
        "unexpected benchmark id",
    )
    require(v1.get("metric") == "task_success_rate", "unexpected primary metric")
    require(v1.get("value") == 0.625, "unexpected task success baseline")
    summary = v1.get("summary", {})
    require(summary.get("task_count") == 8, "expected eight tasks")
    require(summary.get("measured_iterations") == 8, "measured task count mismatch")
    require(summary.get("tool_selection_accuracy") == 0.875, "tool accuracy mismatch")
    require(summary.get("average_latency_ms") == 986.4655, "latency baseline mismatch")
    require(summary.get("p95_latency_ms") == 3006.9626, "p95 baseline mismatch")
    require(summary.get("total_cost_usd") == 0.0, "cost baseline mismatch")
    require(v1.get("repeat") == 1, "task count must not be reported as run repetition")
    require(v1.get("measured_iterations") == 8, "top-level measured task count mismatch")

    metric = v2["metrics"][0]
    require(metric["name"] == "task_success_rate", "unexpected V2 metric")
    require(metric["value"] == v1["value"], "V1/V2 value mismatch")
    require(metric["samples"] == v1["samples"], "V1/V2 samples mismatch")
    require(metric["failures"] == 0, "publication contains failures")
    require(v2["execution"]["repeat"] == 1, "execution repeat mismatch")
    require(v2["workload"]["measured_iterations"] == 8, "workload task count mismatch")
    require(v2["workload"]["warmup_iterations"] == 0, "unexpected warmup")
    require(
        v2["provenance"]["artifact_digest"] == sha256_file(V1_PATH),
        "raw artifact digest mismatch",
    )
    require(
        re.fullmatch(r"sha256:[0-9a-f]{64}", v2["provenance"]["image_digest"])
        is not None,
        "invalid image digest",
    )
    require(v2["comparability_key"] == config["comparability_key"], "comparability key mismatch")

    trace_provenance = read_json(TRACE_PROVENANCE_PATH)
    provider = trace_provenance.get("provider", {})
    producer_state = trace_provenance.get("producer", {})
    execution = trace_provenance.get("execution", {})
    artifacts = trace_provenance.get("artifacts", {})
    require(trace_provenance.get("graph") == ["planner_model", "tool_executor", "trace_evaluator"], "agent graph mismatch")
    require(provider.get("model") == config["model"], "agent model mismatch")
    require(provider.get("model_digest") == config["model_digest"], "agent model digest mismatch")
    require(execution.get("measured_tasks") == 8, "agent task count mismatch")
    require(execution.get("decision_failures") == 1, "decision failure count mismatch")
    require(execution.get("tool_failures") == 2, "tool failure count mismatch")
    require(execution.get("prompt_tokens") == 583, "prompt token count mismatch")
    require(execution.get("completion_tokens") == 139, "completion token count mismatch")
    require(artifacts.get("inputs_sha256") == sha256_file(INPUTS_PATH), "agent input digest mismatch")
    require(artifacts.get("traces_sha256") == sha256_file(TRACES_PATH), "trace digest mismatch")
    require(re.fullmatch(r"[0-9a-f]{40}", producer_state.get("source_commit", "")) is not None, "invalid agent producer source")
    require(re.fullmatch(r"sha256:[0-9a-f]{64}", producer_state.get("image_digest", "")) is not None, "invalid agent producer image")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for expected in ("62.5%", "87.5%", "3,006.96", "986.47"):
        require(expected in readme, f"README is missing benchmark value {expected}")
    require(
        "result_path: benchmarks/publication/agent-eval-baseline-v2.json" in manifest,
        "manifest V2 path mismatch",
    )

    if args.require_git:
        source_commit = v2["provenance"]["source_commit"]
        require(git_has_commit(source_commit), "source commit unavailable; fetch full history")
        require(git_has_commit(producer_state["source_commit"]), "agent producer source unavailable")
        producer = load_producer()
        require(
            v2["workload"]["fixture_digest"]
            == producer.digest_committed_path(ROOT, FIXTURE_PATH, source_commit),
            "committed fixture digest mismatch",
        )
        require(
            v2["workload"]["config_digest"]
            == producer.digest_committed_path(ROOT, CONFIG_PATH, source_commit),
            "committed config digest mismatch",
        )
        require(
            v2["provenance"]["dependency_lock_digest"]
            == producer.digest_committed_path(ROOT, LOCK_PATH, source_commit),
            "committed validation-lock digest mismatch",
        )

    serialized = json.dumps({"v1": v1, "v2": v2})
    for forbidden in ("C:\\Users\\", "github" + "_pat_", "gh" + "p_"):
        require(forbidden not in serialized, f"forbidden value in evidence: {forbidden}")
    print("publication_evidence=passed")


if __name__ == "__main__":
    main()
