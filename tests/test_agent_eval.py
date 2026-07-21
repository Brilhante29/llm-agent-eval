import json
import tempfile
import unittest
from pathlib import Path

from llm_agent_eval.cli import TraceValidationError, evaluate


class AgentEvalTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def write_jsonl(self, name, records):
        path = Path(self.temp_dir.name, name)
        path.write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )
        return path

    def test_evaluates_observed_outcomes_tools_latency_and_cost(self):
        tasks = self.write_jsonl(
            "tasks.jsonl",
            [
                {"id": "a", "expected_output": "ok", "expected_tool_calls": ["search"]},
                {"id": "b", "expected_output": "done", "expected_tool_calls": ["write"]},
            ],
        )
        traces = self.write_jsonl(
            "traces.jsonl",
            [
                {"task_id": "a", "output": "OK", "tool_calls": [{"name": "search"}], "latency_ms": 10, "cost_usd": 0.01},
                {"task_id": "b", "output": "failed", "tool_calls": [{"name": "read"}], "latency_ms": 30, "cost_usd": 0.03},
            ],
        )

        result = evaluate(tasks, traces)

        self.assertEqual(result["value"], 0.5)
        self.assertEqual(result["summary"]["tool_selection_accuracy"], 0.5)
        self.assertEqual(result["summary"]["average_latency_ms"], 20.0)
        self.assertEqual(result["summary"]["total_cost_usd"], 0.04)
        self.assertEqual(result["samples"], [1.0, 0.0])

    def test_emits_shared_benchmark_contract(self):
        result = evaluate()
        required = {"project", "metric", "value", "unit", "timestamp", "command"}
        self.assertTrue(required.issubset(result))
        self.assertEqual(result["metric"], "task_success_rate")
        self.assertEqual(result["summary"]["task_count"], 4)
        self.assertEqual(result["value"], 0.75)
        self.assertEqual(result["summary"]["tool_selection_accuracy"], 0.75)

    def test_rejects_missing_trace_fields(self):
        tasks = self.write_jsonl(
            "tasks.jsonl",
            [{"id": "a", "expected_output": "ok", "expected_tool_calls": []}],
        )
        traces = self.write_jsonl(
            "traces.jsonl",
            [{"task_id": "a", "output": "ok", "tool_calls": [], "latency_ms": 1}],
        )
        with self.assertRaisesRegex(TraceValidationError, "cost_usd"):
            evaluate(tasks, traces)

    def test_rejects_duplicate_or_unmatched_traces(self):
        tasks = self.write_jsonl(
            "tasks.jsonl",
            [{"id": "a", "expected_output": "ok", "expected_tool_calls": []}],
        )
        duplicate = {"task_id": "a", "output": "ok", "tool_calls": [], "latency_ms": 1, "cost_usd": 0}
        traces = self.write_jsonl("traces.jsonl", [duplicate, duplicate])
        with self.assertRaisesRegex(TraceValidationError, "unique"):
            evaluate(tasks, traces)

        unknown = self.write_jsonl(
            "unknown.jsonl",
            [{"task_id": "b", "output": "ok", "tool_calls": [], "latency_ms": 1, "cost_usd": 0}],
        )
        with self.assertRaisesRegex(TraceValidationError, "mismatch"):
            evaluate(tasks, unknown)


if __name__ == "__main__":
    unittest.main()
