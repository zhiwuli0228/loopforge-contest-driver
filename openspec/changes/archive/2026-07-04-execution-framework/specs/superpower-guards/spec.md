## ADDED Requirements

### Requirement: Phase-scoped permission guards

The SuperPower guards file SHALL define a mapping from each migration phase to its allowed actions. Each phase entry MUST specify:
- `allowed_tools`: list of `tools.py` subcommands the agent MAY invoke
- `allowed_fs`: filesystem operations permitted (read, write, create, delete) with path patterns
- `forbidden`: explicit list of actions the agent MUST NOT perform in this phase

#### Scenario: Agent uses allowed tool in correct phase
- **WHEN** agent is in the `implement` phase and calls `tools.py run-verification`
- **THEN** the guard configuration SHALL list `run-verification` in `allowed_tools` for the `implement` phase

#### Scenario: Agent attempts forbidden action
- **WHEN** agent is in the `understand` phase and attempts to call `tools.py fault-injection`
- **THEN** the guard configuration SHALL NOT list `fault-injection` in `allowed_tools` for the `understand` phase, and the action is forbidden

### Requirement: Default-deny policy

The SuperPower guards file SHALL operate on a default-deny basis. Any tool or action not explicitly listed in a phase's `allowed_tools` or `allowed_fs` MUST be considered forbidden.

#### Scenario: Unlisted tool is forbidden
- **WHEN** a phase does not list `neutrality-audit` in its `allowed_tools`
- **THEN** the agent MUST NOT invoke `tools.py neutrality-audit` during that phase

### Requirement: Filesystem access patterns

Each phase SHALL declare `allowed_fs` entries with:
- `operation`: one of `read`, `write`, `create`, `delete`
- `path_pattern`: glob pattern for allowed paths (e.g., `work/migration-openspec/**`)

#### Scenario: Write to allowed path
- **WHEN** agent is in the `spec` phase and writes to a spec file
- **THEN** the path SHALL match the `allowed_fs` write pattern for the `spec` phase

#### Scenario: Write to disallowed path
- **WHEN** agent is in the `preflight` phase and attempts to write to `work/runtime/tools.py`
- **THEN** the path SHALL NOT match any `allowed_fs` write pattern for the `preflight` phase

### Requirement: YAML structure validity

The SuperPower guards file SHALL be valid YAML with a top-level `phases` key containing a mapping of phase names to guard definitions.

#### Scenario: Valid YAML parse
- **WHEN** the guards file is loaded with a standard YAML parser
- **THEN** parsing SHALL succeed without errors and produce a dictionary with a `phases` key

### Requirement: No project-specific customization

The SuperPower guards file MUST NOT contain any project-specific paths, names, or configurations. All path patterns SHALL use generic placeholders or relative paths.

#### Scenario: Generic path patterns
- **WHEN** the guards file is inspected
- **THEN** all `path_pattern` values SHALL use relative paths (no absolute paths) and SHALL NOT reference specific project names
