---
stage_id: "dic-03"
stage_name: "Design Model Extraction"
stage_package: "work/subagent/dic-03-design-model.md"
predecessors:
  - "dic-01"
  - "dic-02"
inputs:
  - "work/design/README.md"
  - "logs/trace/consistency/01-design-intake.md"
  - "logs/trace/consistency/01-design-intake-gate.json"
  - "logs/trace/consistency/01-design-intake-evidence.json"
  - "logs/trace/consistency/02-source-inventory.md"
  - "logs/trace/consistency/02-source-inventory.json"
  - "logs/trace/consistency/02-adapter-selection.json"
  - "logs/trace/consistency/02-source-inventory-gate.json"
outputs:
  - "logs/trace/consistency/03-design-model-summary.md"
  - "logs/trace/consistency/03-design-model.json"
  - "logs/trace/consistency/03-design-model-gate.json"
  - "logs/trace/consistency/03-design-model-evidence.json"
success_gate: "READY_FOR_DIC_04"
failure_gate: "BLOCKED_WITH_REPORT"
when_always_finalize: "dic-09"
source_reads_allowed: false
source_writes_allowed: false
advisory_only: false
---

# DIC Stage Package: Design Model Extraction

## Objective

Normalize design entities, constraints, and evidence into the canonical design model shared by later traceability and drift stages.

## Orchestrator Boundary

- Pass only declared design intake and inventory artifacts.
- Do not inject unstructured implementation assumptions into this stage.

## Required Outputs

- `logs/trace/consistency/03-design-model-summary.md`: extraction summary and coverage notes
- `logs/trace/consistency/03-design-model.json`: canonical design model
- `logs/trace/consistency/03-design-model-gate.json`: gate result
- `logs/trace/consistency/03-design-model-evidence.json`: design evidence index and unavailable-evidence reasons

## Gate Rules

- Success: the design model is structurally valid and every extracted object references design evidence.
- Failure: preserve partial model fragments and the reason the model cannot satisfy downstream traceability.

## Handoff Rules

- Downstream consumers use the summary, model JSON, gate file, and evidence index only.
