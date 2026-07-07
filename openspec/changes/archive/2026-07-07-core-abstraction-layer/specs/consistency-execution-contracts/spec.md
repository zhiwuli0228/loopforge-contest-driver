## MODIFIED Requirements

### Requirement: Ten-stage execution contract
The system SHALL provide `work/profiles/superspec/design-implementation-consistency-stages.yaml` defining exactly the ordered stages `dic-00` through `dic-09` for preflight, design intake, source inventory, design model extraction, implementation model extraction, traceability mapping, drift analysis, risk classification, repair planning, and finalization. Every stage SHALL declare its inputs, outputs, gate conditions, and failure behavior. Stages `dic-03` through `dic-09` SHALL exchange artifacts that conform to the authoritative Core models for design objects, implementation objects, traceability, drift findings, risk summaries, and final reports.

#### Scenario: Stage completes successfully
- **WHEN** a stage produces all declared outputs and satisfies its gate
- **THEN** the next stage receives only declared file paths and summaries as its cross-stage inputs, and any shared model artifact conforms to the corresponding Core capability contract

#### Scenario: Stage gate fails
- **WHEN** a stage cannot satisfy a declared gate
- **THEN** execution stops or follows an explicitly declared fail-soft transition, preserves available stage evidence, and retains a path to final reporting when `always_finalize=true`

### Requirement: Cross-artifact contract consistency
The Skill, default Java profile, stage definition, and guard definition SHALL use consistent stage identifiers, adapter names, execution defaults, artifact paths, and Core model terminology. Existing generic consistency profiles SHALL be explicitly aligned, referenced as templates, or marked non-authoritative so that the repository exposes one unambiguous default contract, and every stage that emits a shared model artifact SHALL reference the same canonical model names used by the Core capability.

#### Scenario: Contract artifacts are validated
- **WHEN** repository validation compares the four authoritative contract artifacts
- **THEN** every referenced stage exists, every stage output is permitted by its guard, Java fallback resolves to `generic`, all default execution settings remain read-only, and shared model artifact names align with the Core capability

#### Scenario: Legacy generic profile remains present
- **WHEN** an existing generic consistency profile overlaps the new authoritative contract
- **THEN** its role is documented as a compatible template or its values are aligned so it cannot silently override the authoritative defaults
