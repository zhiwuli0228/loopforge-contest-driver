---
stage_id: "dic-05"
stage_name: "Repair Execution"
stage_package: "work/subagent/dic-05-traceability-map.md"
predecessors:
  - "dic-00"
  - "dic-01"
  - "dic-02"
  - "dic-03"
  - "dic-04"
inputs:
  - "SUBMISSION_ROOT/code/**"
  - "SUBMISSION_ROOT/maven-settings.xml"
  - "logs/trace/consistency/00-submission-layout.json"
  - "logs/trace/consistency/01-acceptance-baseline.json"
  - "logs/trace/consistency/02-source-inventory.json"
  - "logs/trace/consistency/03-gap-model.json"
  - "logs/trace/consistency/04-repair-batches.md"
  - "logs/trace/consistency/04-repair-batches.json"
  - "logs/trace/consistency/04-repair-batches-gate.json"
  - "logs/trace/consistency/04-repair-batches-evidence.json"
outputs:
  - "logs/trace/consistency/05-repair-execution.md"
  - "logs/trace/consistency/05-repair-execution.json"
  - "logs/trace/consistency/05-repair-execution-gate.json"
  - "logs/trace/consistency/05-repair-execution-evidence.json"
success_gate: "READY_FOR_DIC_06"
failure_gate: "SUBMISSION_BLOCKED"
when_always_finalize: "dic-09"
source_reads_allowed: true
source_writes_allowed: true
advisory_only: false
---

# DIC Stage Package: Repair Execution

## Objective

Apply bounded repairs within the allowed mutable scope and record every changed target, blocked write, and verification-relevant side effect as evidence.

## Orchestrator Boundary

- Pass only declared batch, baseline, inventory, and mutable-target paths.
- Never imply that this stage may modify `README.md`, `design-docs/`, `test-cases/`, or undeclared support assets.

## Required Outputs

- `logs/trace/consistency/05-repair-execution.md`: narrative summary of applied repairs and blocked writes
- `logs/trace/consistency/05-repair-execution.json`: structured repair result including changed files, skipped files, and remaining known gaps
- `logs/trace/consistency/05-repair-execution-gate.json`: gate result with next-step disposition
- `logs/trace/consistency/05-repair-execution-evidence.json`: evidence index linking file changes or blocked changes to the repair batches that justified them

## Gate Rules

- Success: the stage applies bounded changes only to declared mutable targets and preserves a machine-readable record of what changed.
- Failure: preserve partial changes, denial evidence, and failure reason so downstream verification or finalization can report the exact repair boundary.

## Handoff Rules

- `dic-06` consumes only the declared repair outputs and must not infer hidden patch reasoning from parent context.
