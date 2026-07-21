# Spec: 9 - llm-agent-eval

## Claim

Evaluate supplied execution traces against expected task outcomes and ordered tool calls, while aggregating observed latency and observed cost.

## Acceptance Criteria

- Reject malformed records, duplicate IDs, unknown tasks, and incomplete task/trace sets.
- Compare normalized outputs and ordered tool-call names independently.
- Report task success, tool-selection accuracy, average and p95 latency, and total and average cost.
- Emit the shared benchmark contract and run locally or in Docker without credentials.
- Never execute a rule router and present it as an agent.
