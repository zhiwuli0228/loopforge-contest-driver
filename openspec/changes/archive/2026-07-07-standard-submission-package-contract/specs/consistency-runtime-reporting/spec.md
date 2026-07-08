## MODIFIED Requirements

### Requirement: Analyze-only runtime command set
The system SHALL provide a consistency-check runtime command set under `work/runtime/tools.py` that exposes the authoritative analyze-only entry points `scan-design`, `scan-code`, `extract-implementation`, `build-traceability`, `run-verification`, and `write-report`. Each command MUST consume declared inputs derived from `SUBMISSION_ROOT`, produce structured outputs suitable for downstream stages, and avoid modifying immutable submission-package assets.

#### Scenario: Operator runs the minimum runtime pipeline
- **WHEN** an operator invokes the authoritative runtime commands in order for a consistency-check run against a standard submission package
- **THEN** each command accepts the declared package, design, code, profile, or intermediate-artifact inputs and writes only the declared trace or result artifacts without editing immutable assets under `SUBMISSION_ROOT`

### Requirement: Verification status preservation
The runtime SHALL record verification outcomes as explicit status data rather than raw shell output alone. Verification artifacts MUST distinguish successful execution, failed execution, timeout, skipped execution, and unavailable-command conditions, MUST preserve the executed command set and supporting evidence for the final report, and MUST record whether a command originated from the standard package contract, authoritative package metadata, or non-authoritative fallback detection.

#### Scenario: Verification command cannot be executed
- **WHEN** `run-verification` is asked to execute a declared verification command from `SUBMISSION_ROOT/README.md` or authoritative package metadata that is unavailable or fails before producing a meaningful result
- **THEN** the runtime records a non-success verification status with the command, command source, failure reason, and preserved evidence so the final report can distinguish blocked package verification from a verified pass

### Requirement: Final report output contract
The runtime SHALL be able to render the terminal consistency-check outputs `result/output.md`, `result/issues/00-summary.md`, and `logs/trace/final-report.md` from structured intermediate artifacts. The report outputs MUST summarize final status, standard-package scope, findings, traceability coverage, risk or repair summaries, verification results, and evidence references without inventing missing evidence.

#### Scenario: Report writer renders a degraded result
- **WHEN** intermediate artifacts contain confirmed drift findings, partial coverage gaps, or non-success verification results for a standard submission package
- **THEN** `write-report` emits the final report files with a degraded or blocked status, references the available evidence, preserves missing-data or unavailable-verification conditions as explicit report content, and identifies the package paths that were treated as design, code, and black-box evaluation scope
