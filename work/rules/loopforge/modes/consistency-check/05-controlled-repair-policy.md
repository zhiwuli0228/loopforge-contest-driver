# Controlled Repair Policy

- Controlled repair starts only after `drift-report.md` and `repair-plan.md` exist.
- Repair must stay within the minimal design-proven scope.
- Prefer the smallest directly relevant source changes first and shared or broad changes only when strictly necessary.
- Every modified file should map back to a recorded drift item.
- If verification remains blocked, stop after recording evidence and do not continue speculative cleanup.
