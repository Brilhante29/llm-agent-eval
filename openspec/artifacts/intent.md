# Intent: llm-agent-eval

## Measurable Claim

Agent evaluation harness that measures task success rate, tool routing correctness, and cost per task on local fixtures.

## Problem

Adds task-level agent evaluation to the platform after answer and retrieval metrics.

## In Scope

- Use the selected component pack: `ai-evaluation-retrieval`.
- Keep the project under the AI Evaluation and Retrieval Systems program.
- Preserve the benchmark contract: `task_success_rate` in `benchmarks/results/agent-eval-baseline.json`.
- Keep the default path local-first and reproducible.

## Out Of Scope

- Paid credentials for the default demo.
- External infrastructure that is not required by the benchmark.
- Replacing local portfolio skills with external components silently.

## Default Demo Path

- Status: benchmarked
- Runtime: python-cli
- Benchmark command: `python -m llm_agent_eval benchmark --output benchmarks/results/agent-eval-baseline.json`

## Public Proof

- Benchmark: Task success rate = 1.00
- Result path: `benchmarks/results/agent-eval-baseline.json`
