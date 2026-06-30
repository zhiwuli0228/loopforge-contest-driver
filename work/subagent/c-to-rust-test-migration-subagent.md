# c-to-rust-test-migration-subagent

## Role

Execute one bounded generic C-to-Rust migration stage. Do not perform unrelated stages.

## Inputs

- `INSTRUCTION.md`
- `work/loopforge.config.yaml`
- `work/profiles/examples/c-to-rust-migration.yaml`
- relevant files under `SOURCE_ROOT`

## Write Scope

Allowed:

- `work/logs/trace/c-to-rust/**`
- runtime-derived Rust output project tests directory

Forbidden:

- `SOURCE_ROOT/**`
- runtime artifacts inside `SOURCE_ROOT`
- git operations

## Output

Write stage output to the runtime-derived Rust test directory and `work/logs/trace/c-to-rust/04-test-mapping.md`.
Every generated Rust test must include assertions and must trace back to an explicit C scenario.

## Gate

Return one of:

- `STAGE_PASS`
- `STAGE_BLOCKED_WITH_REPORT`
- `STAGE_DEGRADED_WITH_REPORT`
