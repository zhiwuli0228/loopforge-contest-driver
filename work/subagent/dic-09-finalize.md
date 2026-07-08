---
stage_id: "dic-09"
stage_name: "Final Verdict Assembly"
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
  - "SUBMISSION_ROOT/README.md"
  - "logs/trace/consistency/00-submission-layout.json"
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
success_gate: "SUBMISSION_PASSED_OR_PARTIAL"
failure_gate: "SUBMISSION_BLOCKED"
when_always_finalize: "self"
source_reads_allowed: false
source_writes_allowed: false
advisory_only: false
---

# DIC Stage Package: Final Verdict Assembly

## Objective

Assemble the terminal delivery summary from successful and failed upstream stages, preserving evidence paths and clearly distinguishing accepted repairs, remaining gaps, and verification outcomes.

## Orchestrator Boundary

- Pass only the declared stage artifacts, submission-package contract path, execution config path, and guard denial log.
- Do not reconstruct missing stage work in parent context; summarize only what upstream files support.

## Required Outputs

- `logs/trace/consistency/09-finalization-summary.md`: final stage-by-stage delivery summary
- `logs/trace/consistency/09-finalization-gate.json`: terminal gate and delivery verdict
- `logs/trace/consistency/09-finalization-evidence.json`: index of preserved evidence paths and unavailable-artifact reasons
- `logs/trace/consistency/09-verification-results.json`: structured verification command outcomes, classes, and ordering status
- `logs/trace/consistency/09-final-report-input.json`: normalized structured payload consumed by report rendering
- `logs/trace/final-report.md`: audit-ready final report
- `result/output.md`: operator-facing report
- `result/issues/00-summary.md`: issues summary

## Gate Rules

- Success: final outputs reflect accepted repairs, blocked stages, preserved evidence, verification outcomes, and a terminal verdict of `SUBMISSION_PASSED` or `SUBMISSION_PARTIAL`.
- Failure: emit `SUBMISSION_BLOCKED` only when finalization itself cannot produce the required terminal report artifacts or preserved upstream evidence proves the submission is blocked.

## Handoff Rules

- This stage must tolerate partial upstream outputs when `always_finalize=true`.
- Missing downstream artifacts must be reported as unavailable, not fabricated from parent context.
- The final verdict must be one of `SUBMISSION_PASSED`, `SUBMISSION_PARTIAL`, `SUBMISSION_BLOCKED`, or `SUBMISSION_INVALID`.
