## ADDED Requirements

### Requirement: Analyze-only runtime command set
The system SHALL provide a consistency-check runtime command set under `work/runtime/tools.py` that exposes the authoritative analyze-only entry points `scan-design`, `scan-code`, `extract-implementation`, `build-traceability`, `run-verification`, and `write-report`. Each command MUST consume declared inputs, produce structured outputs suitable for downstream stages, and avoid modifying business source files under `SOURCE_ROOT`.

#### Scenario: Operator runs the minimum runtime pipeline
- **WHEN** an operator invokes the authoritative runtime commands in order for a consistency-check run
- **THEN** each command accepts the declared design, source, profile, or intermediate-artifact inputs and writes only the declared trace or result artifacts without editing business source files

### Requirement: Structured traceability and evidence outputs
The runtime SHALL emit structured artifacts for design inventory, source inventory, implementation extraction, traceability mapping, and verification status under declared trace paths. These artifacts MUST preserve stable identifiers, adapter provenance, evidence references, and enough status information for downstream drift analysis or final reporting without re-reading the entire source tree.

#### Scenario: Traceability artifacts are handed off
- **WHEN** `build-traceability` receives a canonical design model and implementation model
- **THEN** it writes a structured traceability artifact that records matched links, uncovered design objects, uncovered implementation objects, and evidence references consumable by later stages or report generation

### Requirement: Verification status preservation
The runtime SHALL record verification outcomes as explicit status data rather than raw shell output alone. Verification artifacts MUST distinguish successful execution, failed execution, timeout, skipped execution, and unavailable-command conditions, and MUST preserve the executed command set and supporting evidence for the final report.

#### Scenario: Verification command cannot be executed
- **WHEN** `run-verification` is asked to execute a declared verification command that is unavailable or fails before producing a meaningful result
- **THEN** the runtime records a non-success verification status with the command, failure reason, and preserved evidence so the final report can distinguish blocked verification from a verified pass

### Requirement: Final report output contract
The runtime SHALL be able to render the terminal consistency-check outputs `result/output.md`, `result/issues/00-summary.md`, and `logs/trace/final-report.md` from structured intermediate artifacts. The report outputs MUST summarize final status, scope, findings, traceability coverage, risk or repair summaries, verification results, and evidence references without inventing missing evidence.

#### Scenario: Report writer renders a degraded result
- **WHEN** intermediate artifacts contain confirmed drift findings, partial coverage gaps, or non-success verification results
- **THEN** `write-report` emits the final report files with a degraded or blocked status, references the available evidence, and preserves missing-data or unavailable-verification conditions as explicit report content
