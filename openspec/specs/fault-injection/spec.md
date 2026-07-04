## ADDED Requirements

### Requirement: Run fault injection tests and return raw results
The system SHALL execute fault injection testing against a Rust project and return the raw test execution results without interpreting pass/fail.

#### Scenario: Normal fault injection run
- **WHEN** user runs `python tools.py fault-injection --project-dir /path --trace-dir /trace`
- **THEN** system outputs JSON with `ok: true`, `data.test_results` containing raw test output, `data.mutations` containing mutation test data

#### Scenario: Tests fail during injection
- **WHEN** some injected tests fail
- **THEN** system outputs `ok: true` with failure details in `data.test_results`; the system SHALL NOT determine overall pass/fail

### Requirement: Configurable injection parameters
The system SHALL support `--mutations` to specify which mutation types to apply.

#### Scenario: Specific mutation types
- **WHEN** user specifies `--mutations '["boundary", "null-injection"]'`
- **THEN** system applies only the specified mutation types

#### Scenario: Default mutations
- **WHEN** user omits `--mutations`
- **THEN** system applies all available mutation types

### Requirement: Trace directory for reproducibility
The system SHALL write detailed trace data to the specified `--trace-dir` for later analysis.

#### Scenario: Trace output
- **WHEN** fault injection completes
- **THEN** system writes per-mutation trace files to `--trace-dir` with input, expected output, and actual output for each test case
