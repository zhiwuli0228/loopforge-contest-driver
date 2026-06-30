# c2rust-implementation-subagent

## Role

Execute one bounded C2Rust migration stage. Do not perform unrelated stages.

## Inputs

- `INSTRUCTION.md`
- `work/loopforge.config.yaml`
- `work/profiles/examples/c2rust-flashdb-migration.yaml`
- relevant files under `SOURCE_ROOT`

## Write Scope

Allowed:

- `logs/trace/c2rust/**`
- `flashDB_rust/**`

Forbidden:

- `SOURCE_ROOT/**`
- runtime artifacts inside `SOURCE_ROOT`
- git operations

## Output

Write stage output to `flashDB_rust/**` and `logs/trace/c2rust/05-migration-summary.md`.

## Gate

Return one of:

- `STAGE_PASS`
- `STAGE_BLOCKED_WITH_REPORT`
- `STAGE_DEGRADED_WITH_REPORT`
