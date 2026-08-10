import json
import tempfile
import unittest
from pathlib import Path
from urllib.request import Request

from llm_agent_eval.cli import TraceValidationError, evaluate
from llm_agent_eval.runner import (
    AgentRunError,
    OpenAICompatiblePlanner,
    execute_tool,
    parse_decision,
    run_agent,
)


class FakeResponse:
    def __init__(self, document):
        self.document = document

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.document).encode("utf-8")


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
        self.assertEqual(result["summary"]["task_count"], 8)
        self.assertEqual(result["value"], 1.0)
        self.assertEqual(result["repeat"], 1)
        self.assertEqual(result["measured_iterations"], 8)
        self.assertEqual(result["summary"]["tool_selection_accuracy"], 1.0)

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

    def test_executes_bounded_tools_without_eval(self):
        self.assertEqual(execute_tool("calculator", "19 + 23"), "42")
        self.assertEqual(execute_tool("formatter", "0.125"), "12.5%")
        self.assertEqual(
            execute_tool("retriever", "local AWS cloud emulator"), "kumo"
        )
        with self.assertRaisesRegex(AgentRunError, "unknown tool"):
            execute_tool("shell", "whoami")

    def test_runs_model_planner_and_writes_observed_trace(self):
        inputs = self.write_jsonl(
            "inputs.jsonl", [{"id": "a", "instruction": "Calculate 19 + 23"}]
        )
        traces = Path(self.temp_dir.name, "traces.jsonl")
        provenance = Path(self.temp_dir.name, "provenance.json")

        def opener(request: Request, _timeout: float):
            payload = json.loads(request.data.decode("utf-8"))
            self.assertEqual(payload["temperature"], 0)
            return FakeResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": '{"tool":"calculator","argument":"19 + 23"}'
                            }
                        }
                    ],
                    "usage": {"prompt_tokens": 20, "completion_tokens": 8},
                }
            )

        planner = OpenAICompatiblePlanner(
            base_url="http://agent.test/v1",
            model="test-model",
            model_digest="sha256:" + "a" * 64,
            timeout_seconds=1,
            opener=opener,
        )
        result = run_agent(
            planner=planner,
            inputs_path=inputs,
            traces_path=traces,
            provenance_path=provenance,
            producer_source_commit="b" * 40,
            producer_image_digest="sha256:" + "c" * 64,
        )

        trace = json.loads(traces.read_text(encoding="utf-8"))
        self.assertEqual(trace["output"], "42")
        self.assertEqual(trace["tool_calls"], [{"name": "calculator"}])
        self.assertEqual(result["execution"]["measured_tasks"], 1)
        self.assertEqual(result["execution"]["decision_failures"], 0)
        self.assertEqual(result["graph"], ["planner_model", "tool_executor", "trace_evaluator"])

    def test_parses_json_inside_model_fence_and_rejects_extra_keys(self):
        self.assertEqual(
            parse_decision('```json\n{"tool":"retriever","argument":"metric"}\n```'),
            ("retriever", "metric"),
        )
        with self.assertRaisesRegex(AgentRunError, "tool and argument"):
            parse_decision('{"tool":"retriever","argument":"metric","extra":true}')


if __name__ == "__main__":
    unittest.main()
