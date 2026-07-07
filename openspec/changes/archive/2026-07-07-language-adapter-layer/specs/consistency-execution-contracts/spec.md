## MODIFIED Requirements

### Requirement: Default Java profile with generic fallback
The system SHALL provide `work/profiles/examples/default-java-consistency.yaml` with Java as the default adapter, automatic detection enabled, and Generic as the fallback adapter. The profile SHALL define consistency analysis dimensions, adapter-selection evidence requirements, and verification command selection while preserving `analyze-only`, `allow_patch=false`, and `allow_code_generation=false` defaults.

#### Scenario: Java project is detected
- **WHEN** source inventory identifies a supported Java project
- **THEN** the default profile selects the Java adapter, records the adapter-selection evidence, and retains the generic consistency output contract for downstream stages

#### Scenario: Java detection fails
- **WHEN** the source does not satisfy Java project detection requirements
- **THEN** the default profile selects the Generic adapter, records the fallback reason, and preserves the same stage IDs, artifact paths, and shared implementation-model contract

### Requirement: Ten-stage execution contract
The system SHALL provide `work/profiles/superspec/design-implementation-consistency-stages.yaml` defining exactly the ordered stages `dic-00` through `dic-09` for preflight, design intake, source inventory, design model extraction, implementation model extraction, traceability mapping, drift analysis, risk classification, repair planning, and finalization. Every stage SHALL declare its inputs, outputs, gate conditions, and failure behavior. Stage `dic-02` MUST emit the selected adapter and selection evidence, and stages `dic-03` through `dic-09` SHALL exchange artifacts that conform to the authoritative Core models for design objects, implementation objects, traceability, drift findings, risk summaries, and final reports.

#### Scenario: Stage completes successfully
- **WHEN** a stage produces all declared outputs and satisfies its gate
- **THEN** the next stage receives only declared file paths and summaries as its cross-stage inputs, and any shared model artifact or adapter-selection artifact conforms to the corresponding Core or language-adapter capability contract

#### Scenario: Stage gate fails
- **WHEN** a stage cannot satisfy a declared gate
- **THEN** execution stops or follows an explicitly declared fail-soft transition, preserves available stage evidence, and retains a path to final reporting when `always_finalize=true`

### Requirement: Cross-artifact contract consistency
The Skill, default Java profile, stage definition, guard definition, and language-adapter capability SHALL use consistent stage identifiers, adapter names, execution defaults, artifact paths, and Core model terminology. Existing generic consistency profiles SHALL be explicitly aligned, referenced as templates, or marked non-authoritative so that the repository exposes one unambiguous default contract, and every stage that emits a shared model artifact SHALL reference the same canonical model names used by the Core and language-adapter capabilities.

#### Scenario: Contract artifacts are validated
- **WHEN** repository validation compares the authoritative contract artifacts
- **THEN** every referenced stage exists, every stage output is permitted by its guard, Java fallback resolves to `generic`, adapter identifiers align across profile and stage definitions, all default execution settings remain read-only, and shared model artifact names align with the Core and language-adapter capabilities

#### Scenario: Legacy generic profile remains present
- **WHEN** an existing generic consistency profile overlaps the new authoritative contract
- **THEN** its role is documented as a compatible template or its values are aligned so it cannot silently override the authoritative defaults or contradict the adapter-selection contract
