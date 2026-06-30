# Final Report

## Purpose

The final report is the primary execution handoff artifact. It must be understandable without replaying the entire run.

## Required Sections

Final reports must include:

- final result status
- task context from configuration
- selected mode or workflow context
- configured profile summary
- project detection summary
- contract validation summary and verdict
- mode artifact summary or explicit absence statement
- verification summary or explicit explanation for absence
- gate summary and gate event evidence
- subagent execution evidence with stage-to-subagent mapping
- key artifact references
- artifact location
- boundary statement describing what was and was not modified

## Quality Rules

- Do not claim success without verification evidence.
- Do not omit degraded or blocked states.
- Do not hide missing verification behind generic success language.
- Do not claim staged execution without subagent evidence.
- Prefer concrete execution facts over narrative filler.

## Mode Extension

Mode-specific rules may require extra report sections, but they must extend this core report rather than replace it.

Mode-specific planning and analysis artifacts should be referenced from `work/logs/trace/plan/mode-artifacts.md` when they exist.

For delegated consistency-check runs, the final report must contain:

```md
## Subagent Execution Evidence
```

The section must include one row per stage with:

- stage id
- declared subagent
- artifact path
- gate
- parent direct execution flag
