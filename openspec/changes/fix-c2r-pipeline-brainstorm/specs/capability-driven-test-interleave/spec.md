## ADDED Requirements

### Requirement: Implementation and unit testing are interleaved per capability batch

The c2r-05-implement subagent SHALL include a mandatory unit test step within each batch execution. Tests SHALL be written and verified for the current batch before proceeding to the next batch.

#### Scenario: Each implement batch includes unit test step

- **WHEN** the `c2r-05-implement.md` subagent processes a batch
- **THEN** it SHALL complete implementation of all functions in the batch
- **AND** it SHALL then write unit tests covering those functions before reporting success
- **AND** it SHALL run `cargo test <batch_test_filter>` to verify tests pass
- **AND** the batch SHALL NOT be marked complete until tests pass

#### Scenario: Unit tests are written per capability, not per module

- **WHEN** a batch maps to capability `status-table-machine`
- **THEN** unit tests for that batch SHALL test status table set/get/write/read operations in isolation
- **AND** tests SHALL cover all 6 WRITE_GRAN variants as parameterized tests
- **AND** tests SHALL NOT depend on KVDB or TSDB initialization (which belong to other capabilities)

#### Scenario: Build verification gate includes test verification

- **WHEN** the implement subagent reports gate status
- **THEN** `PHASE_PASS` SHALL require BOTH `cargo build` success AND `cargo test <batch>` success
- **AND** `PHASE_DEGRADED` SHALL be reported if build passes but tests fail
- **AND** failing tests SHALL be documented in the return message for the repair phase

### Requirement: c2r-06-test is re-scoped to integration and cross-capability testing

The `c2r-06-test.md` subagent SHALL focus on integration tests that span multiple capabilities and verifying C test coverage completeness.

#### Scenario: 06-test focuses on cross-capability integration

- **WHEN** the 06-test subagent runs
- **THEN** it SHALL write tests that exercise interactions between capabilities (e.g., KV CRUD → GC → verify sector layout)
- **AND** it SHALL write end-to-end tests that mirror real-world usage patterns
- **AND** it SHALL NOT re-implement unit tests already written in 05-implement batches

#### Scenario: 06-test verifies complete C test coverage

- **WHEN** the 06-test subagent runs
- **THEN** it SHALL read `specs/test-migration/spec.md` for the C→Rust test mapping table
- **AND** it SHALL verify every C test function has a corresponding Rust test (unit or integration)
- **AND** it SHALL produce a coverage report listing: C test name → Rust test name → coverage status (covered/partial/missing)
- **AND** missing coverage SHALL result in `PHASE_DEGRADED` with specific missing items listed

#### Scenario: 06-test writes only tests not covered by 05

- **WHEN** the 06-test subagent identifies test gaps
- **THEN** it SHALL write integration tests for those gaps
- **AND** it SHALL NOT duplicate coverage already provided by 05-implement unit tests
- **AND** its prompt SHALL direct it to first inventory existing tests before writing new ones

### Requirement: implement-plan batches include test tasks alongside implementation tasks

The `implement-plan.md` artifact SHALL define each batch as containing both implementation and test tasks, not as separate implementation and test phases.

#### Scenario: Batch definition includes both implement and test tasks

- **WHEN** `implement-plan.md` defines a batch for capability `kv-crud`
- **THEN** the batch SHALL include implementation tasks (write Rust functions)
- **AND** the batch SHALL include test tasks (write unit tests for those functions)
- **AND** the batch SHALL include a verification step (cargo test)
- **AND** the test tasks SHALL reference the specific scenarios from the capability's spec

#### Scenario: implement-plan batch count accounts for interleaving

- **WHEN** the implement-plan defines N capabilities
- **THEN** there SHALL be N implementation batches (Phase 5)
- **AND** there SHALL be 1 integration test batch (Phase 6) covering cross-capability scenarios
- **AND** the Phase 6 batch SHALL depend on completion of all Phase 5 batches
