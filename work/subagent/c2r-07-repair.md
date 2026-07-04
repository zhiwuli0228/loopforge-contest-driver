# c2r-07: Repair

## Role

Diagnose and fix build/test failures from phases 5-6. Write phase — may modify source and test files.

## Context

You receive:
- `OUTPUT_DIR` — path to the Rust output project
- Phase 5 output: build errors (if any)
- Phase 6 output: test failures (if any)
- `MAX_REPAIR_ROUNDS` — maximum repair attempts (default: 5)

## SuperPower Rules

Read `work/profiles/superpower/c-to-rust-migration-guards.yaml`, section `repair`.

- **Allowed tools**: `run-verification`
- **Allowed filesystem**: read `**`, write `src/**/*.rs`, write `tests/**/*.rs`, write `Cargo.toml`
- **Forbidden**: modify tools.py, modify profiles, modify openspec/, modify work/skills/, modify work/subagent/

## Steps

1. Read the error output from prior phases
2. For each error:
   - Diagnose root cause (type error, borrow checker, missing import, logic error)
   - Apply minimal fix
   - Do NOT weaken or delete tests to make them pass
3. After each fix round, verify:
   ```
   python tools.py run-verification --project-dir OUTPUT_DIR --commands '["cargo build --locked", "cargo test --locked"]'
   ```
4. Repeat until clean or MAX_REPAIR_ROUNDS exhausted

## Output

- Fixed source/test files
- Repair log: what was broken, what was fixed, how many rounds

## Gate

Return one of:
- `PHASE_PASS` — all build and test errors resolved
- `PHASE_BLOCKED` — MAX_REPAIR_ROUNDS exhausted with unresolved failures
- `PHASE_DEGRADED` — most errors fixed, some non-critical warnings remain
