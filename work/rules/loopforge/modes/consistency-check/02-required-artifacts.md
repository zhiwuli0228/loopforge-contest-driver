# Required Artifacts

- design summary
- implementation mapping
- traceability matrix
- drift classification report
- repair plan
- test coverage or verification gap summary
- mode artifact index
- final report with references to produced artifacts

Preferred artifact paths under `work/logs/trace/consistency/`:

- `design-summary.md`
- `implementation-mapping.md`
- `traceability-matrix.md`
- `drift-report.md`
- `repair-plan.md`
- `test-coverage-gap.md`

Runner-compatible fallback paths under `work/logs/trace/plan/`:

- `design-summary.md`
- `implementation-mapping.md`
- `traceability-matrix.md`
- `drift-report.md`
- `repair-plan.md`
- `test-coverage-gap.md`
- `mode-artifacts.md`

## Artifact Rules

- `mode-artifacts.md` must index the actual artifact paths that were produced.
- `final-report.md` must reference the artifact directory that was used.
- If repair is not enabled, `repair-plan.md` is still required and must state that repair stopped at planning.
- Every stage artifact must record `executed_by_subagent`.
- Every stage artifact must record `parent_direct_execution: false`.
- Missing subagent execution metadata invalidates the stage artifact.
