# c2r-00: Preflight

## Role

Verify that the environment and tools.py are ready for migration. Read-only phase — no writes allowed.

## Context

You receive:
- `WORK_DIR` — path to the work directory
- `SOURCE_ROOT` — path to the C source tree

## SuperPower Rules

Read `work/profiles/superpower/c-to-rust-migration-guards.yaml`, section `preflight`.

- **Allowed tools**: `self-check`
- **Allowed filesystem**: read `work/**` only
- **Forbidden**: any write operations, any source modification

## Steps

1. Run `python tools.py self-check` to verify tools.py is functional
2. Verify `SOURCE_ROOT` exists and contains C source files
3. Verify `WORK_DIR` exists and is writable
4. Verify `cargo` and `rustc` are available on PATH
5. Verify `openspec` CLI is available

## Output

Produce a brief status report:
- tools.py status (pass/fail)
- SOURCE_ROOT status (exists, file count)
- WORK_DIR status (exists, writable)
- Toolchain status (cargo, rustc versions)

## Gate

Return one of:
- `PHASE_PASS` — all checks passed
- `PHASE_BLOCKED` — critical dependency missing (tools.py broken, no cargo, no source)
