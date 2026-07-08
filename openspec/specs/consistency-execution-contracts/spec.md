# consistency-execution-contracts Specification

## Purpose
TBD - created by archiving change openspec-skill-profile-contracts. Update Purpose after archive.
## Requirements
### Requirement: Authoritative consistency Skill
The system SHALL provide `work/skills/design-implementation-consistency/SKILL.md` as the authoritative orchestration contract for contest-oriented design-implementation consistency repair and verification. The Skill SHALL define `SUBMISSION_ROOT` as the authoritative external input root, require package-level inputs from `SUBMISSION_ROOT/README.md`, `SUBMISSION_ROOT/design-docs/`, `SUBMISSION_ROOT/code/`, and declared verification assets, define profile selection, staged execution, file-based handoff, evidence-bearing findings, bounded repair behavior, and final delivery verdict expectations without embedding Java-only concepts into the generic workflow.

#### Scenario: Operator starts a consistency repair run
- **WHEN** an operator invokes the design-implementation consistency Skill with `SUBMISSION_ROOT`
- **THEN** the Skill identifies the selected profile, resolves the standard submission package assets under `SUBMISSION_ROOT`, executes the declared contest repair-and-verify stages in order, and requires handoff artifacts under `logs/trace/consistency/`

#### Scenario: Finding lacks evidence
- **WHEN** a stage proposes a drift finding without both design evidence and implementation evidence or an explicit unavailable-evidence reason
- **THEN** the Skill rejects the finding as incomplete and prevents it from being reported as a confirmed inconsistency or a justified repair target

### Requirement: Default Java profile with generic fallback
The system SHALL provide `work/profiles/examples/default-java-consistency.yaml` with Java as the default adapter, automatic detection enabled, and Generic as the fallback adapter. The profile SHALL define consistency analysis dimensions, adapter-selection evidence requirements, verification command selection, bounded repair defaults, and retry limits while preserving immutable design and black-box boundaries and enabling contest-default `repair-and-verify`, `allow_patch=true`, and `allow_code_generation=true` behavior for mutable implementation scope.

#### Scenario: Java project is detected
- **WHEN** source inventory identifies a supported Java project
- **THEN** the default profile selects the Java adapter, records the adapter-selection evidence, and retains the generic consistency output contract for downstream stages

#### Scenario: Java detection fails
- **WHEN** the source does not satisfy Java project detection requirements
- **THEN** the default profile selects the Generic adapter, records the fallback reason, and preserves the same stage IDs, artifact paths, and shared implementation-model contract

### Requirement: Ten-stage execution contract
The system SHALL provide `work/profiles/superspec/design-implementation-consistency-stages.yaml` defining exactly the ordered stages `dic-00` through `dic-09` for submission preflight, acceptance baseline extraction, implementation inventory, gap modeling, repair batch planning, repair execution, build verification, black-box verification, targeted regression repair, and final verdict assembly. Every stage SHALL declare its inputs, outputs, gate conditions, and failure behavior, and the authoritative inputs SHALL resolve from the standard submission package under `SUBMISSION_ROOT`. Stage `dic-00` MUST validate the package layout and mutable support-asset policy, `dic-01` MUST intake `README.md` and `design-docs/` into an acceptance baseline, `dic-02` MUST resolve `code/` and verification assets, `dic-03` MUST model design-to-implementation gaps, `dic-04` MUST produce bounded repair batches, `dic-05` MUST apply bounded repairs within the allowed mutation scope, `dic-06` MUST execute build and project-owned verification, `dic-07` MUST execute black-box verification, `dic-08` MUST support targeted retry bounded by profile policy, `dic-09` SHALL assemble the final delivery verdict, cross-stage handoff SHALL occur through declared files under `logs/trace/consistency/`, and the end-to-end repair-and-verify flow SHALL retain a path to `result/output.md`, `result/issues/00-summary.md`, and `logs/trace/final-report.md`.

#### Scenario: Stage completes successfully
- **WHEN** a stage produces all declared outputs, satisfies its gate, and its corresponding stage package emits the declared handoff artifacts
- **THEN** the next stage receives only declared file paths and summaries as its cross-stage inputs, and any submission-package paths referenced by those artifacts resolve to declared assets under `SUBMISSION_ROOT`

#### Scenario: Stage gate fails
- **WHEN** a stage or its corresponding stage package cannot satisfy a declared gate
- **THEN** execution stops or follows an explicitly declared fail-soft or retry transition, preserves available stage evidence under the declared trace paths, records any package-layout, repair, build, black-box, or unavailable-artifact blockage, and retains a path to final reporting when `always_finalize=true`

### Requirement: Stage-scoped permission guards
The system SHALL provide `work/profiles/superpower/design-implementation-consistency-guards.yaml` with deny-by-default permissions and per-stage read and write allowlists. The guards MUST treat `SUBMISSION_ROOT/README.md`, `SUBMISSION_ROOT/design-docs/**`, `SUBMISSION_ROOT/test-cases/**`, and any authoritative package metadata file as immutable baselines, MUST restrict repair writes to declared mutable implementation paths and explicitly allowed contest support assets, and SHALL restrict non-repair stage writes to declared trace or result paths.

#### Scenario: Non-repair stage attempts source modification
- **WHEN** any stage outside the declared repair stages attempts to write within `SUBMISSION_ROOT/code/**` or an allowed support-asset path
- **THEN** the guard denies the operation and records the denied action as execution evidence

#### Scenario: Repair stage writes allowed targets
- **WHEN** a repair stage writes an output path under `SUBMISSION_ROOT/code/**` or another explicitly declared mutable support-asset path and the write is permitted by both the stage contract and the guard allowlist
- **THEN** the guard permits the write without granting access to immutable submission-package assets or unrelated result paths

### Requirement: Cross-artifact contract consistency
The Skill, default Java profile, stage definition, guard definition, language-adapter capability, stage-package capability, and runtime-reporting capability SHALL use consistent stage identifiers, adapter names, execution defaults, artifact paths, mutable-boundary terminology, and final verdict terminology. Existing generic consistency profiles SHALL be explicitly aligned, referenced as templates, or marked non-authoritative so that the repository exposes one unambiguous default contract, every stage that emits a shared model artifact SHALL reference the same canonical model names used by the Core and language-adapter capabilities, every declared stage output SHALL be writable under both the superspec and the matching stage guard, the authoritative runtime commands SHALL resolve to the same final trace and result paths used by the staged workflow, and no authoritative consistency-check entrypoint SHALL require or implicitly resolve to archived `c-to-rust` or `c2r` assets.

#### Scenario: Contract artifacts are validated
- **WHEN** repository validation compares the authoritative contract artifacts
- **THEN** every referenced stage exists, every stage ID resolves to one stage package, every stage output is permitted by its guard, Java fallback resolves to `generic`, adapter identifiers align across profile and stage definitions, default execution settings align to repair-and-verify rather than analyze-only, shared model artifact names align with the Core, language-adapter, and stage-package capabilities, runtime/report outputs align to `logs/trace/consistency/`, `logs/trace/final-report.md`, `result/output.md`, and `result/issues/00-summary.md`, and no authoritative skill/profile/stage/guard/runner reference resolves to archived C2Rust assets

#### Scenario: Legacy consistency or migration assets remain present
- **WHEN** legacy consistency-adjacent or C2Rust migration assets remain in the repository for historical compatibility
- **THEN** their role is documented as archived or non-authoritative so they cannot silently override the default consistency contract, contradict the adapter-selection contract, diverge from the declared stage-package handoff model, or reintroduce legacy migration paths into the authoritative runtime/report flow

