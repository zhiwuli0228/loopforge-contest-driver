---
name: design-implementation-consistency
description: Repair and verify a standard submission package under SUBMISSION_ROOT while preserving immutable contest baselines.
---

# Design-Implementation Consistency Skill

## Mission

Serve as the authoritative orchestration contract for staged design-implementation consistency repair and verification.

## Mandatory Inputs

Read, in order:

1. `INSTRUCTION.md`
2. `work/loopforge.config.yaml`
3. `work/profiles/examples/default-java-consistency.yaml`
4. `work/profiles/superspec/design-implementation-consistency-stages.yaml`
5. `work/profiles/superpower/design-implementation-consistency-guards.yaml`
6. `work/subagent/design-implementation-consistency-stage-map.yaml`
7. `work/design/README.md`
8. `SUBMISSION_ROOT`
9. [Contract Audit](references/contract-audit.md)
10. [Stage Handoff Contract](references/stage-handoff-contract.md)
11. [Evidence Completeness Contract](references/evidence-completeness-contract.md)
12. [Adapter-Neutral Contract](references/adapter-neutrality-contract.md)
13. [Change 3 Handoff Assumptions](references/change-3-handoff.md)
14. [Core Model Contract](references/core-model-contract.md)

## Profile Resolution

Resolve the active profile in this order:

1. explicit operator override
2. `task.profile` from `work/loopforge.config.yaml`
3. `work/profiles/examples/default-java-consistency.yaml`

If the selected profile does not resolve to adapter `java` or fallback adapter `generic`, stop with `SUBMISSION_BLOCKED`.

## Execution Defaults

- strategy: `repair-and-verify`
- unattended: `true`
- allow_patch: `true`
- allow_code_generation: `true`
- fail_soft: `true`
- always_finalize: `true`
- max_repair_rounds: `1`

Any attempt to confirm a finding or justify a repair target without the required evidence contract is invalid.

## Ordered Workflow

Execute these stages in order and use only file handoff artifacts declared by the stage contract:

1. `dic-00` Submission Preflight
2. `dic-01` Acceptance Baseline Extraction
3. `dic-02` Implementation Inventory
4. `dic-03` Gap Modeling
5. `dic-04` Repair Batch Planning
6. `dic-05` Repair Execution
7. `dic-06` Build Verification
8. `dic-07` Black-Box Verification
9. `dic-08` Targeted Regression Repair
10. `dic-09` Final Verdict Assembly

Resolve each stage ID through `work/subagent/design-implementation-consistency-stage-map.yaml` and dispatch exactly one corresponding stage package under `work/subagent/`.

All cross-stage artifacts must live under `logs/trace/consistency/` unless they are final reports under `result/` or `logs/trace/final-report.md`. The parent orchestrator passes only declared file paths, short summaries, and guard constraints to each stage package. It must not inline full `SUBMISSION_ROOT` context or unrecorded intermediate reasoning across stages.

The authoritative runtime command surface for these staged artifacts is:

- `scan-design` for acceptance-baseline extraction inputs and inventories
- `scan-code` for `02-source-inventory.json` and `02-adapter-selection.json`
- `extract-implementation` for implementation model extraction used by gap modeling
- `build-traceability` for gap-model and repair-batch preparation inputs
- `run-verification` for build verification and black-box verification results
- `write-report` for `09-final-report-input.json`, `logs/trace/final-report.md`, `result/output.md`, and `result/issues/00-summary.md`

## Evidence Rules

A confirmed inconsistency or repair target must include:

- acceptance-baseline evidence
- implementation evidence
- traceability or verification context
- severity, repair scope, or execution-risk context

If either side of the evidence is unavailable, the stage must record an explicit unavailable-evidence reason. Findings missing this contract must stay unconfirmed and must not appear as confirmed drift or justified repair scope.

## Adapter-Neutral Behavior

- Stage IDs, handoff paths, and final verdict semantics are adapter-neutral.
- The Java adapter changes extraction and verification behavior only.
- The Generic fallback preserves the same stage graph, artifact paths, and final report structure.

## Write Scope

Allowed:

- `SUBMISSION_ROOT/code/**`
- `SUBMISSION_ROOT/maven-settings.xml`
- `logs/trace/consistency/**`
- `logs/trace/final-report.md`
- `result/output.md`
- `result/issues/00-summary.md`

Forbidden:

- `SUBMISSION_ROOT/README.md`
- `SUBMISSION_ROOT/design-docs/**`
- `SUBMISSION_ROOT/test-cases/**`
- `work/skills/**`
- `work/profiles/**`
- `work/subagent/**`
- `openspec/**`
- git mutations

## Final Statuses

Return one of:

- `SUBMISSION_PASSED`
- `SUBMISSION_PARTIAL`
- `SUBMISSION_BLOCKED`
- `SUBMISSION_INVALID`

`dic-09` must run when `always_finalize=true`, even if an earlier stage fails, as long as some evidence can be preserved for reporting.
