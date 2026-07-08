---
name: loopforge-driver
description: Execute the repository's default design-implementation consistency workflow against a standard submission package.
---

# LoopForge Driver Skill

Use this skill as the repository-level entry point for unattended `consistency-check` runs.

## Execution Root

- Repository root contains `INSTRUCTION.md`, `work/design/README.md`, and the harness assets
- Framework assets live under `work/`
- Runtime evidence is written under `logs/trace/consistency/` and `logs/trace/final-report.md`
- Evaluator-facing outputs are written under `result/`

## Required Inputs

- `INSTRUCTION.md`
- `SUBMISSION_ROOT`
- `work/loopforge.config.yaml`
- `work/skills/design-implementation-consistency/SKILL.md`
- `work/profiles/examples/default-java-consistency.yaml`
- `work/profiles/superspec/design-implementation-consistency-stages.yaml`
- `work/profiles/superpower/design-implementation-consistency-guards.yaml`
- `work/subagent/design-implementation-consistency-stage-map.yaml`

## OpenSpec Integration

Use `work/scripts/openspec.sh` as the repository entry point for OpenSpec operations.

```bash
bash work/scripts/openspec.sh schemas --json
bash work/scripts/openspec.sh status --change <name> --json
bash work/scripts/openspec.sh instructions <artifact> --change <name> --json
```

The repository default schema is `spec-driven`. Legacy `c2r-migration` artifacts are archived under `work/archived/c-to-rust/` and are not authoritative.

## Mission

Drive an unattended design-implementation consistency run using `SUBMISSION_ROOT/README.md` and `SUBMISSION_ROOT/design-docs/` as the task definition and `SUBMISSION_ROOT/code/` as the business implementation input.

## Hard Constraints

- Do not modify static files in the LoopForge root during execution.
- Do not require humans to fill placeholder task name, language, objective, or verification commands.
- Do not write into immutable submission-package assets; outputs must stay under `logs/trace/consistency/`, `logs/trace/final-report.md`, `result/output.md`, and `result/issues/00-summary.md`.
- Do not resolve the default workflow through archived `c-to-rust` or `c2r` paths.
- Stop after verification and report generation.

## Entrypoints

- Linux: `SUBMISSION_ROOT="/path/to/submission" bash work/scripts/run.sh`
- Linux fallback: `bash work/scripts/run.sh`

## Required Procedure

### Stage 1: Runtime Pipeline

Run the repository driver:

```bash
SUBMISSION_ROOT="/path/to/submission" bash work/scripts/run.sh --run
```

This writes:

- `logs/trace/consistency/01-design-inventory.json`
- `logs/trace/consistency/02-source-inventory.json`
- `logs/trace/consistency/02-adapter-selection.json`
- `logs/trace/consistency/03-design-model.json`
- `logs/trace/consistency/04-implementation-model.json`
- `logs/trace/consistency/05-traceability-matrix.json`
- `logs/trace/consistency/09-verification-results.json`
- `logs/trace/consistency/09-final-report-input.json`
- `logs/trace/final-report.md`
- `result/output.md`
- `result/issues/00-summary.md`
- `logs/trace/run-summary.json`

If the runtime returns `BLOCKED_WITH_REPORT`, stop and report the blocker.

### Stage 2: Staged Consistency Analysis

If deeper stage-by-stage orchestration is required after the runtime pipeline, read `work/skills/design-implementation-consistency/SKILL.md` and execute `dic-00` through `dic-09` in strict order.

Archived `c-to-rust` skills, profiles, guards, stages, subagents, and runtime helpers must not be used to satisfy this default consistency workflow.

## Final State

After the default consistency run completes:

- `result/output.md` reports a consistency final status
- `result/issues/00-summary.md` summarizes findings or degraded verification states
- `logs/trace/final-report.md` preserves the structured audit trail

## Output Expectations

At minimum, the run should leave behind:

- `result/output.md`
- `result/issues/00-summary.md`
- `logs/trace/run-summary.json`
- `logs/trace/final-report.md`
- `logs/trace/consistency/09-verification-results.json`
- `logs/trace/consistency/09-final-report-input.json`

The trace report under `logs/trace/` is runtime evidence, not the primary evaluator-facing result.
