---
stage_id: "dic-09"
stage_name: "Finalization"
stage_package: "work/subagent/dic-09-finalize.md"
predecessors:
  - "dic-00"
  - "dic-01"
  - "dic-02"
  - "dic-03"
  - "dic-04"
  - "dic-05"
  - "dic-06"
  - "dic-07"
  - "dic-08"
inputs:
  - "work/design/README.md"
  - "work/loopforge.config.yaml"
  - "logs/trace/consistency/*.md"
  - "logs/trace/consistency/*.json"
  - "logs/trace/consistency/guard-denials.jsonl"
outputs:
  - "logs/trace/consistency/09-finalization-summary.md"
  - "logs/trace/consistency/09-finalization-gate.json"
  - "logs/trace/consistency/09-finalization-evidence.json"
  - "logs/trace/consistency/09-verification-results.json"
  - "logs/trace/consistency/09-final-report-input.json"
  - "logs/trace/final-report.md"
  - "result/output.md"
  - "result/issues/00-summary.md"
success_gate: "FINALIZED_NO_FINDINGS_OR_WITH_FINDINGS"
failure_gate: "BLOCKED_WITH_REPORT"
when_always_finalize: "self"
source_reads_allowed: false
source_writes_allowed: false
advisory_only: false
---

# DIC Stage Package: Finalization

## Objective

Assemble the terminal audit summary from successful and failed upstream stages, preserving evidence paths and clearly distinguishing confirmed findings from unavailable downstream outputs.

## Orchestrator Boundary

- Pass only the declared stage artifacts, design contract path, execution config path, and guard denial log.
- Do not reconstruct missing stage work in parent context; summarize only what upstream files support.

## Required Outputs

- `logs/trace/consistency/09-finalization-summary.md`: final stage-by-stage summary
- `logs/trace/consistency/09-finalization-gate.json`: terminal gate and final status
- `logs/trace/consistency/09-finalization-evidence.json`: index of preserved evidence paths and unavailable-artifact reasons
- `logs/trace/consistency/09-verification-results.json`: structured verification command outcomes and status
- `logs/trace/consistency/09-final-report-input.json`: normalized structured payload consumed by report rendering
- `logs/trace/final-report.md`: audit-ready final report
- `result/output.md`: operator-facing report
- `result/issues/00-summary.md`: issues summary

## Gate Rules

- Success: final outputs reflect confirmed findings, blocked stages, preserved evidence, and read-only execution posture.
- Failure: emit `BLOCKED_WITH_REPORT` only when finalization itself cannot produce the required terminal report artifacts.

## Handoff Rules

- This stage must tolerate partial upstream outputs when `always_finalize=true`.
- Missing downstream artifacts must be reported as unavailable, not fabricated from parent context.
