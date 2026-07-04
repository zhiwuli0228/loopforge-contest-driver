## ADDED Requirements

### Requirement: SKILL.md defines the 10-phase migration sequence

SKILL.md SHALL define a fixed linear sequence of 10 migration phases (preflight through finalize) that the agent follows in order without skipping.

#### Scenario: Agent follows phases in order
- **WHEN** agent reads SKILL.md and begins migration
- **THEN** agent executes phases 0→1→2→3→4→5→6→7→8→9→10 in sequence, never skipping or reordering

#### Scenario: Phase numbering matches V2 blueprint
- **WHEN** agent reads the phase list in SKILL.md
- **THEN** phases are numbered 0-10 matching the V2 design blueprint (0=preflight, 1=understand, 2=design, 3=spec, 4=plan, 5=implement, 6=test, 7=repair, 8=semantic-audit, 9=quality-gates, 10=finalize)

### Requirement: SKILL.md delegates each phase to a subagent

SKILL.md SHALL spawn a subagent for each phase, passing the subagent prompt file path, phase-specific context, and the OpenSpec change name.

#### Scenario: Subagent delegation with bounded context
- **WHEN** SKILL.md begins a phase
- **THEN** it spawns a subagent with: (1) the subagent prompt file path, (2) SuperPower rules for that phase, (3) the OpenSpec change name, and (4) any phase-specific data from prior phases

#### Scenario: SKILL.md does not embed phase logic
- **WHEN** agent reads SKILL.md
- **THEN** SKILL.md contains only sequencing logic and delegation instructions, not the detailed phase implementation (that lives in subagent files)

### Requirement: SKILL.md checks phase output gates before proceeding

SKILL.md SHALL check each subagent's return status (PHASE_PASS, PHASE_BLOCKED, PHASE_DEGRADED) before advancing to the next phase.

#### Scenario: Phase passes — proceed to next
- **WHEN** subagent returns `PHASE_PASS`
- **THEN** SKILL.md advances to the next phase

#### Scenario: Phase blocked — abort migration
- **WHEN** subagent returns `PHASE_BLOCKED`
- **THEN** SKILL.md stops the migration and reports the blocker

#### Scenario: Phase degraded — proceed with warning
- **WHEN** subagent returns `PHASE_DEGRADED`
- **THEN** SKILL.md logs the degradation and continues to the next phase

### Requirement: SKILL.md is generic with zero project-specific hardcoding

SKILL.md SHALL NOT contain any project-specific paths, file names, or hardcoded values. All paths and configuration SHALL be derived from the OpenSpec change directory and tools.py CLI.

#### Scenario: No hardcoded paths
- **WHEN** SKILL.md is inspected for hardcoded paths
- **THEN** it contains no absolute paths, no project-specific file references, and no hardcoded directory structures beyond the generic `work/` convention

### Requirement: SKILL.md references tools.py commands for data retrieval

SKILL.md SHALL instruct subagents to use `python tools.py <command>` for all data retrieval, never directly parsing source or running cargo commands.

#### Scenario: Subagent uses tools.py for source parsing
- **WHEN** a subagent needs source code analysis
- **THEN** it calls `python tools.py parse-source` rather than directly reading C files

#### Scenario: Subagent uses tools.py for verification
- **WHEN** a subagent needs to run cargo build/test
- **THEN** it calls `python tools.py run-verification` rather than directly invoking cargo

### Requirement: SKILL.md consumes OpenSpec artifact instructions

SKILL.md SHALL use `openspec instructions <artifact> --change <name> --json` to get artifact templates, dependency context, and output paths for each phase.

#### Schema integration
- **WHEN** SKILL.md begins a phase that produces an OpenSpec artifact
- **THEN** it calls `openspec instructions` to retrieve the template and instructions, then passes them to the subagent
