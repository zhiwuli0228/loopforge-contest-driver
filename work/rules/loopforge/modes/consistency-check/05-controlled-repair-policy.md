# Controlled Repair Policy

- Controlled repair starts only after `drift-report.md` and `repair-plan.md` exist.
- Repair must stay within the minimal design-proven scope.
- For Java Maven workspaces, prefer target module changes first and shared common module changes only when strictly necessary.
- Every modified file should map back to a recorded drift item.
- If verification remains blocked, stop after recording evidence and do not continue speculative cleanup.
