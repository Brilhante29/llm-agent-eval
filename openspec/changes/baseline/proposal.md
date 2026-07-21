# Change Proposal: honest trace evaluation

Project: `llm-agent-eval` (#9)

## Why

The previous implementation generated answers with local routing rules and then evaluated those same rules. That measured a fixture router, not supplied agent behavior.

## Scope

- Validate task specifications and execution traces strictly.
- Score expected outcomes and ordered tool calls independently.
- Aggregate observed latency and cost from traces.
- Emit the shared benchmark result contract.
- Keep agent execution and provider SDKs out of the evaluator.

## Acceptance Signal

Changing a supplied trace changes the corresponding metric, malformed traces fail, and the committed result is reproducible without credentials.
