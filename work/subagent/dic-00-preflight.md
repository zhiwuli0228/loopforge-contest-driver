---
stage_id: "dic-00"
stage_name: "Preflight"
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
  - "SOURCE_ROOT"
outputs:
  - "logs/trace/consistency/00-preflight-report.md"
  - "logs/trace/consistency/00-preflight-gate.json"
  - "logs/trace/consistency/00-preflight-evidence.json"
success_gate: "READY_FOR_DIC_01"
failure_gate: "BLOCKED_WITH_REPORT"
when_always_finalize: "dic-09"
source_reads_allowed: true
source_writes_allowed: false
advisory_only: false
---

# DIC Stage Package: Preflight

## Objective

Validate required inputs, resolve the authoritative profile, and record the execution defaults that constrain all later stages.

## Orchestrator Boundary

- Pass only declared file paths, profile metadata, and execution defaults.
- Do not inline large file contents from `SOURCE_ROOT`; this stage may inspect source layout directly if needed.
- Record any blocked prerequisite as file-based evidence rather than carrying it in parent context.

## Required Outputs

- `logs/trace/consistency/00-preflight-report.md`: human-readable readiness summary
- `logs/trace/consistency/00-preflight-gate.json`: machine-readable gate result with `stage_id`, `status`, `next_stage`, and `blocked_reason`
- `logs/trace/consistency/00-preflight-evidence.json`: evidence index for resolved profile, input paths, and denied actions

## Gate Rules

- Success: all mandatory inputs resolve, execution defaults remain `analyze-only`, and the profile resolves to `java` with `generic` fallback.
- Failure: emit `BLOCKED_WITH_REPORT`, preserve missing-path or contract mismatch evidence, and point `next_stage` to `dic-09` when `always_finalize=true`.

## Handoff Rules

- Downstream stages may consume only the declared report, gate file, and evidence index.
- Any denial or constraint breach must be reflected in the evidence index instead of parent-side notes.
