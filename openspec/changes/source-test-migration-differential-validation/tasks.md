## 1. Evidence Contracts and Fixtures

- [x] 1.1 Define schemas for test migration run metadata, test IR, `source-test-map.json`, `semantic-invariant-test-map.json`, `differential-test-vectors.json`, `differential-test-report.json`, `mutation-test-report.json`, and final validation reports
- [x] 1.2 Implement coherent evidence-chain loading for Change 1/2/3 outputs, including run ID, input digest, schema version, Rust工程摘要 and path existence validation
- [x] 1.3 Add negative fixtures for stale inputs, mixed run IDs, missing source tests, missing semantic invariants, missing implementation IDs, and inconsistent report status
- [x] 1.4 Add at least one non-FlashDB fixture that uses the same source-analysis, semantic-planning, generation, test-migration, and differential-validation schemas
- [x] 1.5 Fix canonical counting rules for `source_test_count`, `source_assertion_count`, `semantic_invariant_count`, `differential_scenario_count`, and executed Rust test count

## 2. Source Test Migration

- [x] 2.1 Implement source test and assertion inventory ingestion from verified source-analysis evidence without recalculating or shrinking upstream denominators
- [x] 2.2 Implement project-neutral test IR generation for fixtures, setup/teardown, API call steps, expected observations, source assertions, semantic invariants, and behavior-contract links
- [x] 2.3 Generate Rust test modules from test IR, preserving stable source test IDs, assertion IDs, behavior contract IDs, invariant IDs, and implementation IDs in test metadata
- [x] 2.4 Generate `source-test-map.json` with complete source test, source assertion, Rust test, differential vector, equivalent coverage, and blocking-diagnostic cross references
- [x] 2.5 Generate `semantic-invariant-test-map.json`, requiring every invariant to map to at least one executed assertion or differential comparison
- [x] 2.6 Add blocking diagnostics for unmigratable fixtures, nondeterministic source tests, unsupported platform dependencies, and assertions that cannot be expressed as Rust checks or differential observations

## 3. Assertion Effectiveness Gates

- [x] 3.1 Implement Rust test AST or token-based scanning for `assert!(true)`, `assert_eq!(x, x)`, `assert!(matches!(x, _))`, empty tests, ignored tests, and equivalent vacuous assertion patterns
- [x] 3.2 Detect weakened tests where a source assertion requiring concrete return, state, ordering, persistence, or error behavior is reduced to callability or command success
- [x] 3.3 Validate that every generated test has at least one effective assertion or differential observation linked to source evidence
- [x] 3.4 Add negative tests proving vacuous assertions, self-comparisons, all-match assertions, empty tests, and removed assertion effects all produce `BLOCKED_WITH_REPORT`
- [x] 3.5 Record assertion scan results in the final validation report with test names, source positions, patterns, and source assertion IDs

## 4. Differential Harness

- [x] 4.1 Implement `differential-test-vectors.json` generation from source tests, behavior contracts, state transitions, semantic invariants, fixtures, seeds, and failure plans
- [x] 4.2 Implement isolated C Oracle execution with deterministic working directories, input storage images, environment capture, command logs, and normalized observation output
- [x] 4.3 Implement isolated Rust rewrite execution using the generated Cargo project, same initial state, same inputs, same seeds, same failure plan, and normalized observation output
- [x] 4.4 Implement comparison for return values, errors, KV/TS visible data, traversal order, capacity and boundary behavior, reopen persistence, corruption or interruption recovery, GC effects, and declared side effects
- [x] 4.5 Generate `differential-test-report.json` with per-vector commands, environment summaries, observations, comparison rules, first divergence, linked contracts, and blocking status
- [x] 4.6 Add negative fixtures for C-only failure, Rust-only failure, missing normalized observations, mismatched return codes, ordering divergence, persistence divergence, and recovery divergence

## 5. State Machine and Mutation Testing

- [x] 5.1 Generate fixed-seed state machine operation sequences from behavior contracts and state transitions, including valid, boundary, failure, persistence, and recovery paths
- [x] 5.2 Execute state machine sequences on both C and Rust sides and compare normalized observations after every operation
- [x] 5.3 Implement a fixed mutation set covering wrong return code, missing delete effect, capacity off-by-one, traversal order error, lost reopen persistence, ignored corruption recovery, and missing GC visibility update
- [x] 5.4 Run migration tests, differential vectors, state machine tests, and invariant checks against each mutation and require at least one linked detection per fixed critical mutation
- [x] 5.5 Generate `mutation-test-report.json` with mutation identity, injection location, expected detection surface, actual failing test or vector, and survivor diagnostics
- [x] 5.6 Add negative tests proving any surviving critical mutation blocks the overall validation result

## 6. Anti-FlashDB Customization Gate

- [x] 6.1 Implement scanning for project names, domain terms, known source file names, symbol prefixes, fixed API name lists, sample paths, golden outputs, and project-specific profiles in migration and differential code paths
- [x] 6.2 Distinguish input evidence or log data from control-flow, configuration, comparator, generator, or template logic, and record machine-readable adjudication for allowed data references
- [x] 6.3 Validate the full migration and differential framework against the non-FlashDB fixture using the same schemas and code paths
- [x] 6.4 Add negative tests where project-specific comparator branches, symbol-prefix dispatch, hardcoded API lists, and golden-output shortcuts are detected and produce `BLOCKED_WITH_REPORT`
- [x] 6.5 Include anti-customization scan results and adjudications in the final validation report, with unresolved core hits blocking success

## 7. Cargo Test Execution and Evidence Publication

- [x] 7.1 Execute `cargo test --locked -- --nocapture` for the generated Rust project, recording toolchain, command, working directory, exit code, complete log, executed test count, and test names
- [x] 7.2 Reject zero executed tests, ignored-only suites, nonzero Cargo exit status, stale logs, missing log files, and logs not bound to the current run ID
- [x] 7.3 Atomically publish test maps, differential vectors, differential reports, mutation reports, cargo test logs, anti-customization reports, and final validation reports only after schema and cross-reference validation
- [x] 7.4 Ensure failure publication preserves complete diagnostics for Change 5 without deleting generated tests, weakening assertions, or overwriting prior successful evidence
- [x] 7.5 Wire the validation stage into the runner so it runs only after complete Rust project generation succeeds and before any compile or semantic repair loop begins
- [x] 7.6 Add end-to-end tests covering successful generic fixture validation, blocked FlashDB-specific customization, blocked vacuous tests, blocked differential mismatch, blocked survivor mutation, and coherent successful evidence publication
