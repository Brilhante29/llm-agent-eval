# Reuse Delta: llm-agent-eval

| Candidate | Decision | Reason |
|---|---|---|
| Provider-neutral task/trace schema | backlog for kit | Agent evaluators need one stable evidence boundary. |
| Fail-closed JSONL/cardinality validator | backlog for kit | The same gate applies to RAG, prompt, and agent datasets. |
| Fixture content | repo-local | Expected outcomes and traces are project evidence, not kit policy. |

No project-specific evaluator code should move into the kit until a second consumer proves the abstraction.
