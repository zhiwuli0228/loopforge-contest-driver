---
stage_id: "dic-08"
stage_name: "Repair Planning"
stage_package: "work/subagent/dic-08-repair-plan.md"
predecessors:
  - "dic-06"
  - "dic-07"
inputs:
  - "logs/trace/consistency/06-drift-analysis.md"
  - "logs/trace/consistency/06-drift-findings.json"
  - "logs/trace/consistency/06-drift-analysis-gate.json"
  - "logs/trace/consistency/06-drift-analysis-evidence.json"
  - "logs/trace/consistency/07-risk-classification.md"
  - "logs/trace/consistency/07-risk-classification.json"
  - "logs/trace/consistency/07-risk-classification-gate.json"
  - "logs/trace/consistency/07-risk-classification-evidence.json"
outputs:
  - "logs/trace/consistency/08-repair-plan.md"
  - "logs/trace/consistency/08-repair-plan.json"
  - "logs/trace/consistency/08-repair-plan-gate.json"
  - "logs/trace/consistency/08-repair-plan-evidence.json"
success_gate: "READY_FOR_DIC_09"
failure_gate: "READY_FOR_DIC_09"
when_always_finalize: "dic-09"
source_reads_allowed: false
source_writes_allowed: false
advisory_only: true
---

# DIC Stage Package: Repair Planning

## Objective

Produce bounded, advisory-only repair options, candidate patch descriptions, and verification suggestions without mutating business source files.

## Orchestrator Boundary

- Pass only the declared drift and risk artifacts.
- Never grant write access to `SOURCE_ROOT` or imply that this stage may patch business code.

## Required Outputs

- `logs/trace/consistency/08-repair-plan.md`: advisory repair plan
- `logs/trace/consistency/08-repair-plan.json`: structured repair options and verification suggestions
- `logs/trace/consistency/08-repair-plan-gate.json`: gate result; may still route to `dic-09` even if recommendations are partial
- `logs/trace/consistency/08-repair-plan-evidence.json`: evidence index of findings referenced by each recommendation and any unavailable context

## Gate Rules

- Success: the stage emits bounded recommendations consistent with the read-only workflow.
- Failure: preserve why a useful recommendation could not be completed, but still direct execution to `dic-09`.

## Handoff Rules

- `dic-09` consumes only the declared advisory artifacts and must treat them as recommendations, not applied changes.
