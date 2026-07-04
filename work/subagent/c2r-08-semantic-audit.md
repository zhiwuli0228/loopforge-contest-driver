# c2r-08: Semantic Audit

## Role

Write and run behavioral invariant tests to verify the Rust implementation is semantically equivalent to the C original. Write phase — produces invariant test files.

## Context You Receive

- `SOURCE_ROOT` — path to C source tree (for reference)
- `OUTPUT_DIR` — path to Rust output project
- `WORK_DIR` — path to work directory
- `PRIOR_OUTPUTS.specs_dir` — path to `specs/` directory (contains behavioral invariants)

## SuperPower Rules (this phase only)

- **Allowed tools**: `run-verification`
- **Allowed filesystem**: read `**`, write `tests/**/*.rs`, create `tests/**/*.rs`
- **Forbidden**: modify source code under migration, modify tools.py, modify profiles

## Steps

### 1. Extract Invariants from Specs

Read every `specs/<module>/spec.md`. Extract all `INV-<module>-XXX` invariants. An invariant is a property that must hold before and after operations.

Examples of invariants:
- After `reset()`, all stored data is cleared
- After a failed `set()`, the store is unchanged
- `len()` returns 0 for a new/fresh instance
- `get()` after `del()` returns None
- Iterator yields items in insertion order
- Capacity is never exceeded

### 2. Categorize Invariants

Group invariants by test category:

| Category | What to Test | Example |
|----------|-------------|---------|
| **State initialization** | Fresh instance state | new() → len=0, is_empty=true |
| **Reset behavior** | State after reset | reset() → all data cleared, iter yields nothing |
| **Error state preservation** | State after failed op | failed set() → store unchanged, len unchanged |
| **Boundary conditions** | Edge values | empty key, max-size value, zero-length input |
| **Cross-operation consistency** | Sequence of ops | set→get, set→del→get, set→set(overwrite)→get |
| **Collection invariants** | Properties of collections | no duplicates, ordered, capacity limit |
| **Resource cleanup** | Drop behavior | no leaks (where testable), Drop called |

### 3. Write Invariant Tests

For each invariant category, write focused test functions:

```rust
// Write to tests/invariant_<category>.rs
// Each file groups related invariants

#[test]
fn invariant_reset_clears_all_data() {
    // Setup: create instance, add data
    // Exercise: call reset()
    // Assert: len=0, get returns None for all previously set keys
}

#[test]
fn invariant_failed_set_preserves_state() {
    // Setup: create instance, add known data, snapshot state
    // Exercise: attempt invalid set (e.g., oversized value)
    // Assert: state identical to snapshot, previous data still accessible
}

#[test]
fn invariant_boundary_empty_key() {
    // Setup: create instance
    // Exercise: set("", "value")
    // Assert: defined behavior — either error or success, must be consistent
}
```

Write at least 3 invariant tests per module, covering the most critical behavioral properties.

### 4. Run Invariant Tests

```
python WORK_DIR/runtime/tools.py run-verification \
  --project-dir "OUTPUT_DIR" \
  --commands '["cargo test --locked"]'
```

### 5. Analyze Failures

For each failing invariant test:
- Is the test correct? (re-read the C source to verify expected behavior)
- Is the implementation wrong? (logic error in the Rust code)
- Is the invariant underspecified? (C behavior is ambiguous)

**Do NOT weaken or remove a failing invariant test.** Record the failure with analysis. If the implementation is wrong, note it for potential repair. If the invariant itself is flawed (doesn't match actual C behavior), note that too.

### 6. Produce Audit Report

```
Semantic Audit Report
=====================
Module: core
  INV-core-001 (reset clears data):     PASS
  INV-core-002 (error state preserved): PASS
  INV-core-003 (boundary empty input):  FAIL — implementation returns Ok(()) but C returns error

Module: kv
  INV-kv-001 (insertion order):         PASS
  INV-kv-002 (capacity limit):          PASS

Summary: X/Y invariants verified, Z failures
```

## Output

1. Invariant test files under `OUTPUT_DIR/tests/invariant_*.rs`
2. Test results from tools.py
3. Semantic audit report (in your return message)

## Gate

- `PHASE_PASS` — all invariant tests written and pass
- `PHASE_BLOCKED` — critical invariant failure that indicates fundamental semantic mismatch (e.g., core API behavior differs from C)
- `PHASE_DEGRADED` — most invariants pass, some non-critical failures (e.g., edge case behavior differs but documented in C as undefined)
