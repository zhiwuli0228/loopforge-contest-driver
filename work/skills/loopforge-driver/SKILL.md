# loopforge-driver

Use this skill as the single agent entry point for LoopForge execution.

## Mission

Drive an unattended LoopForge run using the human-maintained `work/` package and apply task changes only inside `code/`.

## Required Inputs

- `work/INSTRUCTION.md`
- `work/loopforge.config.yaml`
- `work/rules/loopforge/core/`
- `work/rules/loopforge/modes/{task.mode}/`
- relevant adapter rules under `work/rules/loopforge/adapters/`
- the configured profile under `work/profiles/`

## Hard Constraints

- Do not modify static files in `work/`.
- Do not generate or rewrite rules, profiles, or configuration.
- Do not guess verification commands.
- Do not create commits, pushes, pull requests, or submissions.
- Do not write outside `code/` except for reading files under `work/`.
- Write runtime artifacts only under `code/.loopforge/`.
- Stop after verification and final report generation.

## Cross-platform Execution Policy

Development and local testing may run on Windows. Official submission runs on Linux.

The agent must follow these rules:

1. Do not hard-code Windows-only paths.
2. Do not hard-code Linux-only paths except in Linux submission scripts.
3. Use `/` in configuration paths.
4. Treat `work/scripts/bootstrap.sh` as the official Linux entry.
5. Treat `work/scripts/bootstrap.ps1` as the Windows development entry.
6. Use the Python runner for cross-platform deterministic actions.
7. Do not modify verification commands.
8. Select platform-specific commands from `work/loopforge.config.yaml`.
9. If a platform-specific verification command is missing, fall back to default commands.
10. If no command is configured, generate `BLOCKED_WITH_REPORT`.

## Rule Load Order

Read the platform contract in this order:

1. `work/INSTRUCTION.md`
2. `work/loopforge.config.yaml`
3. `work/rules/loopforge/core/00-core.md`
4. `work/rules/loopforge/core/01-work-code-boundary.md`
5. `work/rules/loopforge/core/02-static-rule-ownership.md`
6. `work/rules/loopforge/core/03-verification-contract.md`
7. `work/rules/loopforge/core/04-gate-policy.md`
8. `work/rules/loopforge/core/05-final-report.md`
9. `work/rules/loopforge/core/06-code-generation-boundary.md`
10. all files under `work/rules/loopforge/modes/{task.mode}/`
11. relevant files under `work/rules/loopforge/adapters/`
12. the configured profile under `work/profiles/`

## Required Procedure

1. Read `work/INSTRUCTION.md`.
2. Read `work/loopforge.config.yaml`.
3. Load all core rules in the declared order.
4. Load the full rule set for `task.mode` from `work/rules/loopforge/modes/{mode}/`.
5. Load adapter rules relevant to the configured language or platform.
6. Read the referenced profile from `work/profiles/`.
7. Confirm the run is operating in a valid `work/` and `code/` sibling layout.
8. Inspect `code/` and plan work according to the selected mode.
9. Modify only files inside `code/`.
10. Record mode-specific planning and analysis artifacts under `code/.loopforge/plan/` while executing the selected mode.
11. Maintain `code/.loopforge/plan/mode-artifacts.md` as the index of mode-specific artifacts produced during the run.
12. Use `work/runtime/loopforge_runner.py` with `--work-dir` and `--code-dir` to initialize artifacts, snapshot diffs, run configured verification, and finalize the report.
13. If verification cannot pass, still leave a blocked final report rather than inventing a verifier.
14. Leave `code/.loopforge/reports/final-report.md` behind and stop.

## Mode Expectations

- `feature-development`: expand requirements, define acceptance criteria, and implement the smallest useful slice.
- `migration`: inventory the source system, define compatibility expectations, and migrate intentionally.
- `defect-repair`: diagnose the failure, identify root cause, and apply the smallest effective patch.
- `consistency-check`: default to analysis, mapping, and drift reporting; repair only if explicitly enabled.
- `skill-generation`: produce a reusable business skill from an underlying capability without altering LoopForge core.

## Runner Invocation Pattern

```text
python work/runtime/loopforge_runner.py --work-dir work --code-dir code --init --self-check --detect
python work/runtime/loopforge_runner.py --work-dir work --code-dir code --snapshot before-change
python work/runtime/loopforge_runner.py --work-dir work --code-dir code --verify --finalize
```

## Output Expectations

At minimum, the run should leave behind:

- `code/.loopforge/runtime/loopforge_runner.py`
- `code/.loopforge/state/loop-state.json`
- `code/.loopforge/state/verification-summary.json` when verification is attempted
- `code/.loopforge/gates/gate-events.md`
- `code/.loopforge/plan/mode-artifacts.md`
- `code/.loopforge/reports/final-report.md`

## Mode Artifact Contract

Mode-specific artifacts should stay lightweight and auditable. Write them under `code/.loopforge/plan/` and index them from `mode-artifacts.md`.

Recommended entries:

- `feature-development`: requirement summary, brainstorm decision note, design draft, implementation plan
- `migration`: source inventory, target architecture summary, compatibility contract, migration plan
- `defect-repair`: failure summary, root cause statement, minimal patch plan, changed-file summary
- `consistency-check`: design summary, implementation mapping, traceability matrix, drift report
- `skill-generation`: capability inventory, usage contract, skill draft summary, example coverage note
