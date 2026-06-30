# c-to-rust-final-report-subagent

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
- `work/result/**`

Forbidden:

- `SOURCE_ROOT/**`
- runtime artifacts inside `SOURCE_ROOT`
- git operations

## Output

Write stage output to `work/result/output.md` and `work/result/issues/00-summary.md`.
`READY_FOR_EVALUATION` is valid only when cargo build, cargo test, unsafe gate, and semantic gate all pass.

## Gate

Return one of:

- `STAGE_PASS`
- `STAGE_BLOCKED_WITH_REPORT`
- `STAGE_DEGRADED_WITH_REPORT`
