# Repair Policy

## Objective

Allow limited correction cycles after verification failures without expanding the original task scope.

## Rules

- Maximum repair rounds: `2`
- Do not broaden requirements during repair.
- Do not modify forbidden files.
- Do not introduce new dependencies.
- Only repair against concrete observed failures.
- Re-run verification after each repair attempt.

## Exit Conditions

- If repair succeeds, continue to finalize.
- If repair budget is exhausted, move to `DEGRADED_DONE`.
