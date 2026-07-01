## ADDED Requirements

### Requirement: Preloaded design is the authoritative requirement source
The system SHALL use the committed `work/design/README.md` as the sole authoritative source of task requirements, constraints, and acceptance criteria.

#### Scenario: Load the submitted design contract
- **WHEN** a contest run starts with a valid `work/design/README.md`
- **THEN** the runtime contract and every downstream stage use that file as their requirement input

#### Scenario: Ignore source-project documentation as requirements
- **WHEN** `SOURCE_ROOT` contains one or more README files
- **THEN** those files do not override, augment, or replace `work/design/README.md`

### Requirement: Design input is preflight validated
The system MUST stop before source analysis when `work/design/README.md` is missing, unreadable, not a regular file, or empty, and MUST emit an explicit blocked report identifying the submission-contract error.

#### Scenario: Missing preloaded design
- **WHEN** `work/design/README.md` does not exist at startup
- **THEN** execution ends as `BLOCKED_WITH_REPORT` without selecting another README

#### Scenario: Empty preloaded design
- **WHEN** `work/design/README.md` contains no effective content
- **THEN** execution ends as `BLOCKED_WITH_REPORT` with a design-input validation issue

### Requirement: Source project does not require a README
The system SHALL discover and analyze the source project without requiring or scoring README presence under `SOURCE_ROOT`.

#### Scenario: README-free source project
- **WHEN** `SOURCE_ROOT` contains a uniquely resolvable C or C++ project with translation units and no README
- **THEN** source discovery succeeds using source, build, test, and directory evidence

#### Scenario: Ambiguous README-free layout
- **WHEN** filesystem and build evidence cannot identify one defensible project root
- **THEN** execution blocks with candidate and ambiguity diagnostics instead of using README presence or guessing

### Requirement: Local work code is not a production dependency
Production runtime, configuration, rules, skills, subagent contracts, and packaging SHALL NOT require `work/code/` or use `work/code/README.md` as a requirement source or fallback.

#### Scenario: Submission excludes work code
- **WHEN** the harness runs from a submission package that has no `work/code/` directory
- **THEN** startup, source discovery, requirement loading, and execution proceed without missing-fixture errors

### Requirement: Source root remains read-only
The system MUST treat `SOURCE_ROOT` and every resolved source-project path beneath it as input-only and MUST place generated or modified artifacts outside that tree.

#### Scenario: Successful execution preserves source input
- **WHEN** a run analyzes, migrates, repairs, or verifies an injected source project
- **THEN** no file or directory under `SOURCE_ROOT` is created, modified, renamed, or deleted by the harness

### Requirement: Design identity is recorded as evidence
The system SHALL compute a SHA-256 digest of the validated `work/design/README.md` and record both its canonical path and digest in runtime evidence available to final reporting.

#### Scenario: Evidence identifies exact design bytes
- **WHEN** preflight accepts the preloaded design README
- **THEN** the run evidence contains its canonical path and SHA-256 digest before downstream execution begins

### Requirement: Submission validation proves input independence
The submission validation suite MUST include a package-shaped execution with `work/code/` absent and a valid README-free `SOURCE_ROOT`.

#### Scenario: Package-shaped validation succeeds
- **WHEN** submission validation runs with only the formal harness assets, `work/design/README.md`, and a README-free source fixture
- **THEN** the run passes input preflight and demonstrates no production dependency on omitted README sources
