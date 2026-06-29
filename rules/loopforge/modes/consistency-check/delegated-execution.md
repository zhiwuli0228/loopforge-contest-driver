# Delegated Execution Rule for Consistency Check

## Purpose

This rule prevents large-context monolithic execution during consistency-check tasks.

The consistency-check workflow must be executed through unattended staged delegated execution.

## Mandatory Behavior

The orchestrator must:

1. read `loopforge.config.yaml`
2. load the configured profile
3. load configured SuperSpec and SuperPower files
4. resolve stage definitions
5. execute stages in order
6. write each stage output to `code/.loopforge/consistency/`
7. validate each stage gate
8. continue automatically when the gate allows
9. generate final report without human intervention

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
