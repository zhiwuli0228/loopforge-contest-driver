---
name: design-implementation-consistency
description: Analyze a preloaded design contract against the implementation under SOURCE_ROOT without mutating business source files.
---

# Design-Implementation Consistency Skill

## Mission

Serve as the authoritative orchestration contract for staged design-implementation consistency checks.

## Mandatory Inputs

Read, in order:

1. `INSTRUCTION.md`
2. `work/loopforge.config.yaml`
3. `work/profiles/examples/default-java-consistency.yaml`
4. `work/profiles/superspec/design-implementation-consistency-stages.yaml`
5. `work/profiles/superpower/design-implementation-consistency-guards.yaml`
6. `work/subagent/design-implementation-consistency-stage-map.yaml`
7. `work/design/README.md`
8. `SOURCE_ROOT`
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

If the selected profile does not resolve to adapter `java` or fallback adapter `generic`, stop with `BLOCKED_WITH_REPORT`.

## Execution Defaults

- strategy: `analyze-only`
- unattended: `true`
- allow_patch: `false`
- allow_code_generation: `false`
- fail_soft: `true`
- always_finalize: `true`

Any attempt to confirm a finding without the required evidence contract is invalid.

## Ordered Workflow

Execute these stages in order and use only file handoff artifacts declared by the stage contract:

1. `dic-00` Preflight
2. `dic-01` Design Intake
3. `dic-02` Source Inventory
4. `dic-03` Design Model Extraction
5. `dic-04` Implementation Model Extraction
6. `dic-05` Traceability Mapping
7. `dic-06` Drift Analysis
8. `dic-07` Risk Classification
9. `dic-08` Repair Planning
10. `dic-09` Finalization

Resolve each stage ID through `work/subagent/design-implementation-consistency-stage-map.yaml` and dispatch exactly one corresponding stage package under `work/subagent/`.

All cross-stage artifacts must live under `logs/trace/consistency/` unless they are final reports under `result/` or `logs/trace/final-report.md`. The parent orchestrator passes only declared file paths, short summaries, and guard constraints to each stage package. It must not inline full `SOURCE_ROOT` context or unrecorded intermediate reasoning across stages.

The authoritative runtime command surface for these staged artifacts is:

- `scan-design` for `01-design-inventory.json` and design-model handoff inputs
- `scan-code` for `02-source-inventory.json` and `02-adapter-selection.json`
- `extract-implementation` for `04-implementation-model.json`
- `build-traceability` for `05-traceability-matrix.json`
- `run-verification` for `09-verification-results.json`
- `write-report` for `09-final-report-input.json`, `logs/trace/final-report.md`, `result/output.md`, and `result/issues/00-summary.md`

## Evidence Rules

A confirmed inconsistency must include:

- design evidence
- implementation evidence
- traceability context
- severity or risk classification

If either side of the evidence is unavailable, the stage must record an explicit unavailable-evidence reason. Findings missing this contract must stay unconfirmed and must not appear as final confirmed drift.

## Adapter-Neutral Behavior

- Stage IDs, outputs, and final statuses are adapter-neutral.
- The Java adapter changes extraction and verification behavior only.
- The Generic fallback preserves the same stage graph, artifact paths, and final report structure.

## Write Scope

Allowed:

- `logs/trace/consistency/**`
- `logs/trace/final-report.md`
- `result/output.md`
- `result/issues/00-summary.md`

Forbidden:

- `SOURCE_ROOT/**`
- `work/skills/**`
- `work/profiles/**`
- `work/subagent/**`
- `openspec/**`
- git mutations

## Final Statuses

Return one of:

- `FINALIZED_NO_FINDINGS`
- `FINALIZED_WITH_FINDINGS`
- `DEGRADED_FINAL_REPORT_READY`
- `BLOCKED_WITH_REPORT`

`dic-09` must run when `always_finalize=true`, even if an earlier stage fails, as long as some evidence can be preserved for reporting.
