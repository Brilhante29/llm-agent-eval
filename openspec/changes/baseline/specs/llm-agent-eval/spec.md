# llm-agent-eval Specification

## ADDED Requirements

### Requirement: real agent execution and trace evaluation

The system SHALL run a planner through a replaceable OpenAI-compatible port, execute only bounded tools, emit observed traces, and evaluate those traces independently.

#### Scenario: local tool-routing graph

- GIVEN a pinned local model and one task instruction
- WHEN the graph runs
- THEN the planner emits a strict tool decision
- AND the selected bounded tool executes without shell access
- AND model, source, image, tokens, latency, failures, and artifacts are recorded.

#### Scenario: complete trace set

- GIVEN one expected outcome and ordered tool-call list per task
- AND exactly one valid trace per task
- WHEN evaluation runs
- THEN task success and tool-selection accuracy are reported independently
- AND latency and cost are aggregated from observed trace fields.

### Requirement: fail-closed trace validation

The system SHALL reject malformed records, duplicate IDs, missing traces, and unknown traces without writing a benchmark result.

#### Scenario: incomplete trace set

- GIVEN a task without one matching trace
- WHEN evaluation runs
- THEN the command exits with a validation error
- AND no partial metric is accepted.

### Requirement: shared benchmark evidence

A successful run SHALL emit the required shared benchmark fields plus samples, summary, environment, and per-task details.

#### Scenario: valid evidence output

- GIVEN a complete valid task and trace set
- WHEN evaluation succeeds
- THEN the result includes `project`, `metric`, `value`, `unit`, `timestamp`, and `command`.
