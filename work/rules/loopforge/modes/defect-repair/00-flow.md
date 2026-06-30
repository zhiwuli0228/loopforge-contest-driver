# Defect Repair Flow

## Applies To

- failing tests
- reproducible defects
- regressions in existing behavior
- production-style bug fixes where minimal scope matters

## Flow

`FAILURE_DIAGNOSIS -> ROOT_CAUSE_ANALYSIS -> MINIMAL_PATCH_PLAN -> CODE_GENERATE -> REGRESSION_VERIFY -> FINAL_REPORT`

## Phase Outcomes

- `FAILURE_DIAGNOSIS`: restate the defect in observable terms
- `ROOT_CAUSE_ANALYSIS`: identify the smallest convincing cause
- `MINIMAL_PATCH_PLAN`: choose the narrowest patch that addresses the cause
- `CODE_GENERATE`: implement the patch under `code/`
- `REGRESSION_VERIFY`: run configured verification to check for breakage
- `FINAL_REPORT`: record the fix, evidence, and residual risk
