import unittest
from llm_agent_eval.cli import evaluate, run_agent

class AgentEvalTests(unittest.TestCase):
    def test_agent_routes_tools(self):
        self.assertEqual(run_agent("Calculate 2 plus 3"), ("calculator", "5"))
        self.assertEqual(run_agent("Format success rate as percent for 0.5"), ("formatter", "50%"))

    def test_success_rate_is_measurable(self):
        result = evaluate()
        self.assertGreaterEqual(result["task_success_rate"], 1.0)
        self.assertEqual(result["cost_per_task_usd"], 0.0)

if __name__ == "__main__":
    unittest.main()
