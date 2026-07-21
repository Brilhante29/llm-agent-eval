# Intent: llm-agent-eval

Measure supplied agent evidence rather than a self-authored router.

- Primary metric: `task_success_rate`.
- Secondary metrics: tool-selection accuracy, observed latency, observed cost.
- Default path: local JSONL and Python CLI.
- Status: `benchmarked`.
- Excluded: live-agent execution, provider credentials, and estimated telemetry.
