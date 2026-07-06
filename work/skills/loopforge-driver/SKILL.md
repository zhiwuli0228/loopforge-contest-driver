---
name: loopforge-driver
description: Execute the contest driver using the preloaded work/design/README.md contract plus a read-only SOURCE_ROOT.
---

# LoopForge Driver Skill

Use this skill as the entry point for contest execution.

## Execution Root

- Repository root contains `INSTRUCTION.md`, `work/design/README.md`, and the harness assets
- Framework assets live under `work/`
- Runtime evidence is written under `logs/trace/`
- Evaluator-facing outputs are written under `result/` and `logs/`

## Required Inputs

- `INSTRUCTION.md`
- `SOURCE_ROOT`
- `work/design/README.md`
- `work/loopforge.config.yaml`
- `work/rules/loopforge/core/`
- `work/rules/loopforge/modes/{task.mode}/`
- relevant adapter rules under `work/rules/loopforge/adapters/`
- the configured profile under `work/profiles/`

## OpenSpec Integration

The workflow uses OpenSpec for schema-driven artifact management. Use `work/scripts/openspec.sh` as the entry point (handles global install, local install, and bash fallback).

```bash
# Check available schemas
bash work/scripts/openspec.sh schemas --json

# Check change status
bash work/scripts/openspec.sh status --change <name> --json

# Get artifact instructions
bash work/scripts/openspec.sh instructions <artifact> --change <name> --json
```

The project schema is `c2r-migration` with 6 artifacts: proposal → specs + design → tasks → implement-plan → verification-report.

## SuperPower Guards

Before each migration phase, the agent MUST read the permission boundaries from:

```text
work/profiles/superpower/c-to-rust-migration-guards.yaml
```

This file defines:
- `allowed_tools`: which `tools.py` subcommands are permitted per phase
- `allowed_fs`: filesystem access patterns (read/write/create/delete with glob paths)
- `forbidden`: explicit deny list per phase

Default-deny policy: anything not explicitly allowed is forbidden. The agent MUST check guards before invoking tools or writing files.

## Mission

Drive an unattended contest run using `work/design/README.md` as the task definition and `SOURCE_ROOT` as read-only source input.

## Hard Constraints

- Do not modify static files in the LoopForge root during execution.
- Do not require humans to fill placeholder task name, language, objective, or verification commands.
- Read `work/loopforge.config.yaml` as framework defaults, not as the sole source of task intent.
- Parse the preloaded design README first and record its path and SHA-256 digest.
- If the preloaded design README is invalid, degrade into `BLOCKED_WITH_REPORT` with explicit evidence.
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
6. otherwise block with explicit missing-source evidence

The driver must use only the preloaded design README to infer requirements and constraints before planning work.

## Entrypoints

- Linux: `SOURCE_ROOT="/path/to/source" bash work/scripts/run.sh`
- Linux fallback: `bash work/scripts/run.sh`

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

This is a **two-stage** unattended pipeline. Both stages MUST execute sequentially. Do not stop after Stage 1.

### Stage 1: Data Preparation (Python tools)

Run the data-prep subagent to extract structured source data (no judgment):

```bash
SOURCE_ROOT="/path/to/source" bash work/scripts/run.sh --run
```

This writes:
- `logs/trace/execution-adapter/state/context-package.json` — all absolute paths + analysis summary
- `result/output.md` — status `AGENT_DELEGATION_READY` with next-step instructions
- `logs/trace/run-summary.json` — full gate results

If Stage 1 returns `BLOCKED_WITH_REPORT`, stop and report the blocker. Do not proceed to Stage 2.

### Stage 2: Agent Judgment (Phases 0→10)

After Stage 1 completes, immediately read `work/skills/c-to-rust-migration-v2/SKILL.md` and execute phases 0→10 in strict order.

The SKILL.md orchestrates:
- Phase 0, 2: preflight, design (inline)
- Phase 1, 3, 4: understand, spec, plan (delegated to subagent)
- Phase 5: code generation (subagent per batch) → `work/output/<project>/src/**/*.rs`
- Phase 6: test migration (subagent per batch) → `work/output/<project>/tests/**/*.rs`
- Phase 7: repair loop (subagent) → cargo build + test fixes
- Phase 8: semantic audit (subagent) → invariant tests
- Phase 9: quality gates (subagent) → unsafe, fault-injection, neutrality
- Phase 10: finalize → `result/output.md` with `READY_FOR_EVALUATION`

The context package at `logs/trace/execution-adapter/state/context-package.json` contains all paths needed for phases 0→10.

Each phase returns a gate token: `PHASE_PASS`, `PHASE_BLOCKED`, or `PHASE_DEGRADED`. On `PHASE_BLOCKED`, stop immediately and report.

### Final State

After Stage 2 Phase 10 completes:
- `work/output/<project>/` contains a complete, buildable Rust project
- `result/output.md` status is `READY_FOR_EVALUATION` or `BLOCKED_WITH_REPORT`

## Output Expectations

At minimum, the run should leave behind:

- `result/output.md`
- `result/issues/00-summary.md`
- `logs/trace/run-summary.json`
- `logs/trace/final-report.md`
- `logs/trace/c-to-rust/06-verification-report.md`
- `work/output/<project>/` — generated Rust project with `Cargo.toml`, `src/`, `tests/`

The trace report under `logs/trace/` is runtime evidence, not the primary evaluator-facing result.
