# Stage Handoff Contract

Every stage must declare:

- `stage_id`
- `stage_package`
- ordered predecessor stages
- required input files
- produced output files
- stage summary output
- gate result output
- evidence index output
- success and failure gates

Handoff rules:

- A stage may read `SUBMISSION_ROOT` assets only if the guard for that stage allows the relevant package subpaths.
- A stage may consume predecessor artifacts only when those paths are declared in the superspec.
- A stage may write only its own declared outputs and shared denial evidence.
- The orchestrator may pass only declared file paths, concise summaries, and guard constraints into a stage package.
- The orchestrator must not rely on accumulated full-source context as a substitute for declared handoff artifacts.
- `dic-09` may read all declared stage outputs plus `SUBMISSION_ROOT/README.md`, the resolved submission-layout artifact, and `work/loopforge.config.yaml` to assemble final reporting.

Required artifact roots:

- stage artifacts: `logs/trace/consistency/`
- final report: `logs/trace/final-report.md`
- result outputs: `result/output.md`, `result/issues/00-summary.md`
- stage map: `work/subagent/design-implementation-consistency-stage-map.yaml`
