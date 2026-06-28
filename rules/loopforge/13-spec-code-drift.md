# Spec Code Drift Rule

## Objective

Detect mismatches between stated requirements and the current implementation.

## Flow

1. Normalize the input spec.
2. Inspect implementation and tests.
3. Build a lightweight traceability matrix.
4. Record missing behavior, missing tests, or contradictory behavior.
5. Optionally propose focused tests for confirmation.

## Expected Report Content

- requirement-to-code mapping
- requirement-to-test mapping
- drift findings
- confidence level for each finding
