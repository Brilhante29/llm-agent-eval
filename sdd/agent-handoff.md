# Agent Handoff

This file records verifiable state and decisions, not private reasoning.

- Real graph: `planner_model -> tool_executor -> trace_evaluator`.
- Planner: Ollama `qwen2.5-coder:0.5b`, digest `sha256:4ff64a7...3fb09`.
- Producer source/image: `4408cc0b12400cd3ca11002605f4997bb05211f0` / `sha256:438430143c275656fb73d54fb5c80d0a1f61839ff7b626c090861ba1e3dba43f`.
- Result: task success `0.625`, tool accuracy `0.875`, mean `986.4655 ms`, p95 `3006.9626 ms`, token tariff `US$0.00`.
- Observed failures: one invalid planner decision and two invalid tool arguments. Do not hide or relabel them.
- Continue by keeping HTTP planning, bounded tool execution, and offline evaluation separated by the trace contract.
