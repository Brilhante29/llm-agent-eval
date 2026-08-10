# Benchmark Plan

Primary metric: `task_success_rate`. Secondary metrics: ordered tool-selection accuracy, observed mean/p95 latency, and token tariff cost.

Eight instructions cover calculator, retrieval, and formatting routes. A pinned local model plans once per task; the selected bounded tool produces the final output. Hidden task records define expected output and ordered tool calls.

The committed run measured `0.625` task success and `0.875` tool accuracy. One malformed decision and two tool execution failures remain visible. One process run is `repeat=1`; workload size is `measured_iterations=8`.

The V2 wrapper binds the offline evaluation to a clean commit, exact Docker image, complete fixtures, config, and validation lock. Agent trace provenance separately binds the producing model, source/image, tokens, latency, failures, and artifact hashes.
