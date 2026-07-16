# #9 llm-agent-eval: Task success rate = 1.00

Agent evaluation harness that measures task success rate, tool routing correctness, and cost per task on local fixtures.

This repository belongs to the AI Evaluation and Retrieval Systems program. Its job is narrow: prove the measurable claim through the selected component pack before adding unrelated infrastructure or features.

The benchmark is the proof. Task success rate = 1.00. Average latency: 0.13 ms. The result is stored in `benchmarks/results/agent-eval-baseline.json` and can be reproduced from the Docker/local path.

The important architecture decision is clean-architecture. The metric and benchmark use cases must stay independent from CLI, fixtures, and future providers.

The default path stays local-first. The project uses python, exposes cli-first, uses messaging mode `none`, and stores data with `fixture-files`. The dependency rule is explicit: Domain metrics and application benchmark orchestration do not import interface code.

The rejected work matters as much as the implemented work. Anything that does not improve the benchmark stays out of the first version.

Post angle: start with the number, show the architecture boundary, then explain which future adapter can be added without changing the core use cases.
