# c-to-rust-verification-subagent

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

Forbidden:

- `SOURCE_ROOT/**`
- runtime artifacts inside `SOURCE_ROOT`
- git operations

## Output

Write the stage report to `logs/trace/c-to-rust/06-verification-report.md` and `logs/trace/c-to-rust/unsafe-ratio.json`.
The report must include cargo build, cargo test, unsafe gate, semantic gate, and repair-loop evidence.

## Gate

Return one of:

- `STAGE_PASS`
- `STAGE_BLOCKED_WITH_REPORT`
- `STAGE_DEGRADED_WITH_REPORT`
