---
stage_id: "dic-01"
stage_name: "Acceptance Baseline Extraction"
stage_package: "work/subagent/dic-01-design-intake.md"
predecessors:
  - "dic-00"
inputs:
  - "SUBMISSION_ROOT/README.md"
  - "SUBMISSION_ROOT/design-docs/**"
  - "logs/trace/consistency/00-preflight-report.md"
  - "logs/trace/consistency/00-preflight-gate.json"
  - "logs/trace/consistency/00-preflight-evidence.json"
  - "logs/trace/consistency/00-submission-layout.json"
outputs:
  - "logs/trace/consistency/01-design-intake.md"
  - "logs/trace/consistency/01-acceptance-baseline.json"
  - "logs/trace/consistency/01-design-intake-gate.json"
  - "logs/trace/consistency/01-design-intake-evidence.json"
success_gate: "READY_FOR_DIC_02"
failure_gate: "SUBMISSION_BLOCKED"
when_always_finalize: "dic-09"
source_reads_allowed: false
source_writes_allowed: false
advisory_only: false
---

# DIC Stage Package: Acceptance Baseline Extraction

## Objective

Extract the authoritative acceptance baseline from `README.md` and `design-docs/`, including frozen API contracts, error-code rules, verification commands, and modification boundaries.

## Orchestrator Boundary

- Provide the submission-package `README.md`, `design-docs/`, and the preflight artifacts only.
- Do not pass implementation files or inferred source structure into this stage.

## Required Outputs

- `logs/trace/consistency/01-design-intake.md`: concise acceptance-baseline summary, package-level rules, invariants, and open-risk summary
- `logs/trace/consistency/01-acceptance-baseline.json`: machine-readable acceptance baseline derived from `README.md` plus `design-docs/`
- `logs/trace/consistency/01-design-intake-gate.json`: stage gate with `next_stage`
- `logs/trace/consistency/01-design-intake-evidence.json`: evidence index of README sections, design sections, citations, and unavailable-evidence reasons

## Gate Rules

- Success: the stage identifies enough frozen contract structure to guide implementation inventory, gap modeling, and verification planning.
- Failure: preserve the missing or ambiguous baseline evidence and direct finalization to report the blocked boundary.

## Handoff Rules

- Later stages may rely on the acceptance-baseline summary and evidence index, but must not assume unrecorded design or README facts.
