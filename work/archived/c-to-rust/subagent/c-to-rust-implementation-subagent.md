# c-to-rust-implementation-subagent

## Role

Execute one bounded generic C-to-Rust migration stage. Do not perform unrelated stages.

## Inputs

- `INSTRUCTION.md`
- `work/loopforge.config.yaml`
- `work/profiles/examples/c-to-rust-migration.yaml`
- relevant files under `SOURCE_ROOT`

## Write Scope

Allowed:

- `logs/trace/c-to-rust/**`
- runtime-derived Rust output project

Forbidden:

- `SOURCE_ROOT/**`
- runtime artifacts inside `SOURCE_ROOT`
- git operations

## Output

Write stage output to the runtime-derived Rust output project and `logs/trace/c-to-rust/05-migration-summary.md`.
Generated Rust code must not contain `todo!()` or `unimplemented!()`.

## Gate

Return one of:

- `STAGE_PASS`
- `STAGE_BLOCKED_WITH_REPORT`
- `STAGE_DEGRADED_WITH_REPORT`
