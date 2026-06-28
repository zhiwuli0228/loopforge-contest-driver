# loopforge-driver

Use this skill as the single entry point for unattended contest execution.

## Mission

Bootstrap and drive a LoopForge workflow inside the current target repository using local rules and a generated Python runner.

## Required Inputs

- the user task, problem statement, spec, or repair goal
- the `rules/loopforge/` rule pack

## Hard Constraints

- Do not ask for human confirmation.
- Do not use hooks.
- Do not create multiple workflows.
- Do not create multiple PRs.
- Do not skip final report generation when the milestone supports it.
- Do not claim success without verification evidence.
- Bootstrap runner first.
- Use fail-soft, block-late gate policy.
- Keep all changes inside the current work tree.
- Do not introduce third-party dependencies for the runner.

## Required Rule Load Order

1. `rules/loopforge/00-core.md`
2. `rules/loopforge/01-bootstrap-runner.md`
3. `rules/loopforge/02-mode-selection.md`
4. `rules/loopforge/03-spec-normalization.md`
5. `rules/loopforge/04-brainstorm.md`
6. `rules/loopforge/05-subagent-lease.md`
7. `rules/loopforge/06-gate-policy-contest.md`
8. `rules/loopforge/07-verification-policy.md`
9. `rules/loopforge/08-repair-policy.md`
10. `rules/loopforge/09-final-report.md`
11. Mode-specific and language-specific rules as needed
12. `rules/loopforge/20-runner-source-python.md`

## Execution Procedure

1. Select the task mode using `02-mode-selection.md`.
2. Create `.loopforge/` and all required subdirectories.
3. Extract the Python code block from `20-runner-source-python.md`.
4. Write `.loopforge/runtime/loopforge_runner.py`.
5. Run the runner with `--init` and `--self-check`.
6. Run `--prepare <task-file>` to generate task, normalized spec, brainstorm, plan, and lease artifacts.
7. Record task mode and project detection results.
8. Run `--start-apply` before code changes to create the pre-apply snapshot and subagent report scaffold.
9. Apply changes under lease control.
10. Run `--complete-apply` after coding to update the subagent report with detected changes.
11. Run `--integrate-review` after coding and before verification.
12. Run verification and, if needed, `--repair` before finalization.
13. Run finalize after verification or repair exhaustion.
14. Always leave evidence files behind, even in degraded mode.

## Output Expectations

The workflow should leave behind:

- `.loopforge/state/loop-state.json`
- `.loopforge/gates/gate-events.md`
- `.loopforge/snapshots/*.diff` when git is available
- `.loopforge/reports/final-report.md` when finalize is implemented

## Current Milestone Note

In this repository version, the runner is only required to support:

- `--init`
- `--self-check`
- `--detect`
- `--snapshot <name>`
- `--prepare <task-file>`
- `--start-apply`
- `--complete-apply`
- `--integrate-review`
- `--verify`
- `--repair`
- `--finalize`

Treat repair as a documented future stage unless explicitly implemented later.
