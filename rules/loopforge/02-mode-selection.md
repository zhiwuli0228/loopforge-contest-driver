# Mode Selection Rule

## Supported Modes

- `spec-implementation`
- `test-generation`
- `spec-code-drift`
- `clean-code-repair`

## Selection Logic

- If the task asks to implement or complete functionality, use `spec-implementation`.
- If the task asks to generate or extend tests, use `test-generation`.
- If the task asks to compare spec and implementation, use `spec-code-drift`.
- If the task asks to repair code quality without changing scope, use `clean-code-repair`.
- Otherwise default to `spec-implementation`.

## Required Outputs

Write the chosen mode into:

- `.loopforge/task/task.md`
- `.loopforge/state/loop-state.json`
