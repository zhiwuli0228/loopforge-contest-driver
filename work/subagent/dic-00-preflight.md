---
stage_id: "dic-00"
stage_name: "Submission Preflight"
stage_package: "work/subagent/dic-00-preflight.md"
predecessors: []
inputs:
  - "INSTRUCTION.md"
  - "work/loopforge.config.yaml"
  - "work/profiles/examples/default-java-consistency.yaml"
  - "work/profiles/superspec/design-implementation-consistency-stages.yaml"
  - "work/profiles/superpower/design-implementation-consistency-guards.yaml"
  - "work/subagent/design-implementation-consistency-stage-map.yaml"
  - "work/design/README.md"
  - "SUBMISSION_ROOT"
outputs:
  - "logs/trace/consistency/00-preflight-report.md"
  - "logs/trace/consistency/00-preflight-gate.json"
  - "logs/trace/consistency/00-preflight-evidence.json"
  - "logs/trace/consistency/00-submission-layout.json"
success_gate: "READY_FOR_DIC_01"
failure_gate: "SUBMISSION_INVALID"
when_always_finalize: "dic-09"
source_reads_allowed: true
source_writes_allowed: false
advisory_only: false
---

# DIC Stage Package: Submission Preflight

## Objective

Validate required submission-package inputs, resolve the authoritative profile, confirm mutable support-asset policy, and record execution defaults for the repair-and-verify workflow.

## Orchestrator Boundary

- Pass only declared file paths, profile metadata, and execution defaults.
- Do not inline large file contents from `SUBMISSION_ROOT`; this stage may inspect package layout directly if needed.
- Record any blocked prerequisite, unsupported mutable asset, or contract mismatch as file-based evidence rather than parent context notes.

## Required Outputs

- `logs/trace/consistency/00-preflight-report.md`: human-readable readiness summary
- `logs/trace/consistency/00-preflight-gate.json`: machine-readable gate result with `stage_id`, `status`, `next_stage`, and `blocked_reason`
- `logs/trace/consistency/00-preflight-evidence.json`: evidence index for resolved profile, input paths, allowed mutable targets, and denied actions
- `logs/trace/consistency/00-submission-layout.json`: resolved package paths for `README.md`, `design-docs/`, `code/`, `test-cases/`, package metadata, and mutable support assets

## Gate Rules

- Success: all mandatory standard-package inputs resolve, execution defaults remain `repair-and-verify`, the profile resolves to `java` with `generic` fallback, and mutable support assets are limited to declared contract paths.
- Failure: emit `SUBMISSION_INVALID`, preserve missing-path or contract mismatch evidence, and point `next_stage` to `dic-09` when `always_finalize=true`.

## Handoff Rules

- Downstream stages may consume only the declared report, gate file, evidence index, and resolved submission-layout artifact.
- Any denial or unsupported mutable target must be reflected in the evidence index instead of parent-side notes.
