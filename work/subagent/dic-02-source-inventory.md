---
stage_id: "dic-02"
stage_name: "Implementation Inventory"
stage_package: "work/subagent/dic-02-source-inventory.md"
predecessors:
  - "dic-00"
  - "dic-01"
inputs:
  - "SUBMISSION_ROOT/code/**"
  - "SUBMISSION_ROOT/test-cases/**"
  - "SUBMISSION_ROOT/maven-settings.xml"
  - "logs/trace/consistency/00-preflight-report.md"
  - "logs/trace/consistency/00-preflight-gate.json"
  - "logs/trace/consistency/01-design-intake.md"
  - "logs/trace/consistency/01-design-intake-gate.json"
  - "logs/trace/consistency/01-design-intake-evidence.json"
  - "logs/trace/consistency/01-acceptance-baseline.json"
  - "logs/trace/consistency/00-submission-layout.json"
outputs:
  - "logs/trace/consistency/02-source-inventory.md"
  - "logs/trace/consistency/02-source-inventory.json"
  - "logs/trace/consistency/02-adapter-selection.json"
  - "logs/trace/consistency/02-source-inventory-gate.json"
  - "logs/trace/consistency/02-source-inventory-evidence.json"
success_gate: "READY_FOR_DIC_03"
failure_gate: "SUBMISSION_BLOCKED"
when_always_finalize: "dic-09"
source_reads_allowed: true
source_writes_allowed: false
advisory_only: false
---

# DIC Stage Package: Implementation Inventory

## Objective

Inventory repository layout, detectable frameworks, verification entry points, test ownership boundaries, and the selected language adapter with auditable selection evidence.

## Orchestrator Boundary

- Pass only the declared upstream summaries plus the resolved `SUBMISSION_ROOT/code/`, `SUBMISSION_ROOT/test-cases/`, and mutable support-asset paths.
- Do not inline source file contents into parent context; this stage reads the tree directly and writes structured outputs.

## Required Outputs

- `logs/trace/consistency/02-source-inventory.md`: human-readable inventory summary for implementation, black-box, and support-asset scope
- `logs/trace/consistency/02-source-inventory.json`: normalized package inventory including code scope, test-case scope, verification entry points, and mutable support assets
- `logs/trace/consistency/02-adapter-selection.json`: selected adapter, matched signals, and fallback reasons
- `logs/trace/consistency/02-source-inventory-gate.json`: gate result
- `logs/trace/consistency/02-source-inventory-evidence.json`: source and adapter-selection evidence index

## Gate Rules

- Success: adapter selection is explicit, evidence-backed, and downstream gap-model and repair inputs are discoverable.
- Failure: preserve detection attempts, inaccessible paths, and fallback rationale so finalization can distinguish selection failure from later repair failure.

## Handoff Rules

- `dic-03` and `dic-04` consume the inventory summary, machine-readable inventory, adapter selection, and gate/evidence files only.
