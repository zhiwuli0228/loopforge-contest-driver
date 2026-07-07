## ADDED Requirements

### Requirement: Authoritative consistency Skill
The system SHALL provide `work/skills/design-implementation-consistency/SKILL.md` as the authoritative orchestration contract for design-implementation consistency checks. The Skill SHALL define required design and source inputs, profile selection, staged execution, file-based handoff, evidence-bearing findings, and final result expectations without embedding Java-only concepts into the generic workflow.

#### Scenario: Operator starts a consistency check
- **WHEN** an operator invokes the design-implementation consistency Skill with a design root and `SOURCE_ROOT`
- **THEN** the Skill identifies the selected profile, executes the declared consistency stages in order, and requires handoff artifacts under `logs/trace/consistency/`

#### Scenario: Finding lacks evidence
- **WHEN** a stage proposes a drift finding without both design evidence and implementation evidence or an explicit unavailable-evidence reason
- **THEN** the Skill rejects the finding as incomplete and prevents it from being reported as a confirmed inconsistency

### Requirement: Default Java profile with generic fallback
The system SHALL provide `work/profiles/examples/default-java-consistency.yaml` with Java as the default adapter, automatic detection enabled, and Generic as the fallback adapter. The profile SHALL define consistency analysis dimensions and verification command selection while preserving `analyze-only`, `allow_patch=false`, and `allow_code_generation=false` defaults.

#### Scenario: Java project is detected
- **WHEN** source inventory identifies a supported Java project
- **THEN** the default profile selects the Java adapter and retains the generic consistency output contract

#### Scenario: Java detection fails
- **WHEN** the source does not satisfy Java project detection requirements
- **THEN** the default profile selects the Generic adapter without changing downstream stage IDs or output model locations

### Requirement: Ten-stage execution contract
The system SHALL provide `work/profiles/superspec/design-implementation-consistency-stages.yaml` defining exactly the ordered stages `dic-00` through `dic-09` for preflight, design intake, source inventory, design model extraction, implementation model extraction, traceability mapping, drift analysis, risk classification, repair planning, and finalization. Every stage SHALL declare its inputs, outputs, gate conditions, and failure behavior.

#### Scenario: Stage completes successfully
- **WHEN** a stage produces all declared outputs and satisfies its gate
- **THEN** the next stage receives only declared file paths and summaries as its cross-stage inputs

#### Scenario: Stage gate fails
- **WHEN** a stage cannot satisfy a declared gate
- **THEN** execution stops or follows an explicitly declared fail-soft transition, preserves available stage evidence, and retains a path to final reporting when `always_finalize=true`

### Requirement: Stage-scoped permission guards
The system SHALL provide `work/profiles/superpower/design-implementation-consistency-guards.yaml` with deny-by-default permissions and per-stage read and write allowlists. The guards MUST prohibit business source modification when patching or code generation is disabled and SHALL restrict writes to the stage's declared artifact or result paths.

#### Scenario: Analysis stage attempts source modification
- **WHEN** any stage attempts to write within `SOURCE_ROOT` while `allow_patch=false` or `allow_code_generation=false`
- **THEN** the guard denies the operation and records the denied action as execution evidence

#### Scenario: Stage writes its declared artifact
- **WHEN** a stage writes an output path declared by both the stage contract and its guard allowlist
- **THEN** the guard permits the write without granting access to unrelated result or source paths

### Requirement: Cross-artifact contract consistency
The Skill, default Java profile, stage definition, and guard definition SHALL use consistent stage identifiers, adapter names, execution defaults, and artifact paths. Existing generic consistency profiles SHALL be explicitly aligned, referenced as templates, or marked non-authoritative so that the repository exposes one unambiguous default contract.

#### Scenario: Contract artifacts are validated
- **WHEN** repository validation compares the four authoritative contract artifacts
- **THEN** every referenced stage exists, every stage output is permitted by its guard, Java fallback resolves to `generic`, and all default execution settings remain read-only

#### Scenario: Legacy generic profile remains present
- **WHEN** an existing generic consistency profile overlaps the new authoritative contract
- **THEN** its role is documented as a compatible template or its values are aligned so it cannot silently override the authoritative defaults
