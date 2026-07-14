# Spec: 9 - llm-agent-eval

## Claim

Agent evaluation harness that measures task success rate, tool routing correctness, and cost per task on local fixtures.

## Acceptance Criteria

- Runs locally with `python -m llm_agent_eval benchmark --output benchmarks/results/agent-eval-baseline.json`.
- Runs in Docker with no paid secret.
- Writes benchmark JSON under `benchmarks/results/`.
- Keeps domain/evaluation logic independent from CLI and future providers.
