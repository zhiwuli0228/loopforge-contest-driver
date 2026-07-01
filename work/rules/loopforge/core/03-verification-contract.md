# Verification Contract

## Source Of Truth

Verification intent comes from `work/design/README.md` first and framework defaults second.

The runner may read:

- `verification.working_directory`
- `verification.timeout_seconds`
- `verification.commands`

Framework verification commands remain optional defaults. They must not become a required manual task-input surface.

## Execution Rules

- Commands must be executed exactly as selected.
- Command order matters and must be preserved.
- The current platform profile should be selected first.
- If the current platform profile is missing, fall back to `default`.
- The runner may stop on the first successful command.
- The runner must not invent alternate commands when explicit commands already exist.
- If no runnable verification command can be derived, the run must degrade into `BLOCKED_WITH_REPORT`.

## Missing Or Invalid Configuration

If no runnable verification command can be derived:

- do not silently skip verification
- do not wait for humans to fill configuration
- block with a recorded report state

## Output Requirements

Verification evidence must be written under `work/logs/trace/state/` and should include:

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
