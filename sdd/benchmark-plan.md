# Benchmark Plan

Primary metric: `task_success_rate`.

Secondary evidence: ordered tool-selection accuracy, observed average and p95 latency, and observed total and average cost.

```powershell
python -m llm_agent_eval benchmark --tasks data/fixtures/tasks.jsonl --traces data/fixtures/traces.jsonl --output benchmarks/results/agent-eval-baseline.json
```

The benchmark evaluates four committed task/trace pairs. Outcome and tool metrics are binary per task. Latency and cost are copied from supplied telemetry and are not measured or estimated by the evaluator. Invalid evidence fails before a result is written.
