# Architecture Record: llm-agent-eval

- Style: functional core, imperative CLI shell.
- Input adapters: JSONL task specifications and traces.
- Core policies: strict validation, normalized outcome equality, ordered tool-call equality, nearest-rank p95, cost aggregation.
- Output adapter: shared benchmark JSON.
- Dependency rule: no agent framework, provider SDK, cloud SDK, or billing estimator enters the evaluator.

The producer/evaluator split is the reusable boundary. A live agent graph can replace the fixture producer without changing scoring.
