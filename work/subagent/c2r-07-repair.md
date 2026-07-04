# c2r-07: Repair

## Role

Diagnose and fix all build errors and test failures from phases 5 and 6. Iterative repair loop. Write phase — may modify source and test files.

## Context You Receive

- `OUTPUT_DIR` — path to Rust output project
- `WORK_DIR` — path to work directory
- `PRIOR_OUTPUTS.build_errors` — build errors from Phase 5 (all batches)
- `PRIOR_OUTPUTS.test_failures` — test failures from Phase 6 (all batches)
- `MAX_REPAIR_ROUNDS` — maximum repair attempts (default: 5, from loopforge.config.yaml)

## SuperPower Rules (this phase only)

- **Allowed tools**: `run-verification`
- **Allowed filesystem**: read `**`, write `src/**/*.rs`, write `tests/**/*.rs`, write `Cargo.toml`
- **Forbidden**: modify tools.py, modify profiles, modify openspec/, modify work/skills/, modify work/subagent/

## Steps

### 1. Collect All Errors

Gather error output from all Phase 5 and Phase 6 batches. Categorize each error:

| Category | Example | Fix Strategy |
|----------|---------|-------------|
| Type mismatch | `expected usize, found u32` | Fix type annotation or cast |
| Borrow checker | `cannot borrow as mutable` | Clone, restructure, or use RefCell |
| Missing import | `use of undeclared type` | Add `use` statement |
| Missing module | `unresolved module` | Add `mod` declaration to lib.rs |
| Logic error | wrong return value | Trace C source, fix logic |
| Test assertion | expected X, got Y | Only fix if test is wrong — never weaken |
| Missing dependency | `failed to resolve: use of undeclared crate` | Add to Cargo.toml |
| Compilation error | syntax, missing semicolon, etc. | Minimal fix |

### 2. Prioritize Fixes

Fix in this order:
1. Compilation errors (syntax, missing imports, missing modules)
2. Type errors
3. Borrow checker errors
4. Dependency errors
5. Logic errors
6. Test assertion errors (only if test is provably wrong)

### 3. Fix → Verify Loop

For each round (1 to MAX_REPAIR_ROUNDS):

**a. Apply fixes**: Fix up to 5 errors at a time. Apply minimal changes — do not refactor, do not redesign.

**b. Format**: Run `cargo fmt --manifest-path "OUTPUT_DIR/Cargo.toml"` to normalize formatting after fixes.

**c. Verify**:
```
python WORK_DIR/runtime/tools.py run-verification \
  --project-dir "OUTPUT_DIR" \
  --commands '["cargo build --locked", "cargo test --locked"]'
```

**d. Evaluate**:
- All build + test pass → `PHASE_PASS`, exit loop
- Fewer errors than previous round → continue to next round
- Same errors persist → re-diagnose, try different approach
- More errors → revert last changes, re-diagnose

### 4. Repair Rules

**DO**:
- Fix type annotations, add imports, add module declarations
- Clone values to resolve borrow conflicts
- Add missing dependencies to Cargo.toml
- Correct logic errors by re-reading C source
- Fix test assertions that are provably wrong (e.g., wrong expected value)

**DO NOT**:
- Delete or comment out failing tests
- Weaken assertions (e.g., `assert_eq!(x, 5)` → `assert!(true)`)
- Rewrite functions from scratch
- Change public API signatures
- Introduce `unsafe` to work around borrow checker

### 5. Write Repair Log

Document every fix:

```
Repair Log
==========
Round 1:
  - src/kv.rs:42 — type mismatch: changed get() return type from u32 to usize
  - src/core.rs:15 — missing import: added use crate::types::Status
  - Cargo.toml: added [dependencies] serde = "1"
  Result: build passed, 3 tests still failing

Round 2:
  - src/kv.rs:78 — logic error: del() didn't update len counter
  - tests/test_kv.rs:30 — test assertion wrong: expected 0, corrected to 1
  Result: all passing
```

## Output

1. Fixed source/test files under `OUTPUT_DIR/`
2. Repair log (in your return message)
3. Final build + test results

## Gate

- `PHASE_PASS` — `cargo build` and `cargo test` both pass with 0 errors
- `PHASE_BLOCKED` — MAX_REPAIR_ROUNDS exhausted, failures remain
- `PHASE_DEGRADED` — build passes, all tests pass, but compiler warnings remain
