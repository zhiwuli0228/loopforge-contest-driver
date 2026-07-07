---
stage_id: "dic-07"
stage_name: "Risk Classification"
stage_package: "work/subagent/dic-07-risk-classification.md"
predecessors:
  - "dic-05"
  - "dic-06"
inputs:
  - "logs/trace/consistency/05-traceability-matrix.json"
  - "logs/trace/consistency/05-traceability-map-evidence.json"
  - "logs/trace/consistency/06-drift-analysis.md"
  - "logs/trace/consistency/06-drift-findings.json"
  - "logs/trace/consistency/06-drift-analysis-gate.json"
  - "logs/trace/consistency/06-drift-analysis-evidence.json"
outputs:
  - "logs/trace/consistency/07-risk-classification.md"
  - "logs/trace/consistency/07-risk-classification.json"
  - "logs/trace/consistency/07-risk-classification-gate.json"
  - "logs/trace/consistency/07-risk-classification-evidence.json"
success_gate: "READY_FOR_DIC_08"
failure_gate: "BLOCKED_WITH_REPORT"
when_always_finalize: "dic-09"
source_reads_allowed: false
source_writes_allowed: false
advisory_only: false
---

# DIC Stage Package: Risk Classification

## Objective

Assign severity, execution risk, and remediation priority to confirmed findings without reclassifying evidence-less candidates as confirmed drift.

## Orchestrator Boundary

- Pass only the declared traceability and drift outputs.
- Do not add ad hoc severity judgments outside the produced classification files.

## Required Outputs

- `logs/trace/consistency/07-risk-classification.md`: human-readable severity summary
- `logs/trace/consistency/07-risk-classification.json`: structured risk rollup
- `logs/trace/consistency/07-risk-classification-gate.json`: gate result
- `logs/trace/consistency/07-risk-classification-evidence.json`: evidence index of severity rationale and unresolved-risk reasons

## Gate Rules

- Success: every confirmed finding receives a taxonomy-compatible severity or an explicit reason it cannot yet be classified.
- Failure: preserve partial classification output and reasoning gaps for finalization.

## Handoff Rules

- `dic-08` and `dic-09` consume only these declared outputs plus earlier drift files they already declare.
