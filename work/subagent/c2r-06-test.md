# c2r-06: Test

## Role

Write and run Rust tests for one batch of the migration. Write phase — produces test files. **Must verify C test coverage.**

## Context

You receive:
- `OPENSPEC_CHANGE` — the OpenSpec change name
- `SOURCE_ROOT` — path to the C source tree
- `OUTPUT_DIR` — path to the Rust output project
- `BATCH_ID` — which batch to test
- Phase 1 output: source inventory with `test_functions` (C test function list)
- Phase 3 output: `specs/test-migration/spec.md` (C→Rust test mapping)
- Phase 4 output: `implement-plan.md` and `specs/` locations
- Phase 5 output: list of implemented modules/functions

## SuperPower Rules

Read `work/profiles/superpower/c-to-rust-migration-guards.yaml`, section `test`.

- **Allowed tools**: `run-verification`
- **Allowed filesystem**: read `**`, write `tests/**/*.rs`, write `src/**/*.rs`, create `tests/**/*.rs`
- **Forbidden**: modify tools.py, modify profiles, modify openspec/, modify work/skills/, modify work/subagent/

## Steps

1. Read `specs/test-migration/spec.md` for the **C→Rust test mapping table**
2. Read the relevant `specs/*/spec.md` for additional test requirements and scenarios
3. Read the C test source files to understand the original test logic
4. Write Rust test files under `OUTPUT_DIR/tests/`:
   - **For each C test function in the mapping table**: write a corresponding Rust test (or confirm it's covered by an existing test)
   - Each spec scenario maps to at least one test
   - Include boundary conditions, error cases, and state preservation tests
   - Tests must contain assertions
5. **Verify C test coverage**: After writing tests, go through the `test_functions` list from the source inventory and confirm every entry has:
   - A corresponding Rust test that covers the same behavior, OR
   - An explicit N/A reason documented in the test file
6. Run test verification:
   ```
   python tools.py run-verification --project-dir OUTPUT_DIR --commands '["cargo test --locked"]'
   ```
7. If tests fail, diagnose: is it a test bug or an implementation bug?
   - Test bug: fix the test
   - Implementation bug: note it for the repair phase

## Output

- Rust test files under `OUTPUT_DIR/tests/`
- Test result from tools.py
- **C test coverage report**: list of C test functions and their Rust coverage status

## Gate

Return one of:
- `PHASE_PASS` — tests written, `cargo test` passes, all C tests have Rust equivalents or explicit N/A
- `PHASE_BLOCKED` — critical test infrastructure failure
- `PHASE_DEGRADED` — some tests failing (implementation issues, noted for repair), or some C tests lack coverage
