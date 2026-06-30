---
name: loopforge-driver
description: Execute the contest driver from INSTRUCTION.md using SOURCE_ROOT plus the source README as the primary task context. Use when asked to run LoopForge, start hosted execution, execute the contest task, or perform unattended repair and verification.
---

# LoopForge Driver Skill

Use this skill as the entry point for contest execution.

## Execution Root

- Repository root contains `INSTRUCTION.md`, `work/`, `result/`, and `logs/`; local source fixtures may live under `.code/`
- Framework assets live under `work/`
- Runtime evidence is written under `logs/trace/`
- Evaluator-facing outputs are written under `result/` and `logs/`

## Required Inputs

- `INSTRUCTION.md`
- `SOURCE_ROOT`
- `${SOURCE_ROOT}/README.md`, `${SOURCE_ROOT}/README`, `${SOURCE_ROOT}/readme.md`, or `${SOURCE_ROOT}/Readme.md`
- `work/loopforge.config.yaml`
- `work/rules/loopforge/core/`
- `work/rules/loopforge/modes/{task.mode}/`
- relevant adapter rules under `work/rules/loopforge/adapters/`
- the configured profile under `work/profiles/`

## Mission

Drive an unattended contest run from the repository root while treating `SOURCE_ROOT` and its README as the primary task-definition input.

## Hard Constraints

- Do not modify static files in the LoopForge root during execution.
- Do not require humans to fill placeholder task name, language, objective, or verification commands.
- Read `work/loopforge.config.yaml` as framework defaults, not as the sole source of task intent.
- Parse the source README first and record the selected README path.
- If no source README exists, degrade into `BLOCKED_WITH_REPORT` with explicit evidence in `result/issues/00-summary.md` and `logs/trace/`.
- Do not create commits, pushes, pull requests, or submissions.
- Do not write into `SOURCE_ROOT`; generated outputs must stay under a runtime-derived repository-root Rust output project, `result/`, and `logs/`.
- Stop after verification and report generation.

## Source Root Protocol

Resolve the source root in this order:

1. platform-provided source path
2. `--source-root`
3. `SOURCE_ROOT`
4. path extracted from natural-language task input and normalized into `SOURCE_ROOT`
5. Linux fallback `/__CONTEST_PLATFORM_SOURCE_ROOT__/source`
6. local fallback `.code`

The driver must inspect the source README and use it to infer requirements and constraints before planning work.

## Entrypoints

- Linux: `SOURCE_ROOT="/path/to/source" bash work/scripts/run.sh`
- Linux fallback: `bash work/scripts/run.sh`
- Windows: `$env:SOURCE_ROOT="C:\path\to\source"; powershell -ExecutionPolicy Bypass -File work/scripts/run.ps1`

`bootstrap.sh` and `bootstrap.ps1` are compatibility wrappers over the same `SOURCE_ROOT` protocol.

## Delegated Execution

When `task.mode` is `consistency-check`, delegated staged execution rules still apply.

If the required subagent layer is unavailable for a task mode that explicitly requires it, stop with:

```text
BLOCKED_WITH_REPORT
reason: required subagent unavailable
```

Do not fall back to simulated stage execution in the main context for such modes.

For non-delegated modes, continue with the normal contest run.

## Required Procedure

1. Read `INSTRUCTION.md`.
2. Resolve `SOURCE_ROOT`.
3. Detect and read the source README.
4. Read `work/loopforge.config.yaml` for framework defaults.
5. Load core rules and mode rules for the configured mode.
6. Inspect `SOURCE_ROOT` and plan the smallest valid task flow for the selected mode.
7. Use `work/runtime/loopforge_runner.py` with `--source-root` to initialize artifacts, detect the project, attempt verification, and finalize reports.
8. If no runnable verification command can be derived, leave a blocked report instead of waiting for manual config edits.
9. Ensure evaluator-facing outputs exist at `result/output.md`, `result/issues/00-summary.md`, and `logs/trace/`.

## Output Expectations

At minimum, the run should leave behind:

- `result/output.md`
- `result/issues/00-summary.md`
- `logs/trace/run-summary.json`
- `logs/trace/final-report.md`
- `logs/trace/c-to-rust/06-verification-report.md`
The trace report under `logs/trace/` is runtime evidence, not the primary evaluator-facing result.
