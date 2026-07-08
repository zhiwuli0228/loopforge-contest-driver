## MODIFIED Requirements

### Requirement: Authoritative consistency Skill
The system SHALL provide `work/skills/design-implementation-consistency/SKILL.md` as the authoritative orchestration contract for design-implementation consistency checks. The Skill SHALL define `SUBMISSION_ROOT` as the authoritative external input root, require package-level inputs from `SUBMISSION_ROOT/README.md`, `SUBMISSION_ROOT/design-docs/`, `SUBMISSION_ROOT/code/`, and declared verification assets, define profile selection, staged execution, file-based handoff, evidence-bearing findings, and final result expectations without embedding Java-only concepts into the generic workflow.

#### Scenario: Operator starts a consistency check
- **WHEN** an operator invokes the design-implementation consistency Skill with `SUBMISSION_ROOT`
- **THEN** the Skill identifies the selected profile, resolves the standard submission package assets under `SUBMISSION_ROOT`, executes the declared consistency stages in order, and requires handoff artifacts under `logs/trace/consistency/`

#### Scenario: Finding lacks evidence
- **WHEN** a stage proposes a drift finding without both design evidence and implementation evidence or an explicit unavailable-evidence reason
- **THEN** the Skill rejects the finding as incomplete and prevents it from being reported as a confirmed inconsistency

### Requirement: Ten-stage execution contract
The system SHALL provide `work/profiles/superspec/design-implementation-consistency-stages.yaml` defining exactly the ordered stages `dic-00` through `dic-09` for preflight, design intake, source inventory, design model extraction, implementation model extraction, traceability mapping, drift analysis, risk classification, repair planning, and finalization. Every stage SHALL declare its inputs, outputs, gate conditions, and failure behavior, and the authoritative inputs SHALL resolve from the standard submission package under `SUBMISSION_ROOT`. Stage `dic-00` MUST validate the package layout, `dic-01` MUST intake `README.md` and `design-docs/`, `dic-02` MUST resolve `code/` and verification assets, stages `dic-03` through `dic-09` SHALL exchange artifacts that conform to the authoritative Core models for design objects, implementation objects, traceability, drift findings, risk summaries, verification status, and final reports, cross-stage handoff SHALL occur through declared files under `logs/trace/consistency/`, and the end-to-end analyze-only flow SHALL retain a path to `result/output.md`, `result/issues/00-summary.md`, and `logs/trace/final-report.md`.

#### Scenario: Stage completes successfully
- **WHEN** a stage produces all declared outputs, satisfies its gate, and its corresponding stage package emits the declared handoff artifacts
- **THEN** the next stage receives only declared file paths and summaries as its cross-stage inputs, and any submission-package paths referenced by those artifacts resolve to declared assets under `SUBMISSION_ROOT`

#### Scenario: Stage gate fails
- **WHEN** a stage or its corresponding stage package cannot satisfy a declared gate
- **THEN** execution stops or follows an explicitly declared fail-soft transition, preserves available stage evidence under the declared trace paths, records any package-layout, verification, or unavailable-artifact blockage, and retains a path to final reporting when `always_finalize=true`

### Requirement: Stage-scoped permission guards
The system SHALL provide `work/profiles/superpower/design-implementation-consistency-guards.yaml` with deny-by-default permissions and per-stage read and write allowlists. The guards MUST treat `SUBMISSION_ROOT/README.md`, `SUBMISSION_ROOT/design-docs/**`, `SUBMISSION_ROOT/test-cases/**`, and any authoritative package metadata file as immutable baselines, MUST prohibit business source modification when patching or code generation is disabled, and SHALL restrict writes to declared trace or result paths in analyze-only mode.

#### Scenario: Analysis stage attempts source modification
- **WHEN** any stage attempts to write within `SUBMISSION_ROOT` while `allow_patch=false` or `allow_code_generation=false`
- **THEN** the guard denies the operation and records the denied action as execution evidence

#### Scenario: Stage writes its declared artifact
- **WHEN** a stage writes an output path declared by both the stage contract and its guard allowlist
- **THEN** the guard permits the write without granting access to unrelated result paths or immutable submission-package assets
