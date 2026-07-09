# c2r-06: Test

## Role

Write INTEGRATION tests that span multiple capabilities and verify end-to-end behavior. This phase runs AFTER all implementation batches (Phase 5a) and unit test batches (Phase 5b) complete. You do NOT write unit tests — those were already written per-batch in Phase 5b. Your job is integration tests, cross-capability tests, and C test coverage verification.

## Context You Receive

- `OPENSPEC_CHANGE` — OpenSpec change name
- `SOURCE_ROOT` — absolute path to C source tree (contains original C tests)
- `OUTPUT_DIR` — absolute path to Rust output project
- `BATCH_ID` — which test batch from implement-plan you are executing (e.g., "6.1")
- `PRIOR_OUTPUTS.implement_plan` — absolute path to `implement-plan.md`
- `PRIOR_OUTPUTS.specs_dir` — absolute path to `specs/` directory
- `PRIOR_OUTPUTS.test_migration_spec` — absolute path to `specs/test-migration/spec.md`
- `PRIOR_OUTPUTS.inventory` — absolute path to `source-inventory.json` (for `test_functions` list)
- `PRIOR_OUTPUTS.capability_map` — (OPTIONAL) absolute path to `01c-capability-map.json`. If provided, unit tests were written per-capability in Phase 5b and this phase writes integration tests only. If NOT provided, this phase also covers unit test gaps.

## SuperPower Rules (this phase only)

- **Allowed tools**: `run-verification`
- **Allowed filesystem**: read `**`, write `tests/**/*.rs`, write `src/**/*.rs` (only for test-related fixes), create `tests/**/*.rs`
- **Forbidden**: modify tools.py, modify profiles, modify openspec/, modify work/skills/, modify work/subagent/

## Steps

### 1. Inventory Existing Tests

List all existing test files under `OUTPUT_DIR/tests/`. Run `cargo test --list` to see all existing test function names.

If capability map is available: These are the unit tests written per-batch in Phase 5b. **Do NOT duplicate any existing test.** Your job is to ADD integration tests, not re-implement unit coverage.

If capability map is NOT available: Identify which C test functions from the inventory are not yet covered. These gaps need unit tests in addition to any integration tests.

### 2. Read Test Migration Spec

Read `specs/test-migration/spec.md`. Find the C→Rust mapping table. For each C test function, check whether it is already covered by a Phase 5b unit test.

### 3. Identify Test Gaps

**If capability map is available**: Integration tests are needed when:
- A C test exercises multiple capabilities together (e.g., init → set → get → del → verify sector layout)
- A scenario spans capability boundaries (e.g., GC requires KV write + sector management + flash erase)
- An end-to-end workflow needs verification (e.g., full init → CRUD → deinit cycle)

**If capability map is NOT available**: Also identify unit test gaps — C test functions not yet covered by any Rust test. These need per-function unit tests.

### 4. Read C Test Source for Uncovered Tests

For each C test function NOT yet covered by Phase 5 unit tests, read the C test source to understand the scenario.

### 5. Write Tests

**If capability map is available**: Write integration tests that exercise cross-capability behavior. Do NOT write single-function unit tests — those already exist. Focus on multi-step workflows.

```rust
#[test]
fn test_full_kv_lifecycle() {
    // Setup: init KVDB (from batch N)
    // Write: set key-value (from batch M)
    // Read: get key-value and verify (from batch M)
    // GC: trigger garbage collection (from batch P)
    // Verify: sector layout is correct after GC (from batch Q)
}
```

**If capability map is NOT available**: Write Rust tests corresponding to each C test function in the inventory that is not yet covered. Follow the C→Rust mapping table from the test-migration spec. Also write integration tests for multi-step workflows.

### 6. Verify C Test Coverage

Produce a complete coverage report:

```
C Test Coverage Report
======================
C: test_flashdb_init    → Rust: test_init (unit, Phase 5b batch 1)     ✓ covered
C: test_flashdb_deinit  → Rust: test_deinit (unit, Phase 5b batch 1)   ✓ covered
C: test_gc_full         → Rust: test_gc_integration (integration)     ✓ covered
C: test_issue_249       → Rust: test_issue_249_regression (unit, P5)  ✓ covered
C: test_legacy_api      → Rust: —                                     ✓ N/A (deprecated)

Coverage: N/M C tests mapped (X%), K tests N/A
```

Every C test function from the inventory must appear with a status: covered (with Rust test name), or N/A (with reason).

### 7. Run All Tests

```
python WORK_DIR/runtime/tools.py run-verification \
  --project-dir "OUTPUT_DIR" \
  --commands '["cargo test --locked"]'
```

### 8. Diagnose Failures

If tests fail:
- **Test bug**: fix the test
- **Implementation bug**: note for Phase 7 repair, do NOT weaken the test
- Record implementation bugs per capability so Phase 7 can triage

## Output

1. Integration test files under `OUTPUT_DIR/tests/` (only if new integration tests were needed)
2. Test run result from tools.py (all tests: unit + integration)
3. Complete C test coverage report (in your return message)

## Gate

- `PHASE_PASS` — all tests pass, every C test function has coverage (unit or integration or N/A with reason)
- `PHASE_BLOCKED` — critical test infrastructure failure (can't compile tests at all)
- `PHASE_DEGRADED` — some tests fail (implementation bugs noted for repair), or C test coverage gaps remain
