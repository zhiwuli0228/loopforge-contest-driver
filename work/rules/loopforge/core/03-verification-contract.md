# Verification Contract

## Source Of Truth

Verification commands come only from `work/loopforge.config.yaml`.

The runner must read:

- `verification.working_directory`
- `verification.timeout_seconds`
- `verification.commands`

`verification.commands` may be either:

- a legacy list of commands, treated as `default`
- a platform map containing `default`, `linux`, `windows`, or `macos`

## Execution Rules

- Commands must be executed exactly as configured.
- Command order matters and must be preserved.
- The current platform profile should be selected first.
- If the current platform profile is missing, fall back to `default`.
- The runner may stop on the first successful command.
- The runner must not invent alternate commands, frameworks, or build entrypoints.
- The runner must not infer project verification from language detection alone.

## Missing Or Invalid Configuration

If `verification.commands` is missing, empty, or structurally invalid:

- do not guess a test command
- do not silently skip verification
- block with a recorded report state

## Output Requirements

Verification evidence must be written under `code/.loopforge/state/` and should include:

- attempted commands
- detected OS
- selected command profile
- whether fallback to `default` was used
- working directory
- timeout
- command exit status
- captured output tails
- final verification result

## Result Semantics

- `DONE` means configured verification succeeded.
- `BLOCKED_WITH_REPORT` means execution produced a report but verification could not pass or could not run as configured.
- `PARTIAL_DONE` is allowed only when finalization happened before verification was attempted.
