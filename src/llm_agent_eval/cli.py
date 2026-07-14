import argparse
import json
import re
import time
from pathlib import Path

KNOWLEDGE = {"retrieval quality": "recall_at_k", "answer overlap": "f1"}

def run_agent(prompt: str) -> tuple[str, str]:
    lower = prompt.lower()
    if "plus" in lower:
        nums = [int(x) for x in re.findall(r"\d+", lower)]
        return "calculator", str(sum(nums))
    if "times" in lower:
        nums = [int(x) for x in re.findall(r"\d+", lower)]
        value = 1
        for num in nums:
            value *= num
        return "calculator", str(value)
    if "percent" in lower:
        number = float(re.findall(r"0\.\d+|\d+", lower)[0])
        return "formatter", f"{round(number * 100)}%"
    for key, value in KNOWLEDGE.items():
        if key in lower:
            return "retriever", value
    return "fallback", "unknown"

def load_tasks() -> list[dict]:
    return [json.loads(line) for line in Path("data/fixtures/tasks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]

def evaluate() -> dict:
    tasks = load_tasks()
    started = time.perf_counter()
    rows = []
    for task in tasks:
        tool, answer = run_agent(task["prompt"])
        rows.append({"id": task["id"], "tool": tool, "answer": answer, "success": answer == task["expected"]})
    latency_ms = (time.perf_counter() - started) * 1000 / len(tasks)
    success = sum(row["success"] for row in rows) / len(rows)
    return {"project": "llm-agent-eval", "primary_metric": "task_success_rate", "task_success_rate": round(success, 4), "cost_per_task_usd": 0.0, "avg_latency_ms": round(latency_ms, 4), "tasks": rows}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["benchmark"], nargs="?", default="benchmark")
    parser.add_argument("--output", default="benchmarks/results/agent-eval-baseline.json")
    args = parser.parse_args()
    result = evaluate()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
