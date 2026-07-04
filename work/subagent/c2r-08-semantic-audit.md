# c2r-08: Semantic Audit

## Role

Write and run invariant-derived tests to verify semantic equivalence with the C source. Write phase — produces invariant test files.

## Context

You receive:
- `SOURCE_ROOT` — path to the C source tree
- `OUTPUT_DIR` — path to the Rust output project
- Phase 3 output: `specs/` with behavioral invariants
- Phase 6 output: existing test suite

## SuperPower Rules

Read `work/profiles/superpower/c-to-rust-migration-guards.yaml`, section `semantic-audit`.

- **Allowed tools**: `run-verification`
- **Allowed filesystem**: read `**`, write `tests/**/*.rs`, create `tests/**/*.rs`
- **Forbidden**: modify source code under migration, modify tools.py, modify profiles

## Steps

1. Read each `specs/*/spec.md` for behavioral invariants
2. For each invariant, derive test scenarios:
   - Normal operation
   - Boundary conditions
   - Error paths
   - Reset-after-mutation behavior
   - Failed-operation state preservation
   - Head/middle/tail deletion paths (if applicable)
3. Write invariant tests under `OUTPUT_DIR/tests/`
4. Run:
   ```
   python tools.py run-verification --project-dir OUTPUT_DIR --commands '["cargo test --locked"]'
   ```
5. If invariant tests fail, record the failure — do NOT weaken the test

## Output

- Invariant test files under `OUTPUT_DIR/tests/`
- Test results from tools.py
- Invariant audit report: which invariants verified, which failed

## Gate

Return one of:
- `PHASE_PASS` — all required invariants verified
- `PHASE_BLOCKED` — critical invariant failure that cannot be resolved
- `PHASE_DEGRADED` — most invariants verified, some non-critical failures noted
