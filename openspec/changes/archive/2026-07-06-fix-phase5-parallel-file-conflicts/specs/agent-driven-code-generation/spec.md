## MODIFIED Requirements

### Requirement: Agent generates Rust code directly from C source

The Phase 5 subagent SHALL read C source files from SOURCE_ROOT and generate Rust code directly. No Python intermediate representation, body_kind classification, or hardcoded type mapping table SHALL be used. The subagent SHALL write Rust code only to the module files declared in its batch's `rust_target` field in `implement-plan.md`.

#### Scenario: Direct C-to-Rust generation
- **WHEN** Phase 5 subagent receives a batch assignment
- **THEN** it SHALL read the relevant C source files directly from SOURCE_ROOT
- **THEN** it SHALL read the spec files for the batch's capability
- **THEN** it SHALL read existing module files in OUTPUT_DIR/src/ for type and trait reference
- **THEN** it SHALL write Rust code only to the files listed in its batch's `rust_target` field
- **THEN** no Python code generation function SHALL be called

#### Scenario: Batch writes to own module only
- **WHEN** Phase 5 subagent implements its batch
- **THEN** it extracts the `rust_target` file list from its batch entry in `implement-plan.md`
- **THEN** it SHALL NOT create, modify, or delete any source file outside that list
- **THEN** it SHALL NOT modify `lib.rs`, `Cargo.toml`, or `types.rs` unless its batch entry explicitly lists them as `rust_target`

### Requirement: Generated code must compile

The subagent SHALL verify that every batch compiles successfully before reporting PHASE_PASS. Compilation errors in files outside the batch's own `rust_target` scope SHALL be reported as PHASE_DEGRADED rather than fixed.

#### Scenario: Build verification
- **WHEN** the subagent writes Rust code for a batch
- **THEN** it SHALL run cargo build in OUTPUT_DIR
- **THEN** it SHALL fix compilation errors in its own files (up to 3 internal attempts)
- **THEN** it SHALL NOT fix errors in files outside its `rust_target` scope
- **THEN** it SHALL return PHASE_BLOCKED if unable to achieve a clean build after all attempts on its own files

#### Scenario: Build fails due to external files
- **WHEN** cargo build fails with errors in files NOT in the subagent's `rust_target` list
- **THEN** the subagent SHALL NOT modify those files
- **THEN** the subagent SHALL return PHASE_DEGRADED with the external error details (file paths, line numbers, error messages)
