## ADDED Requirements

### Requirement: Understand phase is decomposed into three bounded-context sub-stages

The SuperSpec stages YAML at `work/profiles/superspec/c-to-rust-migration-stages.yaml` SHALL replace the single `01-understand` stage with three sub-stages: `01a-inventory`, `01b-capability-analysis`, and `01c-synthesize`. Each sub-stage SHALL have an independent subagent with context ≤ 5K tokens.

#### Scenario: 01a-inventory produces mechanical source inventory

- **WHEN** the orchestrator reaches stage `01a-inventory`
- **THEN** it SHALL invoke `c2r-01a-inventory.md` subagent
- **AND** the subagent SHALL run `tools.py parse-source` to produce `logs/trace/c-to-rust/01a-source-inventory.json`
- **AND** the subagent SHALL NOT read C source files (context ≤ 1K tokens)
- **AND** success gate SHALL be `READY_FOR_CAPABILITY_ANALYSIS`
- **AND** `can_modify_code` SHALL be `false`

#### Scenario: 01b-capability-analysis runs parallel per-module instances

- **WHEN** the orchestrator reads `01a-source-inventory.json` and extracts the module list
- **THEN** it SHALL spawn one `c2r-01b-capability.md` instance per C source module
- **AND** each instance SHALL receive: its assigned C source file path, its header file path, and the inventory JSON path
- **AND** each instance SHALL output `logs/trace/c-to-rust/capabilities/<module>-scenarios.md`
- **AND** all instances SHALL run in parallel (no instance depends on another's output)
- **AND** each instance context SHALL be ≤ 5K tokens (prompt + source + output)
- **AND** success gate SHALL be `READY_FOR_SYNTHESIS`
- **AND** `can_modify_code` SHALL be `false`

#### Scenario: 01b instances are derived from inventory module list

- **WHEN** the inventory contains modules: `fdb_kvdb.c`, `fdb_tsdb.c`, `fdb_utils.c`, `fdb_file.c`, `fdb.c`
- **THEN** the orchestrator SHALL spawn 5 parallel 01b instances
- **AND** each instance SHALL receive the source file path and corresponding header as input
- **AND** test files (`fdb_kvdb_tc.c`, `fdb_tsdb_tc.c`) SHALL be assigned to their corresponding source module's instance

#### Scenario: 01c-synthesize merges per-module scenarios into capability map

- **WHEN** all 01b instances complete
- **THEN** the orchestrator SHALL invoke `c2r-01c-synthesize.md` subagent
- **AND** the subagent SHALL read all `*-scenarios.md` files (summaries only, ~500 tokens each)
- **AND** the subagent SHALL NOT read any C source files
- **AND** the subagent SHALL output `logs/trace/c-to-rust/01c-capability-map.json`
- **AND** the output SHALL contain: capability list with IDs, dependency graph, priority assignments (P0/P1/P2)
- **AND** the subagent SHALL identify cross-module capabilities by matching scenario descriptions across module reports
- **AND** success gate SHALL be `READY_FOR_DESIGN`
- **AND** `can_modify_code` SHALL be `false`

#### Scenario: 01c rejects insufficient capability coverage

- **WHEN** 01c reads the per-module scenarios and finds fewer than 3 total capabilities identified
- **THEN** it SHALL return `PHASE_DEGRADED` with a warning that analysis depth may be insufficient
- **AND** it SHALL still produce the capability map with what was identified
- **AND** the pipeline SHALL NOT be blocked

### Requirement: Stage 01 input/output contracts are updated

Stages 02-design through 04-plan SHALL have their input references updated to consume the new 01c output.

#### Scenario: 02-design consumes capability map

- **WHEN** the orchestrator reaches stage `02-design`
- **THEN** its `input` SHALL include `logs/trace/c-to-rust/01c-capability-map.json`
- **AND** its `input` SHALL include `logs/trace/c-to-rust/01a-source-inventory.json`
- **AND** its `output` SHALL remain `openspec/changes/<name>/design.md`
- **AND** the design subagent SHALL use the capability map to define module-to-capability grouping

#### Scenario: 03-spec consumes capability map

- **WHEN** the orchestrator reaches stage `03-spec`
- **THEN** its `input` SHALL include `logs/trace/c-to-rust/01c-capability-map.json`
- **AND** it SHALL create one spec file per capability ID in the capability map
- **AND** spec files SHALL be at `openspec/changes/<name>/specs/<capability-id>/spec.md`

#### Scenario: 04-plan consumes capability map

- **WHEN** the orchestrator reaches stage `04-plan`
- **THEN** its `input` SHALL include `logs/trace/c-to-rust/01c-capability-map.json`
- **AND** it SHALL define batches where each batch maps to one capability
- **AND** batch dependency order SHALL follow the capability dependency graph
- **AND** each batch SHALL contain both implementation and unit test tasks
