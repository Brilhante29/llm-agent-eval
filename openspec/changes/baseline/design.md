# Change Design: honest trace evaluation

## Decision

Use a functional core with JSONL file adapters and a CLI shell. Task specs and traces are provider-neutral evidence. Validation runs before scoring or output.

## Boundaries

- Trace producers execute agents and record telemetry.
- The evaluator validates and scores supplied evidence.
- The CLI reads paths, reports errors, and writes the shared result.

## Principles

SRP separates production from evaluation. DIP points the evaluator at a stable trace contract. KISS keeps the baseline standard-library only. LSP requires future trace producers to preserve the same fields and units.

## Rejected

- A rule router presented as an agent.
- Provider execution inside the benchmark.
- Estimated latency or cost when observed fields are absent.
- Partial evaluation of missing or unknown task IDs.
