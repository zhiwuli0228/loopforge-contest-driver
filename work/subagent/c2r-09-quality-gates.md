# c2r-09: Quality Gates

## Role

Run three quality gate checks: unsafe ratio, fault injection, and neutrality audit. Read-only phase — no files written.

## Context You Receive

- `OUTPUT_DIR` — path to Rust output project
- `WORK_DIR` — path to work directory

## SuperPower Rules (this phase only)

- **Allowed tools**: `check-unsafe`, `fault-injection`, `neutrality-audit`
- **Allowed filesystem**: read `**` only
- **Forbidden**: any write operations, any source modification

## Steps

### 1. Unsafe Ratio Check

```
python WORK_DIR/runtime/tools.py check-unsafe --project-dir "OUTPUT_DIR"
```

This returns:
- `total_lines`: total lines of Rust code
- `unsafe_lines`: lines inside `unsafe { }` blocks
- `ratio`: unsafe_lines / total_lines as a percentage

**Threshold**: < 10% (from `work/design/README.md` requirement)

Record: total lines, unsafe lines, ratio, pass/fail.

### 2. Fault Injection

```
python WORK_DIR/runtime/tools.py fault-injection \
  --project-dir "OUTPUT_DIR" \
  --trace-dir "WORK_DIR/../../logs/trace"
```

This runs mutation testing:
- Injects faults into the code (e.g., flips comparisons, changes operators)
- Runs tests against mutated code
- Reports which mutations "survived" (tests didn't catch them)

Record:
- `mutation_count`: total mutations applied
- `survivor_count`: mutations not caught by tests
- List of survivors (which file, which mutation)

Interpretation:
- Survivor count = 0: tests are thorough
- Survivors > 0: test coverage gaps exist

### 3. Neutrality Audit

```
python WORK_DIR/runtime/tools.py neutrality-audit \
  --paths '["OUTPUT_DIR/src/**/*.rs", "OUTPUT_DIR/tests/**/*.rs"]' \
  --forbidden-terms '["flashdb", "FlashDB", "ARM", "STM32", "FAL", "RT-Thread", "FreeRTOS", "E://", "C://", "/home/", "/Users/", "contest", "loopforge", "specific-platform"]'
```

This scans all Rust source and test files for:
- Project-specific names that should be generic
- Hardcoded paths
- Platform-specific references

Record:
- `files_scanned`: number of files checked
- `hits`: list of forbidden term occurrences with file/line/context
- `finding_count`: total hits found

**Expectation**: 0 hits for a generic migration.

### 4. Aggregate Results

Compile into a gate summary:

```
Quality Gate Summary
====================
1. Unsafe Ratio: X.X%  [PASS if < 10%] [FAIL if >= 10%]
   Total lines: N, Unsafe lines: M

2. Fault Injection: N mutations, M survivors  [PASS if 0] [DEGRADED if > 0]
   Survivors: <list or "none">

3. Neutrality Audit: N hits  [PASS if 0] [FAIL if > 0]
   Hits: <list or "none">

Overall: PASS / DEGRADED / BLOCKED
```

## Output

Gate summary (in your return message). No files written.

## Gate

- `PHASE_PASS` — all three gates pass: unsafe < 10%, 0 survivors, 0 neutrality hits
- `PHASE_BLOCKED` — unsafe ratio >= 10% (violates hard requirement) or neutrality hits indicate project-specific code in output
- `PHASE_DEGRADED` — some survivors in fault injection (test gaps, non-critical) or borderline unsafe ratio (5-10%)
