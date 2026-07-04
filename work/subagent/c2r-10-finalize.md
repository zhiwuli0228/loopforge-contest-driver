# c2r-10: Finalize

## Role

Aggregate all migration results into final reports. Write phase — produces result files and verification report.

## Context

You receive:
- `OPENSPEC_CHANGE` — the OpenSpec change name
- `OUTPUT_DIR` — path to the Rust output project
- `WORK_DIR` — path to the work directory
- All prior phase outputs (build results, test results, repair log, gate results)

## SuperPower Rules

Read `work/profiles/superpower/c-to-rust-migration-guards.yaml`, section `finalize`.

- **Allowed tools**: `write-report`
- **Allowed filesystem**: read `**`, write `result/**`, write `issues/**`, write `openspec/changes/*/verification-report.md`
- **Forbidden**: modify source code, modify tools.py, modify profiles

## Steps

1. Call `openspec instructions verification-report --change "OPENSPEC_CHANGE" --json` to get the template
2. Aggregate all phase results:
   - Build results per batch (pass/fail, errors, fixes)
   - Test results per batch (pass/fail, coverage)
   - Repair cycles (diagnostics, fixes applied, retries)
   - Semantic audit outcomes (invariants verified)
   - Quality gate results (unsafe ratio, fault injection, neutrality)
3. Write `verification-report.md` to the OpenSpec change directory
4. Write `result/output.md`:
   - Final Rust project path
   - Build result
   - Test result
   - Unsafe ratio
   - Semantic gate result
   - Test migration summary
5. Write `result/issues/00-summary.md`:
   - Known missing behavior
   - Failed tests (if any)
   - Degraded compatibility (if any)
   - Serious risks
6. Use `python tools.py write-report` if structured data formatting is needed

## Output

- `openspec/changes/<name>/verification-report.md`
- `result/output.md`
- `result/issues/00-summary.md`

## Gate

Return one of:
- `PHASE_PASS` — all reports written, migration complete
- `PHASE_BLOCKED` — critical report generation failure
