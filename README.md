# #9 llm-agent-eval

**Claim:** Agent evaluation harness that measures task success rate, tool routing correctness, and cost per task on local fixtures.

**Benchmark:** `task_success_rate` = `1.0` on local deterministic fixtures. Result file: `benchmarks/results/agent-eval-baseline.json`.

## What It Proves

This repository is part of **AI Evaluation and Retrieval Systems**. It provides one measurable layer of the AI Evaluation & RAG Platform while keeping the default path local-first, Dockerized, and free of paid credentials.

## Architecture

```mermaid
flowchart LR
  Fixtures["Local fixtures"] --> Core["Evaluation core"]
  Core --> CLI["CLI benchmark"]
  CLI --> Result["Benchmark JSON"]
  Core --> Future["Future provider adapters"]
```

Dependency rule: evaluation core does not import provider SDKs, cloud SDKs, web frameworks, or GitHub automation.

## Run Locally

```powershell
$env:PYTHONPATH = "src"
python -m llm_agent_eval benchmark --output benchmarks/results/agent-eval-baseline.json
```

## Run With Docker

```powershell
docker build -t llm-agent-eval .
docker run --rm llm-agent-eval
```

## Benchmark Result

See `benchmarks/results/agent-eval-baseline.json`.

## Reuse Contract

- Uses `portfolio-reuse-kit` for agent graph, SDD, validation, design system, and publication gate.
- Records reusable improvement decisions in `sdd/reuse-improvement-review.md`.
- Runs without paid secrets by default.
