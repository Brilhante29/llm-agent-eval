# #9 llm-agent-eval

**Status:** scaffold

**Proves:** agentes avaliados por tarefa.

**Benchmark target:** task_success_rate, cost_per_task.

**Stack:** python, langgraph, pytest, mlflow, docker.

## Next milestone

Implement the smallest Docker-runnable version and produce the first JSON benchmark under enchmarks/results/.

## Run

`ash
docker build -t llm-agent-eval .
docker run --rm llm-agent-eval
`

## Benchmark

`ash
docker run --rm llm-agent-eval benchmark
`

| Metric | Value | Unit |
|---|---:|---|
| task_success_rate, cost_per_task | pending | pending |

## Architecture

Defined in sdd/spec.md before implementation.

## References

See REFERENCES.md.