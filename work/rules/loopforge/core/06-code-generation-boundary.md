# Code Generation Boundary

## Permission Model

Code generation is allowed only when `execution.allow_code_generation` is true in `loopforge.config.yaml`.

If code generation is disabled:

- analysis and reporting may continue
- business-code edits must not occur
- the final report should explain that execution was analysis-only

## Allowed Targets

- source files under `SOURCE_ROOT`
- tests under `SOURCE_ROOT`
- runtime evidence under `SOURCE_ROOT/.loopforge/`

## Forbidden Targets

- any static file in the LoopForge root outside `SOURCE_ROOT`
- version control metadata mutations intended to commit or publish work
- external repositories or sibling directories outside the configured `SOURCE_ROOT`

## Patch Policy

- keep changes mode-appropriate and task-appropriate
- avoid unrelated edits
- for defect repair, prefer minimal patches
- for migration, preserve compatibility goals declared by the mode and profile

LoopForge generates code, records evidence, runs configured verification, writes the final report, and stops.

