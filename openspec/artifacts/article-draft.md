# #9 llm-agent-eval: 62.5% task success, 87.5% tool accuracy

A pinned local LLM routed eight tasks through calculator, retrieval, and formatting tools. It chose the expected tool seven times but completed only five outcomes. One decision was malformed and two calculator arguments failed strict parsing.

The failures are the point: a real agent evaluation must separate planning accuracy from end-to-end success. Provider execution emits trace provenance; bounded tools never expose shell or `eval`; the offline evaluator remains replaceable and deterministic.
