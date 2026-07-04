## ADDED Requirements

### Requirement: Execute arbitrary build/test commands and return raw results
The system SHALL execute one or more shell commands in a specified project directory and return the raw exit code, stdout, and stderr for each.

#### Scenario: Single command execution
- **WHEN** user runs `python tools.py run-verification --project-dir /path --commands '["cargo build --locked"]'`
- **THEN** system executes the command and outputs JSON with `ok: true`, `data.results[0].exit_code`, `data.results[0].stdout`, `data.results[0].stderr`

#### Scenario: Multiple commands in sequence
- **WHEN** user runs with `--commands '["cargo build", "cargo test"]'`
- **THEN** system executes each command sequentially and returns results array with one entry per command

#### Scenario: Command exits with non-zero code
- **WHEN** a command (e.g., `cargo build`) exits with code 1
- **THEN** system still outputs `ok: true` (tool succeeded) with the non-zero exit_code in data; the system SHALL NOT interpret exit codes as pass/fail

### Requirement: Configurable timeout per command
The system SHALL support a `--timeout` parameter (default 300 seconds) that kills a command if it runs too long.

#### Scenario: Command exceeds timeout
- **WHEN** a command runs longer than the specified timeout
- **THEN** system kills the process and includes `timed_out: true` in that command's result entry

### Requirement: Working directory isolation
The system SHALL execute each command with the specified `--project-dir` as the working directory.

#### Scenario: Relative paths in commands
- **WHEN** user runs `--project-dir /my/project --commands '["cargo build"]'`
- **THEN** system sets cwd to `/my/project` before executing `cargo build`
