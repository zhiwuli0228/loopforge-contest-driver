---
name: loopforge-driver
description: Execute LoopForge hosted tasks from INSTRUCTION.md and work/loopforge.config.yaml. Use when asked to run LoopForge, start hosted execution, execute contest task, or run unattended repair and verification.
---

# LoopForge Driver Skill

Use this skill as the single agent entry point for LoopForge execution.

This is the canonical contest skill.

Execution root:

- Repository root contains `INSTRUCTION.md`, `code/`, `work/`, `result/`, and `logs/`
- Framework assets live under `work/`
- Target project defaults to `code/`
- Runtime artifacts live under `code/.loopforge/`

Canonical entry:

- `INSTRUCTION.md`

Configuration:

- `work/loopforge.config.yaml`

Runtime output:

- `code/.loopforge/**`

## Mission

Drive an unattended LoopForge run from the repository root while loading framework assets only from `work/` and applying task changes only inside `code/`.

## Required Inputs

- `INSTRUCTION.md`
- `work/loopforge.config.yaml`
- `work/rules/loopforge/core/`
- `work/rules/loopforge/modes/{task.mode}/`
- relevant adapter rules under `work/rules/loopforge/adapters/`
- the configured profile under `work/profiles/`

## Hard Constraints

- Do not modify static files in the current LoopForge root.
- Do not generate or rewrite rules, profiles, or configuration.
- Do not guess verification commands.
- Read `work/loopforge.config.yaml` before selecting adapters or verification steps.
- Treat `code/docs/` design sources as frozen unless the human explicitly changed the task boundary outside LoopForge execution.
- Do not create commits, pushes, pull requests, or submissions.
- Do not write outside `code/` except for reading LoopForge static assets from the current root.
- Write runtime artifacts only under `code/.loopforge/`.
- Stop after verification and final report generation.
- Do not expand task scope beyond configured modules, design sources, or explicitly evidenced dependencies.

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

## Delegated Staged Execution

When `task.mode` in `work/loopforge.config.yaml` is `consistency-check`, this skill must use delegated staged execution.

The primary agent must act as an orchestrator.

The full workflow must not be executed in one monolithic reasoning context.

The orchestrator must not simulate stage workers in the parent Build context.

Subagent contract:

- `subagent_required: true`
- `fallback_to_main_context_allowed: false`
- `missing_subagent_policy: BLOCKED_WITH_REPORT`
- `parent_direct_execution_allowed: false`
- `file_handoff_required: true`

The orchestrator must load:

- `work/loopforge.config.yaml`
- the configured profile
- the configured SuperSpec file
- the configured SuperPower file
- consistency-check mode rules

Each declared stage must be executed by its bound subagent.

If the required subagent layer is unavailable, stop with:

```text
BLOCKED_WITH_REPORT
reason: required subagent unavailable
```

Do not fall back to main-context execution.

No human intervention is allowed between stages.

## Required Consistency Artifacts

All consistency-check stage artifacts must be written under:

`code/.loopforge/consistency/`

Required artifacts:

1. `00-preflight-report.md`
2. `01-design-summary.md`
3. `02-implementation-mapping.md`
4. `03-drift-report.md`
5. `04-repair-plan.md`
6. `05-patch-summary.md`
7. `06-verification-report.md`
8. `07-final-evidence-index.md`

Final report:

`code/.loopforge/reports/final-report.md`

## Repair Plan Policy

`04-repair-plan.md` is a machine handoff artifact.

It is not a human approval document.

The orchestrator must validate the repair plan against SuperPower write permissions.

If the repair plan only touches allowed paths and stays within scope, the patch stage must continue automatically.

If the repair plan violates guardrails, the orchestrator must write a blocked report and generate the final report.

If any stage is missing a declared subagent, output artifact, or `parent_direct_execution_allowed: false`, the orchestrator must stop with `BLOCKED_WITH_REPORT`.

## Coding Skill Invocation

When a SuperSpec stage declares a `skill` field, load and apply that skill before executing the stage.

For patch implementation stages, treat the declared coding skill as the primary implementation guide.

The driver must:

1. read the declared skill
2. read the stage inputs
3. read optional stage references when present
4. obey SuperPower write permissions
5. modify only allowed target files
6. write the declared output artifact
7. include the applied skill path in the patch summary
8. stop with `BLOCKED_WITH_REPORT` if the declared required skill is missing

Do not replace a declared coding skill with generic implementation behavior.

## Patch Stage Rule

For any stage that modifies code:

1. a repair plan must exist
2. if a stage-level `skill` is declared, load and apply it
3. modify only files allowed by the repair plan and SuperPower
4. make the patch summary explicitly state which coding skill was applied
5. do not start verification until the patch summary exists
6. if the coding skill cannot be loaded, generate a blocked report and still finalize when possible

## Coding Skill Replacement Contract

The configured coding skill may be replaced by a stronger coding skill in the future.

A replacement skill must preserve:

1. the same stage input contract
2. the same output path: `code/.loopforge/consistency/05-patch-summary.md`
3. the same gate values
4. the same write-scope restrictions
5. the requirement to report the applied skill path

Do not depend on internal implementation details of the coding skill.

## Rule Load Order

Read the platform contract in this order:

1. `INSTRUCTION.md`
2. `work/loopforge.config.yaml`
3. `work/rules/loopforge/core/00-core.md`
4. `work/rules/loopforge/core/01-work-code-boundary.md`
5. `work/rules/loopforge/core/02-static-rule-ownership.md`
6. `work/rules/loopforge/core/03-verification-contract.md`
7. `work/rules/loopforge/core/04-gate-policy.md`
8. `work/rules/loopforge/core/05-final-report.md`
9. `work/rules/loopforge/core/06-code-generation-boundary.md`
10. all files under `work/rules/loopforge/modes/{task.mode}/`
11. relevant files under `work/rules/loopforge/adapters/`, including Java and Maven rules for Java Maven runs
12. the configured profile under `work/profiles/`

## Required Procedure

1. Read `INSTRUCTION.md`.
2. Read `work/loopforge.config.yaml`.
3. Load all core rules in the declared order.
4. Load the full rule set for `task.mode` from `work/rules/loopforge/modes/{mode}/`.
5. Load adapter rules relevant to the configured language or platform.
6. For Java runs, load both `adapters/java.md` and `adapters/maven.md` when Maven is detected or configured.
7. Read the referenced profile from `work/profiles/`.
8. Confirm the run is operating in a valid contest-root layout with framework assets under `work/`.
9. Inspect `code/` and plan work according to the selected mode.
10. Modify only files inside `code/`.
11. Record mode-specific planning and analysis artifacts under `code/.loopforge/plan/` or another runner-compatible path referenced from `mode-artifacts.md`.
12. Maintain `code/.loopforge/plan/mode-artifacts.md` as the index of mode-specific artifacts produced during the run.
13. Use `work/runtime/loopforge_runner.py` with `--work-dir` and `--code-dir` to initialize artifacts, snapshot diffs, run configured verification, and finalize the report.
14. If verification cannot pass, still leave a blocked final report rather than inventing a verifier.
15. Leave `code/.loopforge/reports/final-report.md` behind and stop.

## Mode Expectations

- `feature-development`: expand requirements, define acceptance criteria, and implement the smallest useful slice.
- `migration`: inventory the source system, define compatibility expectations, and migrate intentionally.
- `defect-repair`: diagnose the failure, identify root cause, and apply the smallest effective patch.
- `consistency-check`: default to analysis, mapping, and drift reporting; repair only if explicitly enabled.
- `consistency-check` on Java Maven projects must read frozen design docs, produce design summary, implementation mapping, traceability matrix, drift report, repair plan, and verification evidence before stopping.
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
- `consistency-check`: design summary, implementation mapping, traceability matrix, drift report, repair plan, test coverage gap
- `skill-generation`: capability inventory, usage contract, skill draft summary, example coverage note
