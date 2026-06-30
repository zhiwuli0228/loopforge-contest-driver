# LoopForge Core

## Purpose

LoopForge is a generic contest execution framework.

## Stable Model

- The repository root contains static framework assets.
- `SOURCE_ROOT` is the resolved source tree.
- `SOURCE_ROOT/.loopforge/` is internal runtime evidence.
- `task.mode` selects the generic workflow shape.
- `task.profile` selects declarative defaults for the current run.

## Execution Intent

LoopForge should:

- read platform instructions from the repository root
- read task context from the README under `SOURCE_ROOT`
- inspect or modify only the resolved source tree
- leave evaluator-facing outputs under `result/` and `logs/`

LoopForge must not:

- assume a single contest problem or business domain
- require humans to fill task metadata before a run
- hard-code a specific source project path into the framework
- perform commit, push, PR, or submission actions

