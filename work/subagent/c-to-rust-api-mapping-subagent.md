# c-to-rust-api-mapping-subagent

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

Forbidden:

- `SOURCE_ROOT/**`
- runtime artifacts inside `SOURCE_ROOT`
- git operations

## Output

Write the stage report to `work/logs/trace/c-to-rust/02-api-mapping.md`.
The report must record the semantic mapping between the active C source project APIs and generated Rust functions or modules.

## Gate

Return one of:

- `STAGE_PASS`
- `STAGE_BLOCKED_WITH_REPORT`
- `STAGE_DEGRADED_WITH_REPORT`
