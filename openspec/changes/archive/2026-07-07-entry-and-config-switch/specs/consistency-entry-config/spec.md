## ADDED Requirements

### Requirement: Repository entry and workspace docs use consistency-check semantics
The repository entry documentation SHALL present the project as a design-implementation consistency checking harness, and the workspace documentation SHALL describe the same operating model without framing the project as a C/C++ to Rust migration task.

#### Scenario: Root documentation is reoriented
- **WHEN** a contributor opens the top-level repository documentation or workspace README
- **THEN** the primary description SHALL communicate consistency-check behavior and current execution intent

#### Scenario: Legacy migration framing is removed from entry docs
- **WHEN** the entry documentation is reviewed for the main project purpose
- **THEN** the dominant narrative SHALL NOT describe the repository as a Rust migration harness

### Requirement: Default configuration selects consistency-check analyze-only behavior
The default loopforge configuration SHALL set the task semantics to `consistency-check` and the execution strategy to `analyze-only` for the new baseline workflow.

#### Scenario: Baseline configuration is loaded
- **WHEN** the default configuration is read for a new run
- **THEN** the configured mode SHALL resolve to `consistency-check`
- **AND THEN** the execution policy SHALL resolve to `analyze-only`

#### Scenario: Configuration does not imply code mutation
- **WHEN** the default workflow is started without user overrides
- **THEN** the configuration SHALL not imply business code edits or repair actions

### Requirement: Design README becomes the authoritative consistency-check task contract
The `work/design/README.md` file SHALL define the consistency-check task contract, including the expected input model, outputs, and completion criteria for the first change boundary.

#### Scenario: Design README is used as task contract
- **WHEN** the runtime or contributor reads `work/design/README.md`
- **THEN** the document SHALL describe the consistency-check task contract and its required outputs

#### Scenario: Design README supports downstream changes
- **WHEN** later changes consume `work/design/README.md`
- **THEN** the document SHALL provide enough contract detail to guide follow-on design and implementation work
