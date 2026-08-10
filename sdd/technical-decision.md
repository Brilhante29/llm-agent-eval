# Technical Decision

- Runtime: dependency-free Python CLI in a non-root container.
- Graph: OpenAI-compatible planner, bounded deterministic tool executor, offline trace evaluator.
- Tools: arithmetic parser, fixed-corpus retriever, and decimal formatter; no shell and no dynamic `eval`.
- Boundary: planner transport emits JSONL traces; evaluation imports neither model transport nor tool runtime.
- Metrics: exact outcome, ordered tool-call equality, observed mean/p95 latency, and cost aggregation.
- Failure policy: malformed decisions and tool arguments remain failed task traces; no fallback manufactures success.
- Provider strategy: local Ollama first, replaceable by another compatible endpoint through environment configuration.

The eight-task workload proves reproducibility and failure visibility, not production-agent generality.
