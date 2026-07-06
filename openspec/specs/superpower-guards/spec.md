## ADDED Requirements

### Requirement: Spec phase delegation guard

The `spec` phase SHALL be configured as a delegated phase. Its guard definition MUST allow no `write` operations in the main context (specs are written by the subagent). The main agent's only filesystem access during the spec phase is reading dependency files.

#### Scenario: Spec phase guard definition
- **WHEN** the SuperPower guards file is inspected for the `spec` phase
- **THEN** `allowed_fs` SHALL include `read: **` but MUST NOT include `write` operations (subagent handles all writes)

#### Scenario: Spec phase main agent constraint
- **WHEN** the main agent is in the `spec` phase and attempts to write a file
- **THEN** the guard SHALL forbid the write; the main agent SHALL instead delegate to `c2r-03-spec.md`

### Requirement: Plan phase delegation guard

The `plan` phase SHALL be configured as a delegated phase. Its guard definition MUST allow no `write` operations in the main context (plan files are written by the subagent).

#### Scenario: Plan phase guard definition
- **WHEN** the SuperPower guards file is inspected for the `plan` phase
- **THEN** `allowed_fs` SHALL include `read: **` but MUST NOT include `write` operations (subagent handles all writes)

### Requirement: Implement phase maintains delegation guard

The `implement` phase SHALL remain delegated. Its guard definition MUST prohibit the main agent from writing Rust source files or Cargo.toml directly. These writes SHALL only occur inside Phase 5 batch subagents.

#### Scenario: Implement phase main agent constraint
- **WHEN** the main agent is in the `implement` phase and attempts to write `work/output/**/src/*.rs` or `work/output/**/Cargo.toml`
- **THEN** the guard SHALL forbid the write

### Requirement: Phase table includes delegation mode

The SKILL.md and INSTRUCTION.md SHALL clearly mark each phase as "Delegate" or "Keep inline" with the delegation decision rationale. Any phase that produces more than 3 output files MUST be marked "Delegate".

#### Scenario: Phase 3 marked Delegate
- **WHEN** inspecting the delegation table for Phase 3 (Spec)
- **THEN** it SHALL be marked "Delegate" with rationale: "Writes one spec file per capability — can produce 10+ files"

#### Scenario: Phase 4 marked Delegate
- **WHEN** inspecting the delegation table for Phase 4 (Plan)
- **THEN** it SHALL be marked "Delegate" with rationale: "Produces tasks.md and implement-plan.md — batch count varies per project"
