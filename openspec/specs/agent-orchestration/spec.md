## ADDED Requirements

### Requirement: Runner delegates all judgment phases to Agent

The Python runner (`loopforge_runner.py`) SHALL only perform data preparation (resolving SOURCE_ROOT, running tools.py parse-source, running semantic_planning.py) and SHALL delegate all phases that require judgment to the Agent via the V2 SKILL.md orchestrator.

#### Scenario: Runner prepares context and delegates
- **WHEN** loopforge_runner.py is invoked with --run
- **THEN** it SHALL resolve SOURCE_ROOT, run self-check, run tools.py parse-source, run semantic_planning, and output a context package containing all absolute file paths for Agent consumption
- **THEN** it SHALL output instructions for the Agent to read and execute work/skills/c-to-rust-migration-v2/SKILL.md

### Requirement: Runner MUST NOT call hardcoded generation functions

The runner SHALL NOT import or call any of the following functions: `generate_project()`, `_render_function()`, `_render_module()`, `_render_tests()`, `_render_loop_find_then_return()`, `_render_loop_find_then_mutate_return()`, `_map_value_type()`, `_map_param_type()`, `run_repair_loop()`, `evaluate_semantic_equivalence()`, `run_semantic_repair_loop()`.

#### Scenario: Runner has no hardcoded conversion imports
- **WHEN** loopforge_runner.py source is inspected
- **THEN** no import from c2rust_project_generator, c2rust_analysis, c2rust_repair, c2rust_semantic_repair, c2rust_semantic_audit, c2rust_invariant_tests, opencode_repair_provider, or generation_agent_provider SHALL exist

### Requirement: All 10 migration phases execute via subagents

The Agent, following SKILL.md, SHALL execute phases 0 through 10 each by spawning a dedicated subagent from work/subagent/c2r-NN-*.md.

#### Scenario: Complete phase execution
- **WHEN** the Agent executes the V2 skill
- **THEN** Phase 0 SHALL use c2r-00-preflight subagent
- **THEN** Phase 1 SHALL use c2r-01-understand subagent
- **THEN** Phase 2 SHALL use c2r-02-design subagent
- **THEN** Phase 3 SHALL use c2r-03-spec subagent
- **THEN** Phase 4 SHALL use c2r-04-plan subagent
- **THEN** Phase 5 SHALL use c2r-05-implement subagent for each batch
- **THEN** Phase 6 SHALL use c2r-06-test subagent for each batch
- **THEN** Phase 7 SHALL use c2r-07-repair subagent
- **THEN** Phase 8 SHALL use c2r-08-semantic-audit subagent
- **THEN** Phase 9 SHALL use c2r-09-quality-gates subagent
- **THEN** Phase 10 SHALL use c2r-10-finalize subagent

### Requirement: Gate enforcement between phases

The orchestrator SHALL check each subagent's gate result before proceeding to the next phase.

#### Scenario: Phase passes
- **WHEN** a subagent returns PHASE_PASS
- **THEN** the orchestrator SHALL advance to the next phase

#### Scenario: Phase blocked
- **WHEN** a subagent returns PHASE_BLOCKED
- **THEN** the orchestrator SHALL stop the migration and report the blocker

#### Scenario: Phase degraded
- **WHEN** a subagent returns PHASE_DEGRADED
- **THEN** the orchestrator SHALL log the degradation warning and advance to the next phase
