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

Requirements, constraints, and acceptance context are read from the source README near `SOURCE_ROOT`, using the first matching file from:

- `README.md`
- `README`
- `readme.md`
- `Readme.md`

`work/loopforge.config.yaml` provides framework defaults only. It is not the place to manually fill per-task objectives or placeholder verification commands.

## Output Model

Primary run outputs are written to:

- `work/result/output.md`
- `work/result/issues/00-summary.md`
- `work/logs/trace/`

Internal runtime evidence stays under `work/logs/trace/`.
