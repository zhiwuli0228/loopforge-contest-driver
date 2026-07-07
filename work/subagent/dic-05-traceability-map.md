---
stage_id: "dic-05"
stage_name: "Traceability Mapping"
stage_package: "work/subagent/dic-05-traceability-map.md"
predecessors:
  - "dic-03"
  - "dic-04"
inputs:
  - "logs/trace/consistency/03-design-model-summary.md"
  - "logs/trace/consistency/03-design-model.json"
  - "logs/trace/consistency/03-design-model-gate.json"
  - "logs/trace/consistency/03-design-model-evidence.json"
  - "logs/trace/consistency/04-implementation-model-summary.md"
  - "logs/trace/consistency/04-implementation-model.json"
  - "logs/trace/consistency/04-implementation-model-gate.json"
  - "logs/trace/consistency/04-implementation-model-evidence.json"
outputs:
  - "logs/trace/consistency/05-traceability-map.md"
  - "logs/trace/consistency/05-traceability-matrix.json"
  - "logs/trace/consistency/05-traceability-map-gate.json"
  - "logs/trace/consistency/05-traceability-map-evidence.json"
success_gate: "READY_FOR_DIC_06"
failure_gate: "BLOCKED_WITH_REPORT"
when_always_finalize: "dic-09"
source_reads_allowed: false
source_writes_allowed: false
advisory_only: false
---

# DIC Stage Package: Traceability Mapping

## Objective

Link canonical design objects to canonical implementation objects and record matched, missing, and ambiguous coverage states.

## Orchestrator Boundary

- Pass model artifacts and evidence indexes only.
- Do not provide hidden similarity reasoning outside the produced matrix and summary files.

## Required Outputs

- `logs/trace/consistency/05-traceability-map.md`: narrative traceability summary
- `logs/trace/consistency/05-traceability-matrix.json`: machine-readable traceability matrix
- `logs/trace/consistency/05-traceability-map-gate.json`: gate result
- `logs/trace/consistency/05-traceability-map-evidence.json`: traceability evidence index and unresolved-link reasons

## Gate Rules

- Success: every confirmed link or gap is represented in the matrix with evidence context.
- Failure: preserve partial mapping evidence and ambiguous-link reasons for downstream reporting.

## Handoff Rules

- Downstream stages must rely on the traceability summary, matrix, gate file, and evidence index rather than parent-side comparison notes.
