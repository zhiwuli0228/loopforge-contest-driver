## MODIFIED Requirements

### Requirement: Phase-scoped permission guards

The SuperPower guards file SHALL define a mapping from each migration phase to its allowed actions. Each phase entry MUST specify:
- `allowed_tools`: list of `tools.py` subcommands the agent MAY invoke
- `allowed_fs`: filesystem operations permitted (read, write, create, delete) with path patterns
- `forbidden`: explicit list of actions the agent MUST NOT perform in this phase
- `subagent`: path to the subagent prompt file that executes this phase

Phases SHALL be: preflight, understand, design, spec, plan, implement, test, repair, semantic-audit, quality-gates, finalize. The implement and test phases MAY have multiple subagent instances (one per batch). All phases EXCEPT implement and test SHALL use a single dedicated subagent.

#### Scenario: Agent uses allowed tool in correct phase
- **WHEN** agent is in the `implement` phase and calls `tools.py run-verification`
- **THEN** the guard configuration SHALL list `run-verification` in `allowed_tools` for the `implement` phase

#### Scenario: Agent attempts forbidden action
- **WHEN** agent is in the `understand` phase and attempts to call `tools.py fault-injection`
- **THEN** the guard configuration SHALL NOT list `fault-injection` in `allowed_tools` for the `understand` phase, and the action is forbidden

#### Scenario: Each phase has a subagent
- **WHEN** the guards file is inspected
- **THEN** each phase entry SHALL include a `subagent` field pointing to the corresponding work/subagent/c2r-NN-*.md file

### Requirement: No Python generation functions in any phase

No phase's allowed_tools SHALL reference or allow execution of Python code generation functions. The implement, test, repair, and semantic-audit phases SHALL use Agent subagents, not Python scripts, for code generation.

#### Scenario: Implement phase uses subagent
- **WHEN** the `implement` phase executes
- **THEN** code generation SHALL be performed by the subagent defined in the phase's `subagent` field
- **THEN** no tools.py subcommand for code generation SHALL exist in the allowed_tools list beyond run-verification
