## MODIFIED Requirements

### Requirement: Analyze-only runtime command set
The system SHALL provide a consistency-check runtime command set under `work/runtime/tools.py` that exposes the authoritative repair-aware entry points needed for acceptance-baseline extraction, source inventory, implementation extraction, traceability construction, repair execution support, verification, and report rendering. The command surface MUST continue to support `scan-design`, `scan-code`, `extract-implementation`, `build-traceability`, `run-verification`, and `write-report`, MAY add bounded repair-support commands where needed, and MUST consume declared inputs derived from `SUBMISSION_ROOT` while avoiding modification of immutable submission-package assets.

#### Scenario: Operator runs the minimum runtime pipeline
- **WHEN** an operator invokes the authoritative runtime commands in order for a consistency-check run against a standard submission package
- **THEN** each command accepts the declared package, design, code, profile, or intermediate-artifact inputs, restricts any mutation to declared mutable targets, and writes the declared trace or result artifacts without editing immutable assets under `SUBMISSION_ROOT`

### Requirement: Structured traceability and evidence outputs
The runtime SHALL emit structured artifacts for acceptance-baseline inventory, source inventory, implementation extraction, traceability mapping, repair scope, and verification status under declared trace paths. These artifacts MUST preserve stable identifiers, adapter provenance, evidence references, and enough status information for downstream gap analysis, repair execution, retry routing, or final reporting without re-reading the entire source tree.

#### Scenario: Traceability artifacts are handed off
- **WHEN** `build-traceability` receives a canonical design model and implementation model
- **THEN** it writes a structured traceability artifact that records matched links, uncovered design objects, uncovered implementation objects, and evidence references consumable by later stages or report generation

### Requirement: Verification status preservation
The runtime SHALL record verification outcomes as explicit status data rather than raw shell output alone. Verification artifacts MUST distinguish successful execution, failed execution, timeout, skipped execution, and unavailable-command conditions, MUST preserve the executed command set and supporting evidence for the final report, and MUST record whether a command originated from the standard package contract, authoritative package metadata, or non-authoritative fallback detection. For the default contest workflow, verification status MUST also preserve whether a command belonged to build or project-owned verification versus black-box verification and MUST preserve command ordering dependencies declared by the package contract.

#### Scenario: Verification command cannot be executed
- **WHEN** `run-verification` is asked to execute a declared verification command from `SUBMISSION_ROOT/README.md` or authoritative package metadata that is unavailable or fails before producing a meaningful result
- **THEN** the runtime records a non-success verification status with the command, command source, verification class, failure reason, and preserved evidence so the final report can distinguish blocked package verification from a verified pass

#### Scenario: Verification command requires ordered package execution
- **WHEN** the package contract declares that business-code installation must complete before black-box tests execute
- **THEN** the runtime records the declared ordering dependency, reports whether the prerequisite command succeeded, and marks downstream black-box results as blocked rather than independent failures when the prerequisite did not complete

### Requirement: Final report output contract
The runtime SHALL be able to render the terminal consistency-check outputs `result/output.md`, `result/issues/00-summary.md`, and `logs/trace/final-report.md` from structured intermediate artifacts. The report outputs MUST summarize final status, standard-package scope, findings, accepted repairs, remaining gaps, verification results, and evidence references without inventing missing evidence. The terminal status model MUST support delivery-oriented verdicts such as passed, partial, blocked, or invalid submission.

#### Scenario: Report writer renders a degraded result
- **WHEN** intermediate artifacts contain confirmed drift findings, partial coverage gaps, applied repair evidence, or non-success verification results for a standard submission package
- **THEN** `write-report` emits the final report files with a delivery verdict that reflects the available evidence, preserves missing-data or unavailable-verification conditions as explicit report content, and identifies the package paths that were treated as design, code, mutable support assets, and black-box evaluation scope
