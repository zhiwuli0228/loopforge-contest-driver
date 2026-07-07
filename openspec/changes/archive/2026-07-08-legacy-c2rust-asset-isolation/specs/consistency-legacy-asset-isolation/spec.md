## ADDED Requirements

### Requirement: Legacy C2Rust assets are isolated from authoritative consistency paths
The system SHALL isolate retained C2Rust-specific skills, profiles, stage definitions, guard definitions, rules, subagents, and runtime helpers from the authoritative design-implementation consistency workflow. These retained assets SHALL live under `work/archived/c-to-rust/` or an equivalently explicit archive namespace, and they SHALL NOT remain discoverable as default consistency-check entrypoints.

#### Scenario: Operator starts the default consistency workflow
- **WHEN** an operator follows the repository's authoritative consistency-check entry docs, default profile, or runtime command path
- **THEN** the resolved skill, profile, stage, guard, subagent, rule, and runtime helper paths SHALL exclude archived C2Rust assets

#### Scenario: Maintainer needs historical C2Rust materials
- **WHEN** a maintainer needs to inspect or recover legacy migration assets
- **THEN** the repository SHALL provide those assets under the declared archive namespace without presenting them as current default workflow inputs

### Requirement: Archived legacy assets are explicitly marked non-default
The system SHALL mark retained C2Rust assets as archived or non-default wherever they remain user-visible. Any compatibility pointer, README, stub file, or manifest that references an archived asset SHALL state that the authoritative workflow is design-implementation consistency and SHALL direct users to the archive location for historical use only.

#### Scenario: Contributor opens a preserved legacy pointer
- **WHEN** a contributor opens a preserved path that formerly hosted a C2Rust skill, profile, subagent, rule, or runtime helper
- **THEN** the content at that path SHALL indicate that the asset has been archived and SHALL identify the new archive location or replacement behavior

#### Scenario: Repository documentation mentions legacy assets
- **WHEN** repository documentation refers to a retained C2Rust artifact
- **THEN** that reference SHALL describe the artifact as archived, legacy, or non-default rather than as an active consistency-check dependency

### Requirement: Default workflow validation prevents fallback to legacy assets
The system SHALL provide repository validation that detects whether the authoritative consistency-check workflow still resolves to archived C2Rust assets. Validation SHALL cover the default consistency skill, default profiles, stage/guard definitions, runtime entrypoints, and repository-level run instructions.

#### Scenario: Validation checks authoritative workflow references
- **WHEN** repository validation scans the authoritative consistency-check entry chain
- **THEN** it SHALL fail if a default skill, profile, stage, guard, runner, or script reference resolves to a `c-to-rust` or `c2r` asset path that is intended to be archived

#### Scenario: Validation checks trace and runtime namespaces
- **WHEN** repository validation inspects the default consistency runtime and script outputs
- **THEN** it SHALL fail if the default consistency workflow still declares `logs/trace/c-to-rust` or other legacy migration output namespaces as authoritative outputs
