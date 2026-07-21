# Benchmark Proof: llm-agent-eval

- Metric: `task_success_rate`
- Value: `0.75`
- Tool-selection accuracy: `0.75`
- Observed average latency: `124.525 ms`
- Observed p95 latency: `231.7 ms`
- Supplied total cost: `US$ 0.00072`
- Samples: `4`
- Result: `benchmarks/results/agent-eval-baseline.json`

Command:

```powershell
python -m llm_agent_eval benchmark --tasks data/fixtures/tasks.jsonl --traces data/fixtures/traces.jsonl --output benchmarks/results/agent-eval-baseline.json
```

The telemetry is supplied evidence. The evaluator does not execute an agent or measure provider billing.
