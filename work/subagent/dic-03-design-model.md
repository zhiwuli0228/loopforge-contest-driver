---
stage_id: "dic-03"
stage_name: "Gap Modeling"
stage_package: "work/subagent/dic-03-design-model.md"
predecessors:
  - "dic-01"
  - "dic-02"
inputs:
  - "SUBMISSION_ROOT/README.md"
  - "SUBMISSION_ROOT/design-docs/**"
  - "SUBMISSION_ROOT/code/**"
  - "logs/trace/consistency/01-design-intake.md"
  - "logs/trace/consistency/01-acceptance-baseline.json"
  - "logs/trace/consistency/02-source-inventory.md"
  - "logs/trace/consistency/02-source-inventory.json"
  - "logs/trace/consistency/02-adapter-selection.json"
  - "logs/trace/consistency/02-source-inventory-gate.json"
outputs:
  - "logs/trace/consistency/03-gap-model-summary.md"
  - "logs/trace/consistency/03-gap-model.json"
  - "logs/trace/consistency/03-gap-model-gate.json"
  - "logs/trace/consistency/03-gap-model-evidence.json"
success_gate: "READY_FOR_DIC_04"
failure_gate: "SUBMISSION_BLOCKED"
when_always_finalize: "dic-09"
source_reads_allowed: true
source_writes_allowed: false
advisory_only: false
---

# DIC Stage Package: Gap Modeling

## Objective

Model the gaps between the acceptance baseline and the current implementation, preserving evidence from both sides and identifying which differences justify repair.

## Orchestrator Boundary

- Pass only declared acceptance-baseline and inventory artifacts.
- Do not inject uncited repair ideas or implementation assumptions into this stage.

## Required Outputs

- `logs/trace/consistency/03-gap-model-summary.md`: gap-model summary and coverage notes
- `logs/trace/consistency/03-gap-model.json`: canonical gap model with repair-relevant discrepancies
- `logs/trace/consistency/03-gap-model-gate.json`: gate result
- `logs/trace/consistency/03-gap-model-evidence.json`: baseline evidence, implementation evidence, and unavailable-evidence reasons

## Gate Rules

- Success: every repair-targetable gap includes acceptance-baseline evidence and implementation evidence.
- Failure: preserve partial gap fragments and the reason the model cannot satisfy downstream repair planning.

## Handoff Rules

- Downstream consumers use the summary, gap-model JSON, gate file, and evidence index only.
