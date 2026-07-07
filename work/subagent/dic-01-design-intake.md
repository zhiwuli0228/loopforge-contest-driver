---
stage_id: "dic-01"
stage_name: "Design Intake"
stage_package: "work/subagent/dic-01-design-intake.md"
predecessors:
  - "dic-00"
inputs:
  - "work/design/README.md"
  - "logs/trace/consistency/00-preflight-report.md"
  - "logs/trace/consistency/00-preflight-gate.json"
  - "logs/trace/consistency/00-preflight-evidence.json"
outputs:
  - "logs/trace/consistency/01-design-intake.md"
  - "logs/trace/consistency/01-design-inventory.json"
  - "logs/trace/consistency/01-design-intake-gate.json"
  - "logs/trace/consistency/01-design-intake-evidence.json"
success_gate: "READY_FOR_DIC_02"
failure_gate: "BLOCKED_WITH_REPORT"
when_always_finalize: "dic-09"
source_reads_allowed: false
source_writes_allowed: false
advisory_only: false
---

# DIC Stage Package: Design Intake

## Objective

Summarize the authoritative design contract, identify the review boundary, and extract the explicit design evidence that later model stages must preserve.

## Orchestrator Boundary

- Provide the design contract path plus the preflight artifacts only.
- Do not pass implementation files or inferred source structure into this stage.

## Required Outputs

- `logs/trace/consistency/01-design-intake.md`: concise design scope, invariants, and open-risk summary
- `logs/trace/consistency/01-design-inventory.json`: machine-readable design file inventory for runtime handoff
- `logs/trace/consistency/01-design-intake-gate.json`: stage gate with `next_stage`
- `logs/trace/consistency/01-design-intake-evidence.json`: evidence index of design sections, citations, and unavailable-evidence reasons

## Gate Rules

- Success: the stage identifies enough design structure to guide source inventory and model extraction.
- Failure: preserve the missing or ambiguous design evidence and direct finalization to report the blocked boundary.

## Handoff Rules

- Later stages may rely on the design intake summary and evidence index, but must not assume unrecorded design facts.
