# c2r-05: Implement

## Role

Write Rust source code for ONE batch of the migration. Write phase — produces Rust source files under `OUTPUT_DIR/src/`.

## Context You Receive

- `OPENSPEC_CHANGE` — OpenSpec change name
- `SOURCE_ROOT` — path to C source tree (read-only)
- `OUTPUT_DIR` — path to Rust output project
- `BATCH_ID` — which batch from implement-plan you are executing (e.g., "5.1")
- `PRIOR_OUTPUTS.implement_plan` — path to `implement-plan.md`
- `PRIOR_OUTPUTS.specs_dir` — path to `specs/` directory
- `PRIOR_OUTPUTS.design` — path to `design.md`

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

Read the relevant `specs/<module>/spec.md` for your batch. For each function you implement, find its:
- `REQ-<module>-XXX`: behavioral requirements (SHALL/MUST)
- `INV-<module>-XXX`: invariants that must hold
- Scenarios: WHEN/THEN conditions

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

### 6. Build Verification

```
python WORK_DIR/runtime/tools.py run-verification \
  --project-dir "OUTPUT_DIR" \
  --commands '["cargo build --locked"]'
```

If build fails:
- Read the error output carefully
- Fix the issue in your Rust code (type mismatch, missing import, borrow checker)
- Re-run build
- You have up to 3 internal fix attempts before reporting `PHASE_DEGRADED`

### 7. If Cargo.toml Was Updated

If you added dependencies, `--locked` may fail. Remove `--locked` for the first build, then it's fine for subsequent builds.

## Output

1. Rust source files under `OUTPUT_DIR/src/` for your batch's modules
2. Updated `Cargo.toml` and `src/lib.rs` if this is the first batch or added modules
3. Build result: pass/fail, any warnings

## Gate

- `PHASE_PASS` — all functions in batch implemented, `cargo build` passes
- `PHASE_BLOCKED` — irrecoverable failure (C source unreadable, spec missing critical info, 3+ failed build attempts)
- `PHASE_DEGRADED` — build passes with warnings, or some non-critical functions could not be implemented
