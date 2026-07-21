# Architecture Decision

Decision: functional core with a CLI/file adapter.

The problem is offline evaluation of evidence, not agent execution. JSONL task specifications and traces cross a strict validation boundary; pure scoring functions produce metrics; the CLI only handles paths, errors, and output.

This keeps the evaluator decoupled from LLM providers, agent frameworks, cloud SDKs, and billing APIs. A live agent or graph can replace another trace producer as long as it emits the same contract.

Rejected:

- Rule router disguised as an agent: it evaluates its own implementation and makes success tautological.
- Provider SDK in the core: it couples scoring to execution and credentials.
- Event broker or web API: neither improves the local benchmark claim.
