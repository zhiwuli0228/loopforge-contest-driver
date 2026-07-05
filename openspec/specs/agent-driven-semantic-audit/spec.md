## ADDED Requirements

### Requirement: Agent derives semantic invariants from C source

The Phase 8 subagent SHALL read C source files and C test files, derive behavioral invariants, and write Rust invariant tests. No hardcoded invariant extraction logic SHALL be used.

#### Scenario: Invariant derivation
- **WHEN** Phase 8 subagent executes
- **THEN** it SHALL read C source files to understand behavior (reset, capacity, lookup, insert, delete, error recovery)
- **THEN** it SHALL read C test files to extract implicit invariants from test assertions
- **THEN** it SHALL derive invariants covering: normal behavior, boundary conditions, error paths, state preservation after failed operations, reset-after-mutation
- **THEN** it SHALL generate Rust invariant tests in OUTPUT_DIR/tests/

### Requirement: Invariant test failures are recorded, not silenced

If an invariant test fails, the subagent SHALL record the failure with details (which invariant, expected vs actual). It SHALL NOT delete or weaken the test.

#### Scenario: Invariant failure handling
- **WHEN** an invariant test fails
- **THEN** the subagent SHALL record the failing invariant, the test name, and the observed behavior in the audit report
- **THEN** the subagent SHALL NOT delete the failing test
- **THEN** the subagent SHALL NOT modify the test's assertion to make it pass

### Requirement: Semantic audit report

The subagent SHALL produce a semantic audit report documenting each invariant tested, the result, and any failures.

#### Scenario: Audit report output
- **WHEN** Phase 8 completes
- **THEN** the output SHALL include a semantic-audit-report.md file listing each invariant, its test, and pass/fail status
- **THEN** failures SHALL include the expected behavior and observed behavior

### Requirement: No Python invariant extraction

The semantic audit SHALL NOT depend on c2rust_invariant_tests.py or any render_invariant_tests() function. These SHALL NOT exist in the codebase.

#### Scenario: Independent semantic audit
- **WHEN** the subagent performs semantic audit
- **THEN** all invariant derivation SHALL come from the Agent reading C source and C tests
- **THEN** no Python-based _select_semantic_roles() or equivalent pre-computation SHALL be used
