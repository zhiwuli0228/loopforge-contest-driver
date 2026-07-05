## ADDED Requirements

### Requirement: Agent diagnoses and fixes build/test failures

The Phase 7 subagent SHALL read all build and test error output from Phases 5-6, diagnose root causes, and apply fixes by editing the Rust source or test files directly.

#### Scenario: Repair loop
- **WHEN** Phase 7 subagent receives error logs from prior phases
- **THEN** it SHALL analyze each build error and test failure
- **THEN** it SHALL edit the Rust source or test files to fix the issues
- **THEN** it SHALL re-run cargo build --locked and cargo test --locked after each round of fixes
- **THEN** it SHALL repeat for up to 5 rounds (max_repair_rounds from config)

### Requirement: Tests must not be weakened

The repair subagent SHALL NOT weaken assertions, delete tests, or replace test logic with trivial assertions to make tests pass.

#### Scenario: Test integrity during repair
- **WHEN** a test failure is diagnosed
- **THEN** if the implementation is wrong, the subagent SHALL fix the implementation
- **THEN** if the test has a bug (wrong expected value, incorrect setup), the subagent SHALL fix the test while preserving its coverage intent
- **THEN** the subagent SHALL NOT replace assert_eq!(actual, expected) with assert!(true) or equivalent weakening

### Requirement: Repair log

The subagent SHALL produce a repair log recording each round, what was fixed, and the outcome.

#### Scenario: Repair traceability
- **WHEN** repair is complete or max rounds reached
- **THEN** the output SHALL include a repair-rounds.json file listing each round number, the errors found, the files edited, and whether the round succeeded

### Requirement: No Python repair functions

The repair process SHALL NOT call any Python repair function. The repair SHALL be performed entirely by the Agent analyzing errors and editing files.

#### Scenario: Agent-driven repair
- **WHEN** repair is needed
- **THEN** the Agent SHALL read error outputs, determine fixes, and apply edits
- **THEN** no run_repair_loop() or equivalent Python function SHALL be invoked
