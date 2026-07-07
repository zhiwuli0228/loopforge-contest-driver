---
stage_id: "dic-04"
stage_name: "Implementation Model Extraction"
stage_package: "work/subagent/dic-04-implementation-model.md"
predecessors:
  - "dic-02"
  - "dic-03"
inputs:
  - "SOURCE_ROOT"
  - "logs/trace/consistency/02-source-inventory.md"
  - "logs/trace/consistency/02-source-inventory.json"
  - "logs/trace/consistency/02-adapter-selection.json"
  - "logs/trace/consistency/02-source-inventory-gate.json"
  - "logs/trace/consistency/02-source-inventory-evidence.json"
  - "logs/trace/consistency/03-design-model-summary.md"
  - "logs/trace/consistency/03-design-model.json"
  - "logs/trace/consistency/03-design-model-gate.json"
outputs:
  - "logs/trace/consistency/04-implementation-model-summary.md"
  - "logs/trace/consistency/04-implementation-model.json"
  - "logs/trace/consistency/04-implementation-model-gate.json"
  - "logs/trace/consistency/04-implementation-model-evidence.json"
success_gate: "READY_FOR_DIC_05"
failure_gate: "BLOCKED_WITH_REPORT"
when_always_finalize: "dic-09"
source_reads_allowed: true
source_writes_allowed: false
advisory_only: false
---

# DIC Stage Package: Implementation Model Extraction

## Objective

Run the selected adapter against `SOURCE_ROOT` and normalize implementation structures into the canonical implementation model while preserving extraction evidence.

## Orchestrator Boundary

- Pass only declared inventory, adapter-selection, and design-model artifacts plus the `SOURCE_ROOT` path.
- Do not move raw source text through parent context; keep source inspection and evidence capture inside this stage.

## Required Outputs

- `logs/trace/consistency/04-implementation-model-summary.md`: extraction summary and coverage notes
- `logs/trace/consistency/04-implementation-model.json`: canonical implementation model
- `logs/trace/consistency/04-implementation-model-gate.json`: gate result with next-step disposition
- `logs/trace/consistency/04-implementation-model-evidence.json`: adapter provenance, source evidence, and denied-action references

## Gate Rules

- Success: a valid implementation model is produced using the declared adapter contract.
- Failure: preserve partial extraction output, adapter provenance, and failure reason so the pipeline can stop cleanly or finalize with degraded evidence.

## Handoff Rules

- `dic-05` and later stages may consume only the summary, model JSON, gate file, and evidence index.
