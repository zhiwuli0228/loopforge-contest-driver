# c2r-09: Quality Gates

## Role

Run quality gate checks: unsafe ratio, fault injection, neutrality audit. Read-only phase — no writes allowed.

## Context

You receive:
- `OUTPUT_DIR` — path to the Rust output project
- `WORK_DIR` — path to the work directory
- Paths to files to audit for neutrality

## SuperPower Rules

Read `work/profiles/superpower/c-to-rust-migration-guards.yaml`, section `quality-gates`.

- **Allowed tools**: `check-unsafe`, `fault-injection`, `neutrality-audit`
- **Allowed filesystem**: read `**` only
- **Forbidden**: any write operations, any source modification

## Steps

1. **Unsafe ratio check**:
   ```
   python tools.py check-unsafe --project-dir OUTPUT_DIR
   ```
   Record the unsafe ratio. Threshold: < 10%.

2. **Fault injection**:
   ```
   python tools.py fault-injection --trace-dir WORK_DIR
   ```
   Record pass/fail results.

3. **Neutrality audit**:
   ```
   python tools.py neutrality-audit --paths '["OUTPUT_DIR/src", "OUTPUT_DIR/tests"]' --forbidden-terms '["project-specific-term", "hardcoded-path"]'
   ```
   Record any hits. Zero hits expected for a generic migration.

4. Aggregate all gate results into a summary.

## Output

A quality gate summary:
- Unsafe ratio: X% (pass if < 10%)
- Fault injection: N passed, M failed
- Neutrality audit: N hits (pass if 0)
- Overall gate status

## Gate

Return one of:
- `PHASE_PASS` — all quality gates passed
- `PHASE_BLOCKED` — unsafe ratio >= 10% or critical neutrality violation
- `PHASE_DEGRADED` — some non-critical gate issues (e.g., fault injection partial failure)
