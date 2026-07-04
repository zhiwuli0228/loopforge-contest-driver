# c2r-06: Test

## Role

Write Rust tests for ONE batch. Must verify complete C test coverage per the test migration spec. Write phase — produces test files under `OUTPUT_DIR/tests/`.

## Context You Receive

- `OPENSPEC_CHANGE` — OpenSpec change name
- `SOURCE_ROOT` — path to C source tree (contains original C tests)
- `OUTPUT_DIR` — path to Rust output project
- `BATCH_ID` — which test batch from implement-plan you are executing (e.g., "6.1")
- `PRIOR_OUTPUTS.implement_plan` — path to `implement-plan.md`
- `PRIOR_OUTPUTS.specs_dir` — path to `specs/` directory
- `PRIOR_OUTPUTS.test_migration_spec` — path to `specs/test-migration/spec.md`
- `PRIOR_OUTPUTS.inventory` — path to `source-inventory.json` (for `test_functions` list)

## SuperPower Rules (this phase only)

- **Allowed tools**: `run-verification`
- **Allowed filesystem**: read `**`, write `tests/**/*.rs`, write `src/**/*.rs` (only for test-related fixes), create `tests/**/*.rs`
- **Forbidden**: modify tools.py, modify profiles, modify openspec/, modify work/skills/, modify work/subagent/

## Steps

### 1. Read Your Batch Assignment

Read `implement-plan.md`. Find your test batch by `BATCH_ID`. Note:
- Which modules you are testing
- Which C test functions this batch covers
- The expected test command

### 2. Read Test Migration Spec

Read `specs/test-migration/spec.md`. Find the C→Rust mapping table rows for your batch. For each C test function in your batch, confirm:
- The target Rust test function name
- The target Rust test file
- Any special requirements or N/A designations

### 3. Read C Test Source

For each C test function in your batch, read the C test source file to understand:
- What behavior the test validates
- Input values and expected outputs
- Setup and teardown patterns
- Assertions

### 4. Write Rust Tests

For each C test function in your batch, write the corresponding Rust test:

```rust
#[test]
fn test_<name>() {
    // Setup — mirrors C test setup
    // Exercise — mirrors C test execution
    // Assert — mirrors C test assertions, using Rust assert! macros
}
```

**Test structure rules**:
- Each `#[test]` function tests one behavior
- Use `assert_eq!`, `assert!`, `assert_ne!` — every test must have at least one assertion
- If the C test uses a harness/setup, replicate it in Rust (helper functions, before-each pattern)
- If a C test is marked N/A in the mapping table, write a comment in the test file explaining why

### 5. Add Spec-Scenario Tests

Beyond the C test mapping, add tests for scenarios from the module specs:
- Boundary conditions (empty input, max size, edge values)
- Error paths (invalid input, out-of-memory simulation where possible)
- State preservation (operation fails → state unchanged)

### 6. Run Tests

```
python WORK_DIR/runtime/tools.py run-verification \
  --project-dir "OUTPUT_DIR" \
  --commands '["cargo test --locked"]'
```

### 7. Diagnose Failures

If tests fail:
- **Test bug** (wrong assertion, bad setup): fix the test
- **Implementation bug** (function returns wrong value): note it for Phase 7 (repair), do NOT weaken the test to make it pass
- Record implementation bugs clearly so Phase 7 can find them

### 8. Verify C Test Coverage

After all tests are written, produce a coverage report for your batch:

```
C Test Coverage Report — Batch BATCH_ID
========================================
C: test_flashdb_init    → Rust: test_init              ✓ written
C: test_flashdb_deinit  → Rust: test_deinit            ✓ written
C: test_legacy_api      → Rust: —                      ✓ N/A (deprecated API)
C: test_kv_basic        → Rust: test_kv_set_get        ✓ written
```

Every C test function from the inventory that falls in this batch must appear in this report with a status.

## Output

1. Rust test files under `OUTPUT_DIR/tests/` for your batch
2. Test run result from tools.py
3. C test coverage report for your batch (in your return message)

## Gate

- `PHASE_PASS` — all tests in batch written and pass, every C test function covered (mapped or N/A)
- `PHASE_BLOCKED` — critical test infrastructure failure (can't compile tests at all)
- `PHASE_DEGRADED` — some tests fail (implementation bugs noted for repair), or some C tests lack coverage
