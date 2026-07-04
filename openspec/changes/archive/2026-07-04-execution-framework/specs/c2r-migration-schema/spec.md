## ADDED Requirements

### Requirement: c2r-migration schema extends spec-driven

The project SHALL have a project-local OpenSpec schema named `c2r-migration` that extends the `spec-driven` schema. The schema SHALL define 6 artifacts in order: `proposal`, `specs`, `design`, `tasks`, `implement-plan`, `verification-report`.

#### Schema artifact dependency chain

- `proposal`: no dependencies
- `specs`: requires `proposal`
- `design`: requires `proposal`
- `tasks`: requires `specs` + `design`
- `implement-plan`: requires `tasks`
- `verification-report`: requires `implement-plan`

#### Scenario: Schema is discoverable
- **WHEN** `openspec schemas` is executed
- **THEN** the output SHALL include `c2r-migration` in the schema list

#### Scenario: Schema validation passes
- **WHEN** `openspec schema validate c2r-migration` is executed
- **THEN** validation SHALL pass without errors

### Requirement: implement-plan artifact defines batch execution strategy

The `implement-plan` artifact SHALL be generated as `implement-plan.md`. Its instruction SHALL guide the agent to:
- Read specs and tasks to identify implementation batches
- Map each batch to source files and functions
- Define batch boundaries (5-8 functions per batch per context management spec)
- Specify which subagent gets which batch
- Include expected build and test commands per batch

#### Scenario: implement-plan has correct template
- **WHEN** the implement-plan template is read
- **THEN** it SHALL contain sections for: Batch Overview, Batch Details (per batch: specs covered, functions, expected outputs, build commands), Execution Order

#### Scenario: implement-plan requires tasks
- **WHEN** `openspec instructions implement-plan --change <name> --json` is executed
- **THEN** the dependencies SHALL include `tasks`

### Requirement: verification-report artifact aggregates execution results

The `verification-report` artifact SHALL be generated as `verification-report.md`. Its instruction SHALL guide the agent to:
- Record cargo build results per batch
- Record cargo test results per batch
- Document repair cycles (errors found, fixes applied)
- Summarize semantic audit outcomes (invariants verified)
- Report quality gate results (unsafe ratio, fault injection, neutrality)
- Provide final pass/fail assessment

#### Scenario: verification-report has correct template
- **WHEN** the verification-report template is read
- **THEN** it SHALL contain sections for: Build Results, Test Results, Repair Log, Semantic Audit, Quality Gates, Final Assessment

#### Scenario: verification-report requires implement-plan
- **WHEN** `openspec instructions verification-report --change <name> --json` is executed
- **THEN** the dependencies SHALL include `implement-plan`

### Requirement: Schema templates exist for all artifacts

Each artifact in the schema SHALL have a corresponding template file under `openspec/schemas/c2r-migration/templates/`.

#### Scenario: All templates present
- **WHEN** the templates directory is listed
- **THEN** it SHALL contain: `proposal.md`, `spec.md`, `design.md`, `tasks.md`, `implement-plan.md`, `verification-report.md`

### Requirement: apply requires verification-report

The schema's `apply` section SHALL specify `requires: [verification-report]` and `tracks: tasks.md`. This ensures all execution artifacts are complete before implementation begins.

#### Scenario: apply gate includes verification-report
- **WHEN** the schema.yaml is read
- **THEN** `apply.requires` SHALL contain `verification-report`
