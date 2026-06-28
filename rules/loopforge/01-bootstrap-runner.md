# Bootstrap Runner Rule

## Objective

Create the LoopForge runtime directory and materialize the Python runner into the target repository.

## Procedure

1. Create `.loopforge/` and the required subdirectories.
2. Read `rules/loopforge/20-runner-source-python.md`.
3. Extract the full Python source code block.
4. Write `.loopforge/runtime/loopforge_runner.py`.
5. Run `python .loopforge/runtime/loopforge_runner.py --init`.
6. Run `python .loopforge/runtime/loopforge_runner.py --self-check`.
7. If successful, continue to mode selection and project detection.

## Required Directories

- `.loopforge/runtime/`
- `.loopforge/task/`
- `.loopforge/spec/`
- `.loopforge/brainstorm/`
- `.loopforge/plan/`
- `.loopforge/leases/`
- `.loopforge/snapshots/`
- `.loopforge/subagents/`
- `.loopforge/gates/`
- `.loopforge/state/`
- `.loopforge/reports/`

## Degrade Strategy

- If `.loopforge/` cannot be created, attempt a root-level fallback report.
- If Python is unavailable, continue in rule-only degraded mode.
- If runner materialization fails, continue in rule-only degraded mode and record the failure.
