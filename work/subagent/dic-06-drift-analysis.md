---
stage_id: "dic-06"
stage_name: "Build Verification"
stage_package: "work/subagent/dic-06-drift-analysis.md"
predecessors:
  - "dic-05"
inputs:
  - "SUBMISSION_ROOT/code/**"
  - "SUBMISSION_ROOT/maven-settings.xml"
  - "logs/trace/consistency/05-repair-execution.md"
  - "logs/trace/consistency/05-repair-execution.json"
  - "logs/trace/consistency/05-repair-execution-gate.json"
  - "logs/trace/consistency/05-repair-execution-evidence.json"
outputs:
  - "logs/trace/consistency/06-build-verification.md"
  - "logs/trace/consistency/06-build-verification.json"
  - "logs/trace/consistency/06-build-verification-gate.json"
  - "logs/trace/consistency/06-build-verification-evidence.json"
success_gate: "READY_FOR_DIC_07"
failure_gate: "READY_FOR_DIC_08"
when_always_finalize: "dic-09"
source_reads_allowed: true
source_writes_allowed: false
advisory_only: false
---

# DIC Stage Package: Build Verification

## Objective

Run project-owned verification and installation commands required before black-box tests, and preserve their ordered outcomes as structured evidence.

## Orchestrator Boundary

- Provide only the declared repair outputs, source paths, and mutable support-asset paths.
- Do not reinterpret failed verification outside the stage outputs; every failure, skip, or unavailable command must be recorded explicitly.

## Required Outputs

- `logs/trace/consistency/06-build-verification.md`: human-readable build and project-test verification summary
- `logs/trace/consistency/06-build-verification.json`: structured verification outcomes, including command class and prerequisite status
- `logs/trace/consistency/06-build-verification-gate.json`: gate result with next-step disposition
- `logs/trace/consistency/06-build-verification-evidence.json`: command provenance, stdout/stderr summary, and blocked-prerequisite evidence

## Gate Rules

- Success: required build and project-owned verification commands complete with evidence adequate for black-box progression.
- Failure: preserve command outcomes, partial outputs, and prerequisite failure evidence so execution can route to targeted retry or finalization.

## Handoff Rules

- `dic-07`, `dic-08`, and `dic-09` may consume only the declared verification outputs.
