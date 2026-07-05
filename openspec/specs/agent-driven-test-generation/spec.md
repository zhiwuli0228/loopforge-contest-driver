## ADDED Requirements

### Requirement: Agent generates Rust tests from C test inventory and specs

The Phase 6 subagent SHALL read the C test inventory (from Phase 1 source-inventory.json), the test-migration spec (from Phase 3), and the C test source files, and SHALL generate Rust test files directly.

#### Scenario: Test generation from C test evidence
- **WHEN** Phase 6 subagent receives a batch assignment
- **THEN** it SHALL read the C test inventory listing all C test functions
- **THEN** it SHALL read the test-migration spec mapping C tests to Rust tests
- **THEN** it SHALL read relevant C test source files from SOURCE_ROOT for understanding test intent
- **THEN** it SHALL write Rust test code to OUTPUT_DIR/tests/

### Requirement: Every C test must be covered

Each C test function identified in the Phase 1 inventory SHALL have a corresponding Rust test or an explicit N/A justification.

#### Scenario: Full C test coverage
- **WHEN** Phase 6 subagent completes test generation
- **THEN** its output SHALL include a coverage map showing each C test function name and its corresponding Rust test function name (or "N/A" with reason)
- **THEN** no C test function SHALL be silently omitted

### Requirement: Test quality

Every Rust test SHALL contain at least one assertion. Tests SHALL cover normal paths, error paths, and boundary conditions as specified in the capability's spec.

#### Scenario: Test assertion requirements
- **WHEN** the subagent writes a test function
- **THEN** the test SHALL contain at least one assert!/assert_eq!/assert_ne! macro
- **THEN** the test SHALL verify observable behavior, not implementation details

### Requirement: Test compilation and execution

The subagent SHALL verify that all tests compile and pass before reporting PHASE_PASS.

#### Scenario: Test verification
- **WHEN** the subagent writes Rust tests
- **THEN** it SHALL run cargo test --locked in OUTPUT_DIR
- **THEN** it SHALL fix any test failures (up to 3 internal attempts)
- **THEN** it SHALL NOT weaken or delete tests to make them pass
- **THEN** it SHALL return PHASE_DEGRADED if tests fail and document each failure for Phase 7 repair

### Requirement: No Python test rendering dependency

The test generation SHALL NOT depend on any _render_tests(), _render_semantic_test(), or _render_fallback_call_test() function. These functions SHALL NOT exist in the codebase.

#### Scenario: Independent test generation
- **WHEN** the subagent generates tests
- **THEN** all test logic SHALL be written by the subagent based on C test source reading and spec scenarios
