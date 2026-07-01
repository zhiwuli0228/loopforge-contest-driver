# Work Asset Guide

`work/` contains the static LoopForge runtime assets used by the contest driver.

## Purpose

- `work/runtime/` holds the Python runner
- `work/scripts/` holds Linux and Windows entry scripts
- `work/skills/` holds agent-facing execution guidance
- `work/rules/`, `work/profiles/`, and `work/subagent/` hold framework contracts

## Input Model

The driver accepts one external runtime input:

- `SOURCE_ROOT`

Requirements, constraints, and acceptance context are read only from the submission asset `work/design/README.md`. `SOURCE_ROOT` is read-only and does not need a README. `work/code/` is a local test fixture and is absent from the formal submission package.

`work/loopforge.config.yaml` provides framework defaults only. It is not the place to manually fill per-task objectives or placeholder verification commands.

## Output Model

Primary run outputs are written to:

- `work/result/output.md`
- `work/result/issues/00-summary.md`
- `work/logs/trace/`

Internal runtime evidence stays under `work/logs/trace/`.
