---
stage_id: "dic-08"
stage_name: "Targeted Regression Repair"
stage_package: "work/subagent/dic-08-repair-plan.md"
predecessors:
  - "dic-03"
  - "dic-04"
  - "dic-06"
  - "dic-07"
inputs:
  - "SUBMISSION_ROOT/code/**"
  - "SUBMISSION_ROOT/maven-settings.xml"
  - "logs/trace/consistency/03-gap-model.json"
  - "logs/trace/consistency/04-repair-batches.json"
  - "logs/trace/consistency/06-build-verification.md"
  - "logs/trace/consistency/06-build-verification.json"
  - "logs/trace/consistency/06-build-verification-gate.json"
  - "logs/trace/consistency/06-build-verification-evidence.json"
  - "logs/trace/consistency/07-black-box-verification.md"
  - "logs/trace/consistency/07-black-box-verification.json"
  - "logs/trace/consistency/07-black-box-verification-gate.json"
  - "logs/trace/consistency/07-black-box-verification-evidence.json"
outputs:
  - "logs/trace/consistency/08-retry-repair.md"
  - "logs/trace/consistency/08-retry-repair.json"
  - "logs/trace/consistency/08-retry-repair-gate.json"
  - "logs/trace/consistency/08-retry-repair-evidence.json"
success_gate: "READY_FOR_DIC_06"
failure_gate: "READY_FOR_DIC_09"
when_always_finalize: "dic-09"
source_reads_allowed: true
source_writes_allowed: true
advisory_only: false
---

# DIC Stage Package: Targeted Regression Repair

## Objective

Use failed build or black-box verification evidence to perform bounded retry repair without reopening unrelated source scope.

## Orchestrator Boundary

- Pass only the declared gap model, repair batches, and verification evidence.
- Never broaden retry scope beyond files, interfaces, rules, or support assets implicated by the failed verification evidence.

## Required Outputs

- `logs/trace/consistency/08-retry-repair.md`: narrative summary of retry scope, applied changes, or retry blockage
- `logs/trace/consistency/08-retry-repair.json`: structured retry result including targeted files, originating failures, and remaining blockers
- `logs/trace/consistency/08-retry-repair-gate.json`: gate result that routes either back to `dic-06` or on to `dic-09`
- `logs/trace/consistency/08-retry-repair-evidence.json`: evidence index linking retry actions to the verification failures that justified them

## Gate Rules

- Success: retry scope remains bounded to verification-linked failures and the stage records changed targets or explicit no-op rationale.
- Failure: preserve why retry could not proceed or could not improve the failing verification boundary, then direct finalization to report the blocked state.

## Handoff Rules

- `dic-06` re-entry and `dic-09` finalization consume only the declared retry outputs.
