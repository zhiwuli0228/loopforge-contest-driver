## ADDED Requirements

### Requirement: Agent generates Rust code directly from C source

The Phase 5 subagent SHALL read C source files from SOURCE_ROOT and generate Rust code directly. No Python intermediate representation, body_kind classification, or hardcoded type mapping table SHALL be used.

#### Scenario: Direct C-to-Rust generation
- **WHEN** Phase 5 subagent receives a batch assignment
- **THEN** it SHALL read the relevant C source files directly from SOURCE_ROOT
- **THEN** it SHALL read the spec files for the batch's capability
- **THEN** it SHALL write Rust code to OUTPUT_DIR/src/<module>.rs
- **THEN** no Python code generation function SHALL be called

### Requirement: Every generated function must be fully implemented

The subagent SHALL NOT leave stub implementations. No `todo!()`, `unimplemented!()`, or empty function bodies SHALL be written.

#### Scenario: Complete implementation
- **WHEN** a function is generated
- **THEN** its body SHALL contain actual Rust logic implementing the C function's semantics
- **THEN** no `todo!()` or `unimplemented!()` SHALL appear in any generated .rs file

### Requirement: Generated code must compile

The subagent SHALL verify that every batch compiles successfully before reporting PHASE_PASS.

#### Scenario: Build verification
- **WHEN** the subagent writes Rust code for a batch
- **THEN** it SHALL run cargo build --locked in OUTPUT_DIR
- **THEN** it SHALL fix any compilation errors (up to 3 internal attempts)
- **THEN** it SHALL return PHASE_BLOCKED if unable to achieve a clean build after all attempts

### Requirement: unsafe code must be minimized and documented

unsafe SHALL only be used when strictly necessary (FFI boundaries, raw memory operations without safe equivalent). Every unsafe block SHALL have a comment explaining why it is needed and why it is sound.

#### Scenario: unsafe usage
- **WHEN** the subagent writes an unsafe block
- **THEN** a comment SHALL precede the block explaining: what safety invariant is being upheld and why safe Rust cannot express the operation

### Requirement: No Python body_kind dependency

The Rust code generation SHALL NOT depend on any body_kind field, translation_status field, or body_value field from source analysis. These fields SHALL NOT exist in the data provided to the subagent.

#### Scenario: Independent generation
- **WHEN** the subagent generates Rust code
- **THEN** all understanding of C function semantics SHALL come from reading the C source files directly, not from pre-computed classification metadata
