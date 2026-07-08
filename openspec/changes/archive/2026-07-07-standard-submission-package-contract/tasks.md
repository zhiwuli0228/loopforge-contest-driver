## 1. Contract And Entry Model

- [x] 1.1 Update the authoritative documentation and Skill/profile contracts to define `SUBMISSION_ROOT` as the external input root instead of `SOURCE_ROOT`.
- [x] 1.2 Rewrite the repository-facing task contract so `README.md`, `design-docs/`, `code/`, and `test-cases/` are described as the standard submission package assets with explicit responsibilities.
- [x] 1.3 Add configuration fields for standard package path resolution, including package README, design directory, code directory, test directory, and optional metadata file handling.

## 2. Stage And Guard Refactor

- [x] 2.1 Update preflight and source-inventory stage contracts so they validate and emit the resolved standard submission package layout before downstream analysis begins.
- [x] 2.2 Update design-intake, implementation-model, repair-planning, and finalization stage packages so their declared inputs and outputs reference the standard package subpaths explicitly.
- [x] 2.3 Update deny-by-default guards so analyze-only runs forbid all writes under `SUBMISSION_ROOT` and future repair-enabled flows are constrained to `SUBMISSION_ROOT/code/`.

## 3. Runtime And Adapter Changes

- [x] 3.1 Refactor runtime path resolution and command inputs so `scan-design`, `scan-code`, `extract-implementation`, `run-verification`, and `write-report` operate on standard package subpaths instead of an arbitrary repository root.
- [x] 3.2 Refactor design scanning to ingest `SUBMISSION_ROOT/README.md` plus `SUBMISSION_ROOT/design-docs/` as the authoritative design corpus and preserve source-of-truth evidence.
- [x] 3.3 Refactor adapter selection and implementation extraction so Java and Generic adapters scan only `SUBMISSION_ROOT/code/`.
- [x] 3.4 Refactor verification planning so package-declared commands from `README.md` or authoritative metadata are preferred over language-level auto-detection, with fallback status preserved explicitly.

## 4. Validation And Regression Coverage

- [x] 4.1 Add or update automated tests for standard package layout validation, source-of-truth precedence, and immutable baseline enforcement.
- [x] 4.2 Add or update runtime tests for code-scoped adapter selection, package-scoped verification command resolution, and final report scope rendering.
- [x] 4.3 Run the relevant test suite and contract validation checks to confirm the standard submission package contract is complete and apply-ready.
