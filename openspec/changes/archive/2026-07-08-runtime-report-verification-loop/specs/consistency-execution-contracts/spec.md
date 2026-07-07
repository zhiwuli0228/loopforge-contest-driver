## MODIFIED Requirements

### Requirement: Ten-stage execution contract
The system SHALL provide `work/profiles/superspec/design-implementation-consistency-stages.yaml` defining exactly the ordered stages `dic-00` through `dic-09` for preflight, design intake, source inventory, design model extraction, implementation model extraction, traceability mapping, drift analysis, risk classification, repair planning, and finalization. Every stage SHALL declare its inputs, outputs, gate conditions, and failure behavior, and SHALL map to exactly one corresponding stage package asset under `work/subagent/`. Stage `dic-02` MUST emit the selected adapter and selection evidence, stages `dic-03` through `dic-09` SHALL exchange artifacts that conform to the authoritative Core models for design objects, implementation objects, traceability, drift findings, risk summaries, verification status, and final reports, cross-stage handoff SHALL occur through declared files under `logs/trace/consistency/`, and the end-to-end analyze-only flow SHALL retain a path to `result/output.md`, `result/issues/00-summary.md`, and `logs/trace/final-report.md`.

#### Scenario: Stage completes successfully
- **WHEN** a stage produces all declared outputs, satisfies its gate, and its corresponding stage package emits the declared handoff artifacts
- **THEN** the next stage receives only declared file paths and summaries as its cross-stage inputs, any shared model artifact or adapter-selection artifact conforms to the corresponding Core, language-adapter, stage-package, and runtime-reporting capability contracts, and the pipeline remains able to produce the declared final report files

#### Scenario: Stage gate fails
- **WHEN** a stage or its corresponding stage package cannot satisfy a declared gate
- **THEN** execution stops or follows an explicitly declared fail-soft transition, preserves available stage evidence under the declared trace paths, records any verification blockage or unavailable downstream artifact state, and retains a path to final reporting when `always_finalize=true`

### Requirement: Cross-artifact contract consistency
The Skill, default Java profile, stage definition, guard definition, language-adapter capability, stage-package capability, and runtime-reporting capability SHALL use consistent stage identifiers, adapter names, execution defaults, artifact paths, and Core model terminology. Existing generic consistency profiles SHALL be explicitly aligned, referenced as templates, or marked non-authoritative so that the repository exposes one unambiguous default contract, every stage that emits a shared model artifact SHALL reference the same canonical model names used by the Core and language-adapter capabilities, every declared stage output SHALL be writable under both the superspec and the matching stage guard, and the authoritative runtime commands SHALL resolve to the same final trace and result paths used by the staged workflow.

#### Scenario: Contract artifacts are validated
- **WHEN** repository validation compares the authoritative contract artifacts
- **THEN** every referenced stage exists, every stage ID resolves to one stage package, every stage output is permitted by its guard, Java fallback resolves to `generic`, adapter identifiers align across profile and stage definitions, all default execution settings remain read-only, shared model artifact names align with the Core, language-adapter, and stage-package capabilities, and runtime/report outputs align to `logs/trace/consistency/`, `logs/trace/final-report.md`, `result/output.md`, and `result/issues/00-summary.md`

#### Scenario: Legacy generic profile remains present
- **WHEN** an existing generic consistency profile overlaps the new authoritative contract
- **THEN** its role is documented as a compatible template or its values are aligned so it cannot silently override the authoritative defaults, contradict the adapter-selection contract, diverge from the declared stage-package handoff model, or point the runtime/report outputs at conflicting final artifact paths
