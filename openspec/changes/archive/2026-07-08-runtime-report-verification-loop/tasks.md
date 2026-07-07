## 1. Runtime command surface

- [x] 1.1 Add or normalize the authoritative consistency-check subcommands in `work/runtime/tools.py` for `scan-design`, `scan-code`, `extract-implementation`, `build-traceability`, `run-verification`, and `write-report`.
- [x] 1.2 Implement the missing runtime modules or helpers needed for design scanning, traceability construction, verification status capture, and final report composition under `work/runtime/`.
- [x] 1.3 Remove or isolate C2Rust-specific assumptions in the consistency-check command path so the new runtime flow does not depend on legacy migration semantics.

## 2. Structured artifacts and path alignment

- [x] 2.1 Define the JSON artifact shapes and output paths for design inventory, source inventory, implementation model, traceability map, verification results, and final report input data under `logs/trace/consistency/`.
- [x] 2.2 Align runtime output naming with the stage-package handoff contract so `dic-05` through `dic-09` can consume the emitted artifacts without ad hoc path translation.
- [x] 2.3 Ensure the runtime defaults remain analyze-only by restricting writes to declared trace/result paths and preventing business source modification under `SOURCE_ROOT`.

## 3. Verification and report outputs

- [x] 3.1 Extend verification execution to record explicit statuses for success, failure, timeout, skipped, and unavailable-command outcomes together with preserved evidence.
- [x] 3.2 Implement report generation that renders `result/output.md`, `result/issues/00-summary.md`, and `logs/trace/final-report.md` from structured intermediate artifacts.
- [x] 3.3 Ensure final report rendering can summarize partial pipeline results, coverage gaps, drift findings, and blocked verification states without inventing missing evidence.

## 4. Contract updates and validation

- [x] 4.1 Update any stage, skill, or profile references needed so the runtime command surface and final artifact paths align with the authoritative execution contract.
- [x] 4.2 Add focused tests or smoke coverage for the minimum analyze-only runtime pipeline, including final output generation and issue summary emission.
- [x] 4.3 Verify a partial-failure path where preserved stage evidence and verification blockage still produce a terminal final report without modifying business source files.
