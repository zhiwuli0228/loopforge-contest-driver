# c2r-05: Implement

## Role

Write Rust source code for one batch of the migration. Write phase — produces Rust source files.

## Context

You receive:
- `OPENSPEC_CHANGE` — the OpenSpec change name
- `SOURCE_ROOT` — path to the C source tree
- `OUTPUT_DIR` — path to the Rust output project
- `BATCH_ID` — which batch from the implement-plan to execute
- Phase 4 output: `implement-plan.md` and `specs/` locations

## SuperPower Rules

Read `work/profiles/superpower/c-to-rust-migration-guards.yaml`, section `implement`.

- **Allowed tools**: `run-verification`
- **Allowed filesystem**: read `**`, write `src/**/*.rs`, `Cargo.toml`, `Cargo.lock`, create `src/**/*.rs`
- **Forbidden**: modify tools.py, modify profiles, modify openspec/, modify work/skills/, modify work/subagent/

## Steps

1. Read `implement-plan.md` to identify your batch's modules and functions
2. Read the relevant `specs/*/spec.md` for requirements
3. Read the C source files for the functions in your batch
4. Write Rust source code:
   - Create module files under `OUTPUT_DIR/src/`
   - Update `Cargo.toml` if needed (dependencies, features)
   - Prefer safe Rust; `unsafe` only when strictly required and documented
   - No `todo!()` or `unimplemented!()`
5. Run build verification:
   ```
   python tools.py run-verification --project-dir OUTPUT_DIR --commands '["cargo build --locked"]'
   ```
6. If build fails, diagnose and fix within this phase

## Output

- Rust source files under `OUTPUT_DIR/src/`
- Build result from tools.py

## Gate

Return one of:
- `PHASE_PASS` — code written, `cargo build` passes
- `PHASE_BLOCKED` — irrecoverable build failure after reasonable repair attempts
- `PHASE_DEGRADED` — code written but with warnings or partial coverage
