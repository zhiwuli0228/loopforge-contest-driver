---
stage_id: "dic-07"
stage_name: "Black-Box Verification"
stage_package: "work/subagent/dic-07-risk-classification.md"
predecessors:
  - "dic-06"
inputs:
  - "SUBMISSION_ROOT/code/**"
  - "SUBMISSION_ROOT/test-cases/**"
  - "SUBMISSION_ROOT/maven-settings.xml"
  - "logs/trace/consistency/06-build-verification.md"
  - "logs/trace/consistency/06-build-verification.json"
  - "logs/trace/consistency/06-build-verification-gate.json"
  - "logs/trace/consistency/06-build-verification-evidence.json"
outputs:
  - "logs/trace/consistency/07-black-box-verification.md"
  - "logs/trace/consistency/07-black-box-verification.json"
  - "logs/trace/consistency/07-black-box-verification-gate.json"
  - "logs/trace/consistency/07-black-box-verification-evidence.json"
success_gate: "READY_FOR_DIC_09"
failure_gate: "READY_FOR_DIC_08"
when_always_finalize: "dic-09"
source_reads_allowed: true
source_writes_allowed: false
advisory_only: false
---

# DIC Stage Package: Black-Box Verification

## Objective

Run package-owned black-box verification after required build prerequisites complete, and preserve command ordering, pass/fail outcomes, and blocked states as evidence.

## Orchestrator Boundary

- Pass only the declared build-verification outputs, black-box paths, and mutable support-asset paths.
- Do not treat black-box verification as independent if required build prerequisites failed; report it as blocked instead.

## Required Outputs

- `logs/trace/consistency/07-black-box-verification.md`: human-readable black-box verification summary
- `logs/trace/consistency/07-black-box-verification.json`: structured black-box outcomes, including blocked-by-prerequisite states
- `logs/trace/consistency/07-black-box-verification-gate.json`: gate result
- `logs/trace/consistency/07-black-box-verification-evidence.json`: command provenance, stdout/stderr summary, and package-contract ordering evidence

## Gate Rules

- Success: required black-box verification runs complete with adequate evidence to determine a final delivery verdict.
- Failure: preserve non-success command results, blocked-prerequisite states, and missing-command evidence so execution can route to targeted retry or finalization.

## Handoff Rules

- `dic-08` and `dic-09` consume only these declared outputs plus earlier build verification outputs they already declare.
