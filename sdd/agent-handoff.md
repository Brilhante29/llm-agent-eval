# Agent Handoff

Project: `9 - llm-agent-eval`

## Current State

- The former rule router was removed.
- The repository now evaluates supplied execution traces only.
- Baseline: task success `0.75`, tool-selection accuracy `0.75`, average latency `124.525 ms`, total supplied cost `US$ 0.00072`.
- Status is `published`; V2 points to source SHA `4f4064c`, whose CI run `30859174373` passed.

## Contracts

- Tasks: `data/fixtures/tasks.jsonl`
- Traces: `data/fixtures/traces.jsonl`
- Shared raw result: `benchmarks/results/agent-eval-baseline.json`
- Publication config: `benchmarks/config/agent-eval-baseline-v2.json`
- V2 evidence: `benchmarks/publication/agent-eval-baseline-v2.json`

## Continue Safely

1. Run `$env:PYTHONPATH='src'; python -m unittest discover -s tests -v`.
2. Run the benchmark command from `project.yaml`.
3. Run `./tools/validate-project.ps1 -SkipDocker`, then the Docker validation.
4. Inspect `git diff --check` and confirm README numbers match the JSON.
5. Require the publication commit to pass GitHub Actions on its exact final SHA.

No code task is intentionally left half-finished. The next meaningful extension is a separate adapter that exports real provider traces in the same format.
