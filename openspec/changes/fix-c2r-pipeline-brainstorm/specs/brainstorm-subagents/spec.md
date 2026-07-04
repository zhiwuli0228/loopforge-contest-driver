## ADDED Requirements

### Requirement: 01a-inventory subagent performs mechanical source parsing only

The subagent prompt at `work/subagent/c2r-01a-inventory.md` SHALL define a read-minimal, mechanical-only phase that runs `tools.py parse-source` and verifies output completeness.

#### Scenario: 01a runs parse-source with correct arguments

- **WHEN** the 01a subagent is invoked
- **THEN** it SHALL run `python WORK_DIR/runtime/tools.py parse-source --source-root SOURCE_ROOT --test-dirs <discovered> --work-dir WORK_DIR --output WORK_DIR/logs/trace/c-to-rust/01a-source-inventory.json`
- **AND** it SHALL discover test directories by checking common patterns under SOURCE_ROOT
- **AND** it SHALL verify the output JSON contains non-empty `files` and `functions` arrays

#### Scenario: 01a does not read C source files

- **WHEN** the 01a subagent prompt is inspected
- **THEN** it SHALL NOT contain instructions to read `.c` or `.h` files
- **AND** its step list SHALL be limited to: discover test dirs, run parse-source, verify JSON fields, produce status summary
- **AND** total prompt SHALL be ≤ 1.5K tokens

#### Scenario: 01a reports parse failures clearly

- **WHEN** `parse_failures` in the output JSON is non-empty
- **THEN** the subagent SHALL list each failed file and the error type in its return summary
- **AND** it SHALL NOT block the pipeline (parse failures are warnings, not blockers, unless `files` is empty)

### Requirement: 01b-capability subagent performs deep per-module scenario analysis

The subagent prompt at `work/subagent/c2r-01b-capability.md` SHALL define a structured capability analysis for ONE C source module, with mandatory output sections and autonomous judgment requirements.

#### Scenario: 01b receives module-specific context

- **WHEN** the 01b subagent is spawned
- **THEN** it SHALL receive `MODULE_SOURCE` (path to one `.c` file), `MODULE_HEADER` (path to corresponding `.h`), and `INVENTORY_PATH` (path to source-inventory.json)
- **AND** it SHALL NOT receive paths to other modules' source files
- **AND** its prompt SHALL explicitly state: "You are analyzing ONE module. Other subagents are analyzing other modules in parallel."

#### Scenario: 01b reads and deeply understands the C source

- **WHEN** the 01b subagent starts
- **THEN** it SHALL read the assigned C source file in full
- **AND** it SHALL read the corresponding header file
- **AND** it SHALL extract from the inventory JSON: functions belonging to this module, their call relationships, types used
- **AND** it SHALL identify: function groups with shared state, state machines, error handling patterns, data structure lifecycles

#### Scenario: 01b outputs a structured scenario document

- **WHEN** the 01b subagent completes analysis
- **THEN** it SHALL write `logs/trace/c-to-rust/capabilities/<module>-scenarios.md`
- **AND** the output SHALL contain these mandatory sections:
  - **Module Overview**: 1 paragraph on what this module does
  - **Identified Capabilities**: For each capability N:
    - Capability name (descriptive, not file-based)
    - Functions involved (with C file line numbers)
    - Trigger conditions
    - State transitions (if applicable, as a state diagram in text)
    - Invariants (at least 1 per capability)
    - Error paths (at least 1 per capability)
    - Boundary conditions (at least 1 per capability)
    - Test scenarios implied by C tests in this module
  - **Cross-module dependencies**: Functions called from other modules, functions this module calls

#### Scenario: 01b exercises autonomous judgment

- **WHEN** the 01b subagent prompt is inspected
- **THEN** it SHALL contain the directive: "You MUST independently decide what constitutes a capability. Do NOT ask the user for guidance. Use these criteria: independent state lifecycle, dedicated error paths, or algorithm with ≥3 intermediate states."
- **AND** it SHALL contain: "If unsure whether to split or merge, prefer splitting. The synthesize phase (01c) will merge if needed."
- **AND** it SHALL contain: "You MUST identify at least 1 capability per module. If you identify only 1, explain why further splitting is not warranted."

#### Scenario: 01b output template prevents laziness

- **WHEN** the 01b output template is inspected
- **THEN** it SHALL use fill-in prompts (e.g., `[Identify the state machine here. If none, write "No state machine" and explain why.]`) instead of HTML comments
- **AND** each section SHALL require explicit content or an explicit "not applicable" statement with reason
- **AND** empty sections SHALL be treated as incomplete

### Requirement: 01c-synthesize subagent merges per-module findings into a capability map

The subagent prompt at `work/subagent/c2r-01c-synthesize.md` SHALL define a synthesis phase that reads all 01b outputs and produces a unified capability map with dependencies and priorities.

#### Scenario: 01c reads only summaries, not C source

- **WHEN** the 01c subagent is invoked
- **THEN** it SHALL receive paths to all `*-scenarios.md` files from 01b
- **AND** it SHALL receive the path to `01a-source-inventory.json`
- **AND** it SHALL NOT receive paths to any C source files
- **AND** its prompt SHALL state: "You are synthesizing findings. Do NOT read C source files. Trust the 01b subagents' analysis."

#### Scenario: 01c identifies cross-module capabilities

- **WHEN** the 01c subagent reads multiple `*-scenarios.md` files
- **THEN** it SHALL compare capability descriptions across modules
- **AND** when two capabilities from different modules describe related behavior (e.g., kvdb's "sector management" and file's "flash erase"), it SHALL create a merged cross-module capability
- **AND** the merged capability SHALL reference the source modules and their scenario files

#### Scenario: 01c assigns priorities based on dependency analysis

- **WHEN** the 01c subagent assigns priorities
- **THEN** P0 SHALL be assigned to capabilities with no internal dependencies (foundational, e.g., CRC32, status table, error types)
- **AND** P1 SHALL be assigned to capabilities that depend only on P0 capabilities (core, e.g., KV CRUD, file I/O)
- **AND** P2 SHALL be assigned to capabilities that depend on P1 or are auxiliary (e.g., print, set_default)
- **AND** the dependency graph SHALL be a DAG with explicit edges

#### Scenario: 01c output is a structured JSON capability map

- **WHEN** the 01c subagent completes
- **THEN** it SHALL write `logs/trace/c-to-rust/01c-capability-map.json`
- **AND** the JSON SHALL have this structure:
  ```json
  {
    "capabilities": [
      {
        "id": "kebab-case-id",
        "name": "Human-readable name",
        "source_modules": ["module1", "module2"],
        "scenario_files": ["capabilities/module1-scenarios.md"],
        "priority": "P0|P1|P2",
        "key_functions": ["func1", "func2"],
        "summary": "One sentence description"
      }
    ],
    "dependency_graph": {
      "capability-id": ["depends-on-id1", "depends-on-id2"]
    },
    "test_coverage_gaps": [
      "Description of scenarios without existing C test coverage"
    ]
  }
  ```

#### Scenario: 01c validates 01b output completeness

- **WHEN** the 01c subagent reads 01b outputs
- **THEN** it SHALL check that each `*-scenarios.md` has all mandatory sections
- **AND** if a module's output is missing sections, it SHALL report `PHASE_DEGRADED` with specific file and missing section names
- **AND** if all outputs are complete, it SHALL report `PHASE_PASS`
