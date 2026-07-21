# llm-agent-eval Specification

## ADDED Requirements

### Requirement: supplied trace evaluation

The system SHALL evaluate supplied traces and SHALL NOT implement an agent or router as the subject under test.

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
