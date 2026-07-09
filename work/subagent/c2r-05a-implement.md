# c2r-05a: Implement (Code + Compile)

## Role

Write Rust source code for ONE batch (one capability). Write phase — produces Rust source files under `OUTPUT_DIR/src/`. You do NOT write tests — that is Phase 5b's job. You do NOT exit until `cargo build` passes for your batch's files.

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
- If you are the **scaffold batch** and `OUTPUT_DIR` already contains a `Cargo.toml`, edit it in place — do not create a sibling project.
- If you are a **non-scaffold batch**, do NOT modify `Cargo.toml`, `lib.rs`, or `types.rs` — these are owned by the scaffold batch.

## Relationship to Phase 5b

After you complete, Phase 5b will:
- Read the compiled Rust source you wrote
- Read the **Test Specification** section from the spec (concrete inputs, expected outputs, assertion hints)
- Write unit tests under `OUTPUT_DIR/tests/<capability>_tests.rs`
- Run tests and fix any bugs found (including implementation bugs in your code)

You should write correct code, but Phase 5b is the safety net. Focus on getting clean compilation.

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

**Extract `rust_target`**: From your batch entry, extract the `Rust target files` (or `rust_target`) field. This is the complete list of `.rs` files your batch is permitted to write. Store this list as your batch's **write scope**. You SHALL NOT create, modify, or delete any `.rs` file outside this list. Reading any file in `OUTPUT_DIR/` is allowed and encouraged.

**Determine if scaffold batch**: Read all batch entries in `implement-plan.md`. Find the lowest `batch_id` at P0 priority. If your `BATCH_ID` matches that lowest P0 batch, you are the **scaffold batch** with special responsibilities (see Step 5).

### 2. Read Requirements

Read the relevant spec file for your batch. For each function you implement, find its:
- `REQ-<id>-NNN`: behavioral requirements (SHALL/MUST)
- `INV-<id>-NNN`: invariants that must hold
- Scenarios: GIVEN/WHEN/THEN conditions

Ignore the "Test Specification" section — that is consumed by Phase 5b, not you.

### 3. Read C Source

Read the C source files listed in your batch. Understand:
- Function signatures (parameters, return types, semantics)
- Data structure layouts
- Error handling patterns (return codes, error states)
- Side effects (global state mutation, I/O)

### 4. Write Rust Code

**File ownership constraint**: You SHALL only create or modify files listed in your batch's `rust_target` (extracted in Step 1). You may READ any file in `OUTPUT_DIR/` to understand types, traits, and signatures.

For each function in your batch:

**Function signature**: Map C types to Rust types per the design's type mapping.
```
C: int lib_init(config_t* cfg, const char* path)
Rust: pub fn init(cfg: &Config, path: &str) -> Result<(), Error>
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

### 5. Update Project Files (Scaffold Batch Only)

**If you are the scaffold batch** (determined in Step 1):

Before writing your own capability code:
1. Read ALL batch entries from `implement-plan.md`
2. Extract every batch's `Rust target files` (or `rust_target`) field
3. Derive the module name from each target file (e.g., `src/kvdb.rs` → `kvdb`)
4. Extract all feature flags mentioned in any batch entry (check `**Build command**` lines for `--features` flags)

Write complete infrastructure files:

**`OUTPUT_DIR/src/lib.rs`**: Write `pub mod` declarations for EVERY module discovered from the plan. Include `#![cfg_attr(...)]` attributes as appropriate. No subsequent batch SHALL need to add, remove, or reorder `pub mod` entries.

**`OUTPUT_DIR/Cargo.toml`**: Write `[package]`, `[dependencies]`, and `[features]` sections. The `[features]` section SHALL include every feature flag discovered from the plan. The `[dependencies]` section SHALL include all crates needed by any batch (infer from the Rust code patterns in the design).

**`OUTPUT_DIR/src/types.rs`** (or equivalent shared module): Write minimal foundational types that all batches depend on — at minimum an `Error` type (enum or struct) and a root database handle type.

**Validate plan completeness**: Before writing infrastructure files, check that every batch entry in `implement-plan.md` has a `Rust target files` (or `rust_target`) field. If any batch is missing this field, return `PHASE_BLOCKED` with a message naming the incomplete batch.

**If you are NOT the scaffold batch**: Skip this step entirely. Do NOT create, modify, or delete `lib.rs`, `Cargo.toml`, or `types.rs`. These files were already written by the scaffold batch. Proceed directly to Step 6.

### 6. Format Code

Run `cargo fmt` before building to ensure consistent formatting:

```
cargo fmt --manifest-path "OUTPUT_DIR/Cargo.toml"
```

### 7. Build Verification

```
python WORK_DIR/runtime/tools.py run-verification \
  --project-dir "OUTPUT_DIR" \
  --commands '["cargo build --locked"]'
```

If build fails, classify errors before acting:

**Errors in your own files** (files in your `rust_target` list):
- Read the error output carefully
- Fix the issue in your Rust code (type mismatch, missing import, borrow checker)
- Re-run build
- You have up to 3 internal fix attempts for errors in your own files

**Errors in other batches' files** (files NOT in your `rust_target` list):
- Do NOT modify those files
- Record the exact file path, line number, and error message for each external error
- If there are also errors in your own files, fix only those (up to 3 attempts)
- If after fixing your own errors the build still fails due to external errors, return `PHASE_DEGRADED` with the external error details
- If the build failure is ONLY due to external errors (your files compile clean), return `PHASE_DEGRADED` with the external error details

### 8. If Cargo.toml Was Updated

If you added dependencies, `--locked` may fail. Remove `--locked` for the first build, then it's fine for subsequent builds.

## Output

1. Rust source files under `OUTPUT_DIR/src/` for your batch's capability (only files in your `rust_target` list)
2. If scaffold batch: complete `Cargo.toml`, `src/lib.rs`, and `src/types.rs` with all module/feature declarations
3. Build result: pass/fail, any warnings, external error report (if PHASE_DEGRADED due to cross-batch errors)

## Gate

- `PHASE_PASS` — all functions implemented, `cargo build` passes with no errors in your batch's files
- `PHASE_BLOCKED` — irrecoverable failure (C source unreadable, spec missing critical info, 3+ failed fix attempts on own files, scaffold batch detects missing `rust_target` in a batch entry)
- `PHASE_DEGRADED` — build passes with compiler warnings, OR build fails due to external compilation errors in other batches' files (document file paths, line numbers, and error messages)
