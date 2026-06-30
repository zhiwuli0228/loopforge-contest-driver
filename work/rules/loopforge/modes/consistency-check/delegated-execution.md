# Delegated Execution Rule for Consistency Check

## Purpose

This rule prevents large-context monolithic execution during consistency-check tasks.

The consistency-check workflow must be executed through unattended staged delegated execution.

Subagent execution is mandatory for every stage.

## Mandatory Behavior

The orchestrator must:

1. read `loopforge.config.yaml`
2. load the configured profile
3. load configured SuperSpec and SuperPower files
4. resolve stage definitions
5. execute stages in order
6. write each stage output to `work/logs/trace/consistency/`
7. validate each stage gate
8. continue automatically when the gate allows
9. generate final report without human intervention
10. verify that every stage declares a subagent, output artifact, and `parent_direct_execution_allowed: false`
11. stop with `BLOCKED_WITH_REPORT` when a required subagent is unavailable
12. use file artifact handoff as the only cross-stage memory

## Prohibited Behavior

The orchestrator must not:

1. run the full workflow in a single long context
2. ask the user to approve intermediate plans
3. ask the user to continue to the next stage
4. use conversation memory as the only handoff mechanism
5. return full source-level analysis back into the main context
6. modify static LoopForge assets
7. modify frozen design documents
8. execute Git operations
9. simulate child-stage execution in the parent Build context
10. continue when the required subagent layer is unavailable

## Repair Plan Policy

`04-repair-plan.md` is a machine handoff artifact.

It is not a human approval document.

The patch stage may execute automatically if:

1. the repair plan only modifies allowed paths
2. the repair plan does not touch frozen design documents
3. the repair plan does not touch LoopForge static assets
4. the repair plan stays within the configured scope

## Gate Policy

Allowed gate values:

- `READY_FOR_DESIGN_READ`
- `READY_FOR_IMPLEMENTATION_MAPPING`
- `READY_FOR_DRIFT_ANALYSIS`
- `READY_FOR_REPAIR_PLAN`
- `READY_FOR_PATCH`
- `READY_FOR_VERIFICATION`
- `READY_FOR_FINAL_REPORT`
- `DEGRADED_BUT_READY_FOR_FINAL_REPORT`
- `BLOCKED_WITH_REPORT`
- `FINAL_REPORT_READY`

If a stage is blocked, the orchestrator must write a blocked report and continue to final report generation when possible.

Missing-subagent policy:

```text
BLOCKED_WITH_REPORT
reason: required subagent unavailable
```

## Patch Coding Skill Policy

The `05-patch` stage must use the configured coding skill when the stage declares a `skill` field.

Default coding skill path:

`skills/code-implementation/SKILL.md`

The patch implementation must:

1. load the declared coding skill
2. execute only within the patch stage
3. follow the repair plan
4. obey SuperPower write permissions
5. write `work/logs/trace/consistency/05-patch-summary.md`
6. report the applied coding skill path
7. preserve the stage gate contract

The coding skill may be replaced in future versions without changing stage orchestration.

## Stage Artifact Metadata Contract

Each stage artifact must include:

- `stage_id`
- `executed_by_subagent`
- `parent_direct_execution: false`
- `input_files_read`
- `output_artifact`
- `gate`
- `summary`
- `next_stage`
