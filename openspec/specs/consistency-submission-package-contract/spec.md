# consistency-submission-package-contract Specification

## Purpose
TBD - created by archiving change standard-submission-package-contract. Update Purpose after archive.
## Requirements
### Requirement: Standard submission package layout
The system SHALL treat a contest-style standard submission package as the authoritative external input model for implementation-validation workflows. A valid submission package MUST be rooted at `SUBMISSION_ROOT` and MUST contain `README.md`, `design-docs/`, and `code/`. The package MUST also contain `test-cases/` unless an authoritative package metadata file explicitly declares that black-box tests are not part of the submission contract.

#### Scenario: Standard package is present
- **WHEN** preflight inspects `SUBMISSION_ROOT` and finds `README.md`, `design-docs/`, `code/`, and `test-cases/`
- **THEN** the workflow accepts the package as structurally valid and records the resolved package layout for downstream stages

#### Scenario: Required package asset is missing
- **WHEN** preflight cannot resolve one of the required standard package assets and no authoritative metadata waives that asset
- **THEN** the workflow records the package as invalid, emits evidence describing the missing path, and blocks authoritative analysis

### Requirement: Authoritative source-of-truth hierarchy
The system SHALL treat `SUBMISSION_ROOT/README.md` as the authoritative entry contract for package-level rules, frozen API baselines, frozen error-code baselines, verification commands, and modification boundaries, and SHALL treat `SUBMISSION_ROOT/design-docs/` as the authoritative business-design corpus. The system MUST NOT replace these inputs with repository-local fallback design files during authoritative submission analysis, and it MUST preserve evidence showing whether a downstream requirement originated from the package README or the design corpus.

#### Scenario: Package-level rules and detailed design are both present
- **WHEN** design intake loads the standard package
- **THEN** it reads `README.md` as the package contract entrypoint, reads `design-docs/` as the detailed design corpus, and preserves evidence showing which requirement came from which source

#### Scenario: Repository-local fallback conflicts with submission package
- **WHEN** a repository-local design asset disagrees with `SUBMISSION_ROOT/README.md` or `SUBMISSION_ROOT/design-docs/`
- **THEN** the workflow treats the submission package assets as authoritative and records the local asset as non-authoritative context only

### Requirement: Standard write-boundary enforcement
The system SHALL treat `SUBMISSION_ROOT/design-docs/`, `SUBMISSION_ROOT/test-cases/`, `SUBMISSION_ROOT/README.md`, and any authoritative package metadata file as read-only validation baselines. In the default contest repair-and-verify workflow, the system MUST restrict business-source mutations to `SUBMISSION_ROOT/code/` and MAY allow mutation only for explicitly declared contest support assets needed to execute authoritative verification. The workflow MUST continue to forbid mutations to the design and test baselines and MUST preserve denial evidence when a write targets an out-of-bounds path.

#### Scenario: Repair-enabled run targets baseline assets
- **WHEN** a repair-enabled workflow proposes a patch to `SUBMISSION_ROOT/README.md`, `SUBMISSION_ROOT/design-docs/**`, `SUBMISSION_ROOT/test-cases/**`, or any undeclared support asset
- **THEN** the workflow rejects the patch target as out of bounds and preserves the denial as execution evidence

#### Scenario: Repair-enabled run targets declared mutable support asset
- **WHEN** a repair-enabled workflow proposes a mutation to an explicitly declared contest support asset needed to execute package verification
- **THEN** the workflow permits the write only if the asset is named by the authoritative contract and the mutation does not alter the frozen design or evaluation baselines

### Requirement: Standard verification asset boundary
The system SHALL treat verification commands and black-box validation assets declared by the standard submission package as part of the authoritative evaluation contract. The workflow MUST preserve the distinction between package-supplied black-box tests under `test-cases/` and mutable project-owned tests under `code/`, and MUST preserve any package-declared ordering dependency between business-code verification and black-box verification.

#### Scenario: Black-box validation assets are discovered
- **WHEN** the package contains `test-cases/` and the package contract declares verification commands that use it
- **THEN** the workflow records `test-cases/` as read-only evaluation input and excludes it from business-source repair scope

#### Scenario: Package verification differs from project-owned unit tests
- **WHEN** verification planning identifies commands for both `code/` tests and `test-cases/` black-box tests
- **THEN** the workflow preserves both command classes separately, records their ordering relationship when declared, and reports which outcomes came from mutable project tests versus immutable evaluation tests

