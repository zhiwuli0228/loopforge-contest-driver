# c2r-05: Implement

## Role

Write Rust source code AND unit tests for ONE batch (one capability) of the migration. Write phase — produces Rust source files under `OUTPUT_DIR/src/` and unit test files under `OUTPUT_DIR/tests/`. You do NOT exit until both implementation AND unit tests pass.

## Context You Receive

- `OPENSPEC_CHANGE` — OpenSpec change name
- `SOURCE_ROOT` — absolute path to C source tree (read-only)
- `OUTPUT_DIR` — absolute path to Rust output project
- `BATCH_ID` — which batch from implement-plan you are executing (e.g., "5.1")
- `PRIOR_OUTPUTS.implement_plan` — absolute path to `implement-plan.md`
- `PRIOR_OUTPUTS.specs_dir` — absolute path to `specs/` directory
- `PRIOR_OUTPUTS.design` — absolute path to `design.md`

## Critical Constraint: Output Project Directory

`OUTPUT_DIR` is derived from the required project name in `work/design/README.md`. This path is authoritative and non-negotiable.

- **NEVER** create a new project directory or rename the output project.
- **ALWAYS** write to exactly the `OUTPUT_DIR` path provided in context.
- If `OUTPUT_DIR` already contains a `Cargo.toml`, edit it in place — do not create a sibling project.

## SuperPower Rules (this phase only)

- **Allowed tools**: `run-verification`
- **Allowed filesystem**: read `**`, write `src/**/*.rs`, `Cargo.toml`, `Cargo.lock`, create `src/**/*.rs`
- **Forbidden**: modify tools.py, modify profiles, modify openspec/, modify work/skills/, modify work/subagent/

## Steps

### 1. Read Your Batch Assignment

Read `implement-plan.md`. Find your batch by `BATCH_ID`. Note:
- Which module(s) you are implementing
- Which functions to write
- Which C source files to reference
- Which spec files define the requirements
- The expected build command

### 2. Read Requirements

Read the relevant spec file for your batch (path may be `specs/<capability-id>/spec.md` or `specs/<module>/spec.md` depending on how specs were organized). For each function you implement, find its:
- `REQ-<id>-NNN`: behavioral requirements (SHALL/MUST)
- `INV-<id>-NNN`: invariants that must hold
- Scenarios: GIVEN/WHEN/THEN conditions

### 3. Read C Source

Read the C source files listed in your batch. Understand:
- Function signatures (parameters, return types, semantics)
- Data structure layouts
- Error handling patterns (return codes, error states)
- Side effects (global state mutation, I/O)

### 4. Write Rust Code

For each function in your batch:

**Function signature**: Map C types to Rust types per the design's type mapping.
```
C: fdb_status flashdb_kv_set(fdb_kv* kv, const char* key, const char* value)
Rust: pub fn set(&mut self, key: &str, value: &str) -> Result<(), Error>
```

**Implementation**: Preserve the original logic flow. Translate:
- C control flow (if/else, loops, goto cleanup → `?` or `drop`)
- C memory operations (malloc → `Vec`/`Box`, free → `Drop`)
- C error codes (return -1 → `Err(Error::...)`)
- C pointer arithmetic → safe Rust alternatives (slices, iterators)
- C null checks → `Option<T>`

**Unsafe usage**: Only when strictly required:
- Raw memory manipulation that can't be expressed in safe Rust
- FFI boundaries
- Document every `unsafe` block with a comment explaining why it's needed and why it's sound

**No stubs**: No `todo!()`, no `unimplemented!()`. Every function must be fully implemented.

### 5. Update Project Files

If this is the first batch (or a batch that needs it), ensure:
- `OUTPUT_DIR/Cargo.toml` exists with correct `[package]` and `[dependencies]`
- `OUTPUT_DIR/src/lib.rs` declares all modules your batch adds
- `OUTPUT_DIR/src/<module>.rs` files are created

### 6. Format Code

Run `cargo fmt` before building to ensure consistent formatting:

```
cargo fmt --manifest-path "OUTPUT_DIR/Cargo.toml"
```

This uses Rust's official formatter — deterministic, zero-config, no style debates.

### 7. Build Verification

```
python WORK_DIR/runtime/tools.py run-verification \
  --project-dir "OUTPUT_DIR" \
  --commands '["cargo build --locked"]'
```

If build fails:
- Read the error output carefully
- Fix the issue in your Rust code (type mismatch, missing import, borrow checker)
- Re-run build
- You have up to 3 internal fix attempts

### 7. Write Unit Tests

**This step is MANDATORY. Do not skip it. Do not report success without it.**

Write unit tests for EVERY function you implemented in this batch. Tests go in `OUTPUT_DIR/tests/<capability>_tests.rs`.

For each function:
- Write at least 1 normal path test (valid input → correct output)
- Write at least 1 error path test (invalid input → correct error)
- Write at least 1 boundary test (edge values, empty input, max capacity)

Use Rust's `#[test]` attribute. Every test must have at least one `assert!`/`assert_eq!`/`assert_ne!` macro.

Reference the scenarios from your capability's spec (`specs/<capability-id>/spec.md`) — each scenario should have a corresponding test.

### 8. Test Verification

```
python WORK_DIR/runtime/tools.py run-verification \
  --project-dir "OUTPUT_DIR" \
  --commands '["cargo test <test_filter> --locked"]'
```

Replace `<test_filter>` with the test name pattern for your capability (e.g., `crc32`, `status_table`).

If tests fail:
- **Test bug** (wrong assertion, bad setup): fix the test
- **Implementation bug** (function returns wrong value): fix the implementation, keep the test
- Do NOT weaken the test to make it pass
- Do NOT delete failing tests
- You have up to 3 internal fix attempts

### 9. If Cargo.toml Was Updated

If you added dependencies, `--locked` may fail. Remove `--locked` for the first build, then it's fine for subsequent builds.

## Output

1. Rust source files under `OUTPUT_DIR/src/` for your batch's capability
2. Unit test files under `OUTPUT_DIR/tests/<capability>_tests.rs`
3. Updated `Cargo.toml` and `src/lib.rs` if this is the first batch or added modules
4. Build result: pass/fail, any warnings
5. Test result: pass/fail, test count

## Gate

- `PHASE_PASS` — all functions implemented, ALL unit tests pass, `cargo build` passes
- `PHASE_BLOCKED` — irrecoverable failure (C source unreadable, spec missing critical info, 3+ failed attempts)
- `PHASE_DEGRADED` — build passes but some tests fail (document each failure for Phase 7 repair)
