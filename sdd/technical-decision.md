# Technical Decision

- Runtime: Python CLI packaged through `pyproject.toml`.
- Dependencies: standard library only.
- Inputs: strict JSONL task specifications and execution traces.
- Metrics: normalized exact outcome, ordered tool-call equality, nearest-rank p95, and arithmetic cost aggregation.
- Output: shared portfolio benchmark JSON with timestamp, command, samples, summary, and environment.
- Docker: copies the dependency-free source and fixtures, runs as UID 10001, and executes the same benchmark command offline.

The small sample is a reproducibility fixture, not a statistically representative agent evaluation corpus.
