## ADDED Requirements

### Requirement: Subagents confine compilation fixes to their own batch files

When `cargo build` or `cargo test` fails during Phase 5 implementation, the subagent SHALL only fix errors in files that belong to its own batch as declared in the batch's `rust_target` field. Errors in files owned by other batches SHALL NOT be fixed.

#### Scenario: Build error in own file — fix it
- **WHEN** `cargo build` fails with an error in a file that is in the subagent's `rust_target` list
- **THEN** the subagent SHALL fix the error in that file (within the standard 3-attempt limit)

#### Scenario: Build error in another batch's file — report, do not fix
- **WHEN** `cargo build` fails with an error in a file that is NOT in the subagent's `rust_target` list
- **THEN** the subagent SHALL NOT modify the file containing the error
- **THEN** the subagent SHALL report the error as part of a `PHASE_DEGRADED` gate token
- **THEN** the report SHALL include the exact file path, line number, and error message from rustc

#### Scenario: Mixed errors — fix own, report others
- **WHEN** `cargo build` fails with errors in both the subagent's own files and other batches' files
- **THEN** the subagent SHALL fix only the errors in its own files
- **THEN** the subagent SHALL return `PHASE_DEGRADED` listing the external errors that prevented a clean build

### Requirement: Subagent prompt explicitly prohibits cross-batch modification

`c2r-05-implement.md` SHALL contain an explicit instruction prohibiting modification of files outside the batch's `rust_target` scope. The instruction SHALL use imperative language ("do NOT modify" or "MUST NOT modify") rather than advisory language ("avoid" or "prefer not to").

#### Scenario: Prompt wording is imperative
- **WHEN** the `c2r-05-implement.md` prompt is inspected
- **THEN** it contains text stating that the subagent MUST NOT modify files owned by other batches
- **THEN** the prohibition applies to ALL write operations: creating, editing, or deleting files

#### Scenario: Prompt includes read permission clarification
- **WHEN** the `c2r-05-implement.md` prompt is inspected
- **THEN** it clarifies that reading any file in `OUTPUT_DIR/` is allowed and encouraged
- **THEN** the write restriction applies only to files outside the batch's own `rust_target` list

### Requirement: Subagent reports external errors as structured metadata

When a subagent returns `PHASE_DEGRADED` due to external compilation errors, the gate summary SHALL include the count of external errors and the affected file paths, enabling the orchestrator or follow-up phases to triage.

#### Scenario: Degraded gate includes error context
- **WHEN** a subagent returns `PHASE_DEGRADED` due to cross-batch compilation errors
- **THEN** the gate summary SHALL include `N external errors in: <file_paths>`
- **THEN** the format allows the orchestrator to identify which batches caused the interference
