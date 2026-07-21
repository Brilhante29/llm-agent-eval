# #9 llm-agent-eval: 0.75 task success from supplied traces

The old demo routed four prompts with local `if` statements and evaluated its own answers. The replacement does not run an agent. It validates execution traces produced elsewhere and compares them with expected outcomes and ordered tool calls.

The committed evidence reports `0.75` task success, `0.75` tool-selection accuracy, `124.525 ms` observed average latency, and `US$ 0.00072` supplied cost. One wrong answer and one wrong tool choice keep the fixture honest.

The reusable decision is the boundary: agent runtimes produce traces; evaluation remains deterministic, local-first, and provider-neutral.
