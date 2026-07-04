## ADDED Requirements

### Requirement: C-to-Rust migration stage pipeline is defined

The system SHALL provide a SuperSpec YAML configuration at `work/profiles/superspec/c-to-rust-migration-stages.yaml` that defines 11 sequential stages (00-preflight through 10-finalize) for C-to-Rust migration. Each stage SHALL declare a subagent binding, input file paths, output artifact path, and gate criteria.

#### Scenario: Orchestrator reads stage definitions

- **WHEN** the V2 orchestrator (SKILL.md v2) loads `c-to-rust-migration-stages.yaml`
- **THEN** it SHALL find 11 stage definitions each with `id`, `subagent`, `input`, `output`, `success_gate`, `failure_gate`, and `blocked_gate` fields

#### Scenario: Stage enforces subagent isolation

- **WHEN** a stage with `parent_direct_execution_allowed: false` is reached
- **THEN** the orchestrator SHALL delegate to the declared subagent file and SHALL NOT execute the stage logic directly in the parent context

#### Scenario: Modify-code stages are explicitly marked

- **WHEN** a stage has `can_modify_code: false`
- **THEN** the subagent SHALL NOT write to Rust source or test files

#### Scenario: Blocked stage halts the pipeline

- **WHEN** a subagent returns a gate value matching the stage's `blocked_gate`
- **THEN** the orchestrator SHALL stop the pipeline and return `BLOCKED_WITH_REPORT`

### Requirement: Stage definitions reference only generic paths

The stages YAML SHALL use only generic path patterns. It SHALL NOT contain any project-specific names, API identifiers, hardcoded file paths, or domain-specific terms.

#### Scenario: Paths use generic variable patterns

- **WHEN** the stages YAML is inspected
- **THEN** all file paths SHALL use generic patterns such as `SOURCE_ROOT/**`, `work/`, `logs/trace/c-to-rust/`, `result/` and SHALL NOT contain any concrete project names or identifiers

#### Scenario: No hardcoded project identity

- **WHEN** the stages YAML is applied to a different C project
- **THEN** all stage definitions SHALL remain valid without modification
