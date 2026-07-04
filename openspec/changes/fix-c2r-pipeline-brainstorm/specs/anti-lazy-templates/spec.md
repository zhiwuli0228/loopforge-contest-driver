## ADDED Requirements

### Requirement: Templates use mandatory structured fields, not HTML comments

All 5 templates under `openspec/schemas/c2r-migration/templates/` SHALL be redesigned to use mandatory structured fields. HTML comments (`<!-- ... -->`) used as sole section content SHALL be removed. Each section SHALL require either explicit content or an explicit "N/A — reason" statement.

#### Scenario: spec.md template enforces structured requirements

- **WHEN** the spec.md template is inspected
- **THEN** each requirement section SHALL contain:
  - `### Requirement: [ID] — [Name]`
  - A fill-in prompt: `[Describe the behavior this requirement mandates. Reference the C source file and line numbers that define this behavior.]`
  - `C source reference: [file:line]`
  - At least 3 scenario slots:
    - `#### Scenario: Normal path` with a fill-in prompt
    - `#### Scenario: Error path` with a fill-in prompt
    - `#### Scenario: Boundary condition` with a fill-in prompt
  - `### Invariants` section with `INV-[ID]-001: [State the invariant. If none, write "No invariants identified" and explain why.]`

#### Scenario: tasks.md template enforces capability-level grouping with spec references

- **WHEN** the tasks.md template is inspected
- **THEN** it SHALL organize tasks under `## Batch N: [Capability Name]` headings
- **AND** each batch heading SHALL include:
  - `关联 capability: [capability-id]`
  - `关联 spec: specs/<capability-id>/spec.md`
  - `C 源文件: [file list]`
  - `Rust 目标文件: [file list]`
- **AND** each batch SHALL contain both implementation and test checkboxes:
  - `- [ ] 实现 <函数名> — 对应 REQ-<capability>-<NNN>`
  - `- [ ] 单元测试 <test_name> — 覆盖场景 <scenario name>`
  - `- [ ] cargo test <test_filter> 通过`
- **AND** batch dependency SHALL be declared: `依赖 batch: [batch-ids or "无"]`

#### Scenario: design.md template enforces capability mapping section

- **WHEN** the design.md template is inspected
- **THEN** it SHALL include a mandatory **Capability Mapping** section between Goals and Decisions
- **AND** the Capability Mapping SHALL be a table:
  ```
  | Capability ID | C Source Files | Rust Target Module | Key Functions | Priority |
  |--------------|----------------|-------------------|---------------|----------|
  | [from capability map] | [files] | [module] | [list] | [P0/P1/P2] |
  ```
- **AND** each Decision SHALL include: description, rationale, and a mandatory **Alternatives considered** subsection with at least 1 rejected alternative

#### Scenario: implement-plan.md template enforces function-level batch detail

- **WHEN** the implement-plan.md template is inspected
- **THEN** each batch SHALL contain these mandatory fields:
  - **Capability**: capability ID and name
  - **Spec reference**: path to spec file
  - **C source files**: explicit file paths
  - **Rust target files**: explicit file paths
  - **Implementation functions**: numbered list with `fn signature — C equivalent in file:line`
  - **Data structures**: table mapping `C struct → Rust struct` with field-level details
  - **Unit tests**: numbered list with `#[test] fn name — covers scenario X`
  - **Build command**: explicit command string
  - **Test command**: explicit command string
  - **Completion criteria**: checklist `[ ] build passes [ ] tests pass [ ] unsafe=0`

#### Scenario: verification-report.md template enforces per-batch and per-capability records

- **WHEN** the verification-report.md template is inspected
- **THEN** it SHALL include a per-batch results table:
  ```
  | Batch | Capability | Build | Tests | Unsafe% | Status |
  |-------|-----------|-------|-------|---------|--------|
  | 1     | [id]      | PASS/FAIL | N passed / M total | X.X% | PASS/FAIL/DEGRADED |
  ```
- **AND** each batch SHALL have a repair log subsection if any failure occurred
- **AND** the repair log SHALL record: error, diagnosis, fix applied, retry result
- **AND** the final assessment SHALL cross-reference capability coverage: "N of M capabilities fully implemented and tested"

### Requirement: Templates exist for all pipeline artifacts

The schema SHALL have templates for every artifact in the pipeline, including the new brainstorm artifact.

#### Scenario: brainstorm artifact has a template

- **WHEN** the schema is inspected
- **THEN** a template SHALL exist at `openspec/schemas/c2r-migration/templates/capability-map.json`
- **AND** the template SHALL define the JSON structure for `01c-capability-map.json` as specified in the brainstorm-subagents spec
- **AND** the template SHALL include placeholder values that are clearly invalid (e.g., `"REQUIRED_FIELD_NOT_SET"`) so incomplete output is detectable

#### Scenario: All 5 existing templates are updated

- **WHEN** the templates directory is inspected
- **THEN** `proposal.md`, `design.md`, `spec.md`, `tasks.md`, `implement-plan.md`, and `verification-report.md` SHALL all follow the no-HTML-comments rule
- **AND** any unchanged template SHALL be treated as incomplete
