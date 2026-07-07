---
stage_id: "dic-06"
stage_name: "Drift Analysis"
stage_package: "work/subagent/dic-06-drift-analysis.md"
predecessors:
  - "dic-03"
  - "dic-04"
  - "dic-05"
inputs:
  - "logs/trace/consistency/03-design-model.json"
  - "logs/trace/consistency/03-design-model-evidence.json"
  - "logs/trace/consistency/04-implementation-model.json"
  - "logs/trace/consistency/04-implementation-model-evidence.json"
  - "logs/trace/consistency/05-traceability-map.md"
  - "logs/trace/consistency/05-traceability-matrix.json"
  - "logs/trace/consistency/05-traceability-map-gate.json"
  - "logs/trace/consistency/05-traceability-map-evidence.json"
outputs:
  - "logs/trace/consistency/06-drift-analysis.md"
  - "logs/trace/consistency/06-drift-findings.json"
  - "logs/trace/consistency/06-drift-analysis-gate.json"
  - "logs/trace/consistency/06-drift-analysis-evidence.json"
success_gate: "READY_FOR_DIC_07"
failure_gate: "BLOCKED_WITH_REPORT"
when_always_finalize: "dic-09"
source_reads_allowed: false
source_writes_allowed: false
advisory_only: false
---

# DIC Stage Package: Drift Analysis

## Objective

Evaluate mapped and unmapped entities to identify candidate and confirmed design-implementation drift with evidence from both sides.

## Orchestrator Boundary

- Provide only declared model, traceability, and evidence artifacts.
- Do not carry uncited findings in parent context; every candidate must appear in the stage outputs or remain unconfirmed.

## Required Outputs

- `logs/trace/consistency/06-drift-analysis.md`: human-readable drift analysis
- `logs/trace/consistency/06-drift-findings.json`: structured candidate and confirmed findings
- `logs/trace/consistency/06-drift-analysis-gate.json`: gate result with next-step disposition
- `logs/trace/consistency/06-drift-analysis-evidence.json`: evidence index that links findings to design and implementation evidence or explicit unavailable-evidence reasons

## Gate Rules

- Success: confirmed findings meet the evidence contract and unresolved candidates remain explicitly marked.
- Failure: preserve partial findings, broken evidence chains, and analysis blockers so `dic-09` can finalize with degraded but auditable output.

## Handoff Rules

- `dic-07`, `dic-08`, and `dic-09` may consume only the declared drift outputs.
