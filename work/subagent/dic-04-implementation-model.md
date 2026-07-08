---
stage_id: "dic-04"
stage_name: "Repair Batch Planning"
stage_package: "work/subagent/dic-04-implementation-model.md"
predecessors:
  - "dic-00"
  - "dic-01"
  - "dic-02"
  - "dic-03"
inputs:
  - "logs/trace/consistency/00-submission-layout.json"
  - "logs/trace/consistency/01-acceptance-baseline.json"
  - "logs/trace/consistency/02-source-inventory.md"
  - "logs/trace/consistency/02-source-inventory.json"
  - "logs/trace/consistency/02-adapter-selection.json"
  - "logs/trace/consistency/03-gap-model-summary.md"
  - "logs/trace/consistency/03-gap-model.json"
  - "logs/trace/consistency/03-gap-model-gate.json"
  - "logs/trace/consistency/03-gap-model-evidence.json"
outputs:
  - "logs/trace/consistency/04-repair-batches.md"
  - "logs/trace/consistency/04-repair-batches.json"
  - "logs/trace/consistency/04-repair-batches-gate.json"
  - "logs/trace/consistency/04-repair-batches-evidence.json"
success_gate: "READY_FOR_DIC_05"
failure_gate: "SUBMISSION_BLOCKED"
when_always_finalize: "dic-09"
source_reads_allowed: false
source_writes_allowed: false
advisory_only: false
---

# DIC Stage Package: Repair Batch Planning

## Objective

Turn accepted gaps into bounded repair batches ordered by verification value, file ownership, and mutation risk.

## Orchestrator Boundary

- Pass only declared submission-layout, inventory, and gap-model artifacts.
- Do not pass mutable source text or hidden patch drafts through parent context.

## Required Outputs

- `logs/trace/consistency/04-repair-batches.md`: human-readable repair batch plan
- `logs/trace/consistency/04-repair-batches.json`: structured repair batches with target files, rationale, and verification intent
- `logs/trace/consistency/04-repair-batches-gate.json`: gate result with next-step disposition
- `logs/trace/consistency/04-repair-batches-evidence.json`: evidence index linking each repair batch to specific gaps and baseline constraints

## Gate Rules

- Success: each batch is bounded to declared mutable targets and references sufficient evidence to justify repair execution.
- Failure: preserve partial batches, blocked targets, and scope reasons so the pipeline can stop cleanly or finalize with degraded evidence.

## Handoff Rules

- `dic-05` and `dic-08` may consume only the summary, batch JSON, gate file, and evidence index.
