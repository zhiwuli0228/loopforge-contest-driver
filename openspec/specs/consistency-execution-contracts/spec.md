# consistency-execution-contracts Specification

## Purpose
TBD - created by archiving change openspec-skill-profile-contracts. Update Purpose after archive.
## Requirements
### Requirement: Authoritative consistency Skill
The system SHALL provide `work/skills/design-implementation-consistency/SKILL.md` as the authoritative orchestration contract for design-implementation consistency checks. The Skill SHALL define required design and source inputs, profile selection, staged execution, file-based handoff, evidence-bearing findings, and final result expectations without embedding Java-only concepts into the generic workflow.

#### Scenario: Operator starts a consistency check
- **WHEN** an operator invokes the design-implementation consistency Skill with a design root and `SOURCE_ROOT`
- **THEN** the Skill identifies the selected profile, executes the declared consistency stages in order, and requires handoff artifacts under `logs/trace/consistency/`

#### Scenario: Finding lacks evidence
- **WHEN** a stage proposes a drift finding without both design evidence and implementation evidence or an explicit unavailable-evidence reason
- **THEN** the Skill rejects the finding as incomplete and prevents it from being reported as a confirmed inconsistency

### Requirement: Default Java profile with generic fallback
The system SHALL provide `work/profiles/examples/default-java-consistency.yaml` with Java as the default adapter, automatic detection enabled, and Generic as the fallback adapter. The profile SHALL define consistency analysis dimensions, adapter-selection evidence requirements, and verification command selection while preserving `analyze-only`, `allow_patch=false`, and `allow_code_generation=false` defaults.

#### Scenario: Java project is detected
- **WHEN** source inventory identifies a supported Java project
- **THEN** the default profile selects the Java adapter, records the adapter-selection evidence, and retains the generic consistency output contract for downstream stages

#### Scenario: Java detection fails
- **WHEN** the source does not satisfy Java project detection requirements
- **THEN** the default profile selects the Generic adapter, records the fallback reason, and preserves the same stage IDs, artifact paths, and shared implementation-model contract

### Requirement: Ten-stage execution contract
The system SHALL provide `work/profiles/superspec/design-implementation-consistency-stages.yaml` defining exactly the ordered stages `dic-00` through `dic-09` for preflight, design intake, source inventory, design model extraction, implementation model extraction, traceability mapping, drift analysis, risk classification, repair planning, and finalization. Every stage SHALL declare its inputs, outputs, gate conditions, and failure behavior, and SHALL map to exactly one corresponding stage package asset under `work/subagent/`. Stage `dic-02` MUST emit the selected adapter and selection evidence, stages `dic-03` through `dic-09` SHALL exchange artifacts that conform to the authoritative Core models for design objects, implementation objects, traceability, drift findings, risk summaries, verification status, and final reports, cross-stage handoff SHALL occur through declared files under `logs/trace/consistency/`, and the end-to-end analyze-only flow SHALL retain a path to `result/output.md`, `result/issues/00-summary.md`, and `logs/trace/final-report.md`.

#### Scenario: Stage completes successfully
- **WHEN** a stage produces all declared outputs, satisfies its gate, and its corresponding stage package emits the declared handoff artifacts
- **THEN** the next stage receives only declared file paths and summaries as its cross-stage inputs, any shared model artifact or adapter-selection artifact conforms to the corresponding Core, language-adapter, stage-package, and runtime-reporting capability contracts, and the pipeline remains able to produce the declared final report files

#### Scenario: Stage gate fails
- **WHEN** a stage or its corresponding stage package cannot satisfy a declared gate
- **THEN** execution stops or follows an explicitly declared fail-soft transition, preserves available stage evidence under the declared trace paths, records any verification blockage or unavailable downstream artifact state, and retains a path to final reporting when `always_finalize=true`

### Requirement: Stage-scoped permission guards
The system SHALL provide `work/profiles/superpower/design-implementation-consistency-guards.yaml` with deny-by-default permissions and per-stage read and write allowlists. The guards MUST prohibit business source modification when patching or code generation is disabled and SHALL restrict writes to the stage's declared artifact or result paths.

#### Scenario: Analysis stage attempts source modification
- **WHEN** any stage attempts to write within `SOURCE_ROOT` while `allow_patch=false` or `allow_code_generation=false`
- **THEN** the guard denies the operation and records the denied action as execution evidence

#### Scenario: Stage writes its declared artifact
- **WHEN** a stage writes an output path declared by both the stage contract and its guard allowlist
- **THEN** the guard permits the write without granting access to unrelated result or source paths

### Requirement: Cross-artifact contract consistency
The Skill, default Java profile, stage definition, guard definition, language-adapter capability, stage-package capability, and runtime-reporting capability SHALL use consistent stage identifiers, adapter names, execution defaults, artifact paths, and Core model terminology. Existing generic consistency profiles SHALL be explicitly aligned, referenced as templates, or marked non-authoritative so that the repository exposes one unambiguous default contract, every stage that emits a shared model artifact SHALL reference the same canonical model names used by the Core and language-adapter capabilities, every declared stage output SHALL be writable under both the superspec and the matching stage guard, the authoritative runtime commands SHALL resolve to the same final trace and result paths used by the staged workflow, and no authoritative consistency-check entrypoint SHALL require or implicitly resolve to archived `c-to-rust` or `c2r` assets.

#### Scenario: Contract artifacts are validated
- **WHEN** repository validation compares the authoritative contract artifacts
- **THEN** every referenced stage exists, every stage ID resolves to one stage package, every stage output is permitted by its guard, Java fallback resolves to `generic`, adapter identifiers align across profile and stage definitions, all default execution settings remain read-only, shared model artifact names align with the Core, language-adapter, and stage-package capabilities, runtime/report outputs align to `logs/trace/consistency/`, `logs/trace/final-report.md`, `result/output.md`, and `result/issues/00-summary.md`, and no authoritative skill/profile/stage/guard/runner reference resolves to archived C2Rust assets

#### Scenario: Legacy consistency or migration assets remain present
- **WHEN** legacy consistency-adjacent or C2Rust migration assets remain in the repository for historical compatibility
- **THEN** their role is documented as archived or non-authoritative so they cannot silently override the default consistency contract, contradict the adapter-selection contract, diverge from the declared stage-package handoff model, or reintroduce legacy migration paths into the authoritative runtime/report flow
