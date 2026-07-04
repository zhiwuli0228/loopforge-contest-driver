# c2r-10: Finalize

## Role

Aggregate all migration results into final reports. Write phase — produces `result/output.md`, `result/issues/00-summary.md`, and verification report.

## Context You Receive

- `OPENSPEC_CHANGE` — OpenSpec change name
- `SOURCE_ROOT` — path to C source tree (for reference)
- `OUTPUT_DIR` — path to Rust output project
- `WORK_DIR` — path to work directory
- `PRIOR_OUTPUTS` — all prior phase outputs:
  - Phase 1: inventory path, test function count
  - Phase 5: build results (all batches)
  - Phase 6: test results (all batches), C test coverage report
  - Phase 7: repair log
  - Phase 8: semantic audit report
  - Phase 9: quality gate summary

## SuperPower Rules (this phase only)

- **Allowed tools**: `write-report`
- **Allowed filesystem**: read `**`, write `result/**`, write `issues/**`, write `openspec/changes/*/verification-report.md`
- **Forbidden**: modify source code, modify tools.py, modify profiles

## Steps

### 1. Collect All Results

Gather from prior phases and run a final verification:

```
python WORK_DIR/runtime/tools.py run-verification \
  --project-dir "OUTPUT_DIR" \
  --commands '["cargo build --locked", "cargo test --locked"]'
```

This is the definitive build+test result for the final report.

### 2. Write Verification Report

Try openspec template:
```
openspec instructions verification-report --change "OPENSPEC_CHANGE" --json
```

Write `openspec/changes/OPENSPEC_CHANGE/verification-report.md`:

```
# Verification Report

## Build
- Command: cargo build --locked
- Result: PASS / FAIL
- Warnings: N

## Tests
- Command: cargo test --locked
- Result: PASS (N tests, 0 failures) / FAIL (N tests, M failures)
- C test coverage: X/Y C test functions have Rust equivalents (Z N/A)

## Repair
- Rounds needed: N
- Issues fixed: <summary>
- Remaining issues: <list or "none">

## Semantic Audit
- Invariants verified: X/Y
- Failures: <list or "none">

## Quality Gates
- Unsafe ratio: X.X% (threshold: < 10%)
- Fault injection: M survivors out of N mutations
- Neutrality audit: N hits

## Deliverables
- Rust project: OUTPUT_DIR
- Cargo.toml: OUTPUT_DIR/Cargo.toml
- Source files: N .rs files
- Test files: M test functions
```

### 3. Write result/output.md

```
# C-to-Rust Migration: FlashDB

## Final Status: READY_FOR_EVALUATION / BLOCKED_WITH_REPORT

## Rust Project
- Path: OUTPUT_DIR
- Cargo.toml: OUTPUT_DIR/Cargo.toml

## Build & Test
- cargo build: PASS
- cargo test: PASS (N tests)
- C test coverage: X/Y migrated, Z N/A

## Quality Gates
- Unsafe ratio: X.X%
- Fault injection survivors: M
- Neutrality hits: N

## Semantic Audit
- Invariants verified: X/Y

## Known Issues
See result/issues/00-summary.md
```

### 4. Write result/issues/00-summary.md

```
# Known Issues — FlashDB Rust Migration

## Unresolved
- <issue description> (if any)

## Degraded
- <description of degraded behavior> (if any)

## N/A Tests
- test_legacy_api: deprecated C API, not applicable to Rust
- ...

## Warnings
- <compiler warnings or other non-blocking issues>

## Risks
- <any remaining risks>
```

### 5. Use tools.py for Structured Data

If you have structured data to format:

```
echo '<json_data>' | python WORK_DIR/runtime/tools.py write-report --result-dir "result"
```

Or with explicit data:
```
python WORK_DIR/runtime/tools.py write-report \
  --result-dir "result" \
  --data '{"rust_project": "OUTPUT_DIR", "build": "PASS", ...}'
```

## Output

Three files:
- `openspec/changes/OPENSPEC_CHANGE/verification-report.md`
- `result/output.md`
- `result/issues/00-summary.md`

## Gate

- `PHASE_PASS` — all reports written, final build+test passes
- `PHASE_BLOCKED` — cannot write reports (disk full, permission denied, no results to report)

## Final Return

After writing all reports, return one of:
- `READY_FOR_EVALUATION` — if all gates passed, build+test clean
- `BLOCKED_WITH_REPORT` — if any prior phase was blocked or final build/test fails
