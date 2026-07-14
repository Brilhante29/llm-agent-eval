# Benchmark Plan

Primary metric: `task_success_rate`.

Command:

```powershell
python -m llm_agent_eval benchmark --output benchmarks/results/agent-eval-baseline.json
```

The benchmark uses local fixtures so the result is reproducible and does not require external credentials.
