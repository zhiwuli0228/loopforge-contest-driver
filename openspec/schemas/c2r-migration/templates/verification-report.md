# Verification Report

## Build Results

| Batch | Capability | Build Status | Errors | Warnings | Fixes Applied |
|-------|-----------|-------------|--------|----------|---------------|
| 1 | [capability-id] | PASS / FAIL | [count] | [count] | [summary or "—"] |
| 2 | [capability-id] | PASS / FAIL | [count] | [count] | [summary] |

[Every batch from implement-plan.md MUST appear in this table.]

## Test Results

| Batch | Capability | Test Status | Passed | Failed | Total | Notes |
|-------|-----------|------------|--------|--------|-------|-------|
| 1 | [capability-id] | PASS / FAIL | [N] | [M] | [T] | [notes or "—"] |
| 2 | [capability-id] | PASS / FAIL | [N] | [M] | [T] | [notes] |

## Repair Log

### Batch [N]: [Capability Name]

[If no failures occurred: "No repairs needed — all build and test gates passed on first attempt."]

[If failures occurred, use this format for each repair round:]

**Round 1:**
- Error: [error message or description]
- Diagnosis: [root cause]
- Fix: [what was changed, file:line]
- Retry result: PASS / FAIL

**Round 2:**
- ...

## Semantic Audit

| Invariant ID | Capability | Test Name | Status | Notes |
|-------------|-----------|-----------|--------|-------|
| INV-[id]-001 | [capability-id] | [test_name] | PASS / FAIL | [notes] |

[If no semantic audit was performed: "Semantic audit skipped — [reason]"]

## Quality Gates

- **Unsafe ratio**: [X.X%] ([N] unsafe lines / [M] total lines) — Threshold: < 10%
- **Fault injection**: [N] mutations injected, [M] survivors — Threshold: 0 survivors
- **Neutrality audit**: [N] files scanned, [M] hits found — Threshold: 0 hits

| Gate | Result | Threshold | Status |
|------|--------|-----------|--------|
| Unsafe ratio | [value] | < 10% | PASS / FAIL |
| Fault injection | [value] | 0 survivors | PASS / FAIL |
| Neutrality | [value] | 0 hits | PASS / FAIL |

## Capability Coverage Summary

[Total] capabilities in migration plan:
- [N] fully implemented and tested (PASS)
- [M] implemented but tests failing (DEGRADED)
- [K] not implemented (MISSING)

| Capability ID | Priority | Implementation | Unit Tests | Integration Tests | Status |
|--------------|----------|---------------|------------|-------------------|--------|
| [id] | [P0/P1/P2] | DONE / PARTIAL / MISSING | DONE / PARTIAL / MISSING | DONE / N/A | PASS / FAIL / DEGRADED |

## Final Assessment

[Overall assessment: Did the migration succeed? Are all P0 and P1 capabilities implemented and tested? What remains for follow-up work?]

- **Build**: [PASS / FAIL] — [summary]
- **Tests**: [PASS / FAIL] — [N]/[M] tests passing
- **Semantic audit**: [PASS / FAIL / SKIPPED]
- **Quality gates**: [PASS / FAIL]
- **Overall**: [PASS / FAIL / DEGRADED]

Remaining issues:
1. [Issue description — file, function, what's wrong, recommended fix]
2. [...]
