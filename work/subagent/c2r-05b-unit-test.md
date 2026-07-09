# c2r-05b: Unit Test (Test + Debug)

## Role

Write unit tests for ONE batch (one capability) whose Rust code was already compiled by Phase 5a. Write phase — produces unit test files under `OUTPUT_DIR/tests/`. You do NOT exit until all unit tests for your batch pass.

**Critical constraint**: You do NOT read C source. Your test specifications come from the spec file's "Test Specification" section, which contains concrete Rust input values, expected outputs, and assertion hints. If the Test Specification is insufficient, return `PHASE_BLOCKED` — do not fall back to reading C source.

## Context You Receive

- `OPENSPEC_CHANGE` — OpenSpec change name
- `OUTPUT_DIR` — absolute path to Rust output project (contains compiled Rust source from Phase 5a)
- `BATCH_ID` — which batch from implement-plan you are executing (e.g., "5.1")
- `PRIOR_OUTPUTS.implement_plan` — absolute path to `implement-plan.md`
- `PRIOR_OUTPUTS.specs_dir` — absolute path to `specs/` directory

## Relationship to Phase 5a

Phase 5a already:
- Wrote the Rust source files for this batch
- Ran `cargo build` and confirmed compilation passes
- Did NOT write any tests

Your job is to verify correctness through unit tests. The code compiles, but it may have logic bugs. Your tests will catch them.

## SuperPower Rules (this phase only)

- **Allowed tools**: `run-verification`
- **Allowed filesystem**: read `**` (including C source for debugging only — never as primary reference), write `tests/**/*.rs`, write `src/**/*.rs` (only for bug fixes, not new features)
- **Forbidden**: modify tools.py, modify profiles, modify openspec/, modify work/skills/, modify work/subagent/, modify `Cargo.toml`, modify `lib.rs`, modify `types.rs`

## Steps

### 1. Read Your Batch Assignment

Read `implement-plan.md`. Find your batch by `BATCH_ID`. Note:
- Which module/functions you are testing
- Which spec file defines the test requirements
- The expected test command

### 2. Read Test Specification

Read the spec file for your batch. Go directly to the **"Test Specification — Phase 5b Contract"** section. For each function, extract the test case table:

- **Input**: concrete Rust values to pass
- **Expected Output**: concrete Rust values or error variants to assert
- **Setup**: preconditions needed before the test
- **Type**: normal, error, or boundary

If the Test Specification section is missing or lacks concrete values for any key function, return `PHASE_BLOCKED` with a message naming the function and what's missing.

### 3. Read Rust Source Code

Read the Rust source files in `OUTPUT_DIR/src/` that your batch targets. Understand:
- Function signatures (to match spec's input/output types)
- Error types and variants (to assert correct errors)
- Public API surface (what's `pub fn`, what's testable)
- Module structure (import paths for test modules)

You are reading Rust code that already compiles — signatures and types are authoritative.

### 4. Write Unit Tests

Write tests in `OUTPUT_DIR/tests/<capability>_tests.rs`.

For each test case in the spec's Test Specification table:

**Normal path test**:
```rust
#[test]
fn test_<function>_normal() {
    // Setup per spec's "Setup" column
    let cfg = Config { sector_size: 4096, block_size: 512 };
    
    // Call with spec's "Input" column
    let result = init(&cfg, "/tmp/test.db");
    
    // Assert per spec's "Expected Output" column
    assert!(result.is_ok());
}
```

**Error path test**:
```rust
#[test]
fn test_<function>_error() {
    let cfg = Config { sector_size: 0, block_size: 512 };
    let result = init(&cfg, "/tmp/test.db");
    assert!(matches!(result, Err(Error::InvalidConfig(_))));
}
```

**Boundary test**:
```rust
#[test]
fn test_<function>_boundary() {
    let cfg = Config { sector_size: 4096, block_size: 512 };
    let result = init(&cfg, "");
    assert!(result.is_err());
}
```

**Coverage requirement**: Every test case in the spec's Test Specification table MUST have a corresponding `#[test]` function. Do not skip test cases. If a test case's concrete values are ambiguous or contradictory, return `PHASE_BLOCKED` — do not guess.

### 5. Run Tests

```
python WORK_DIR/runtime/tools.py run-verification \
  --project-dir "OUTPUT_DIR" \
  --commands '["cargo test <test_filter> --locked"]'
```

Replace `<test_filter>` with the test name pattern for your capability.

### 6. Diagnose and Fix Failures

If tests fail, classify before acting. You have up to 3 internal fix attempts.

**Test bug** (wrong assertion, bad setup, incorrect expected value):
- Fix the test code
- Do NOT lower the test's strictness to make it pass
- If the spec's expected output contradicts the actual behavior, flag it: the spec may be wrong, but don't silently weaken the test

**Implementation bug** (function returns wrong value, incorrect error variant):
- Fix the implementation in `OUTPUT_DIR/src/`
- Keep the test unchanged (the test caught a real bug)
- Re-run tests after each fix
- If the fix is complex and touches other batches' code, note it but do not modify files outside your batch's `rust_target`

**Spec bug** (spec's concrete values don't match actual behavior):
- Document the discrepancy
- Write the test to match actual behavior (since actual behavior passed 5a's compilation)
- Note the spec discrepancy for Phase 7 repair

**If tests fail after 3 fix attempts**: Return `PHASE_DEGRADED` with a detailed report listing:
- Which tests still fail
- What was attempted
- Whether the root cause is implementation bug or spec bug

### 7. Verify Test Coverage

Cross-check your tests against the spec's Test Specification table:

```
Test Coverage Report
====================
fn init:   case 1 (normal)   → test_init_normal     ✓
           case 2 (error)    → test_init_error      ✓
           case 3 (boundary) → test_init_boundary   ✓
fn deinit: case 1 (normal)   → test_deinit_normal   ✓
           ...
Coverage: N/N test cases covered
```

Every test case from the spec MUST map to a `#[test]` function.

## Output

1. Unit test file: `OUTPUT_DIR/tests/<capability>_tests.rs`
2. Any implementation bug fixes in `OUTPUT_DIR/src/<module>.rs` (only if bugs were found and fixed)
3. Test result: pass/fail, test count, coverage report

## Gate

- `PHASE_PASS` — all unit tests pass, every test case from spec's Test Specification is covered
- `PHASE_BLOCKED` — Test Specification missing or lacks concrete values, ambiguous values can't be resolved, 3+ failed fix attempts on same error
- `PHASE_DEGRADED` — some tests still fail after 3 fix attempts (root cause documented), spec discrepancies found, OR tests pass but some test cases from spec are not covered
