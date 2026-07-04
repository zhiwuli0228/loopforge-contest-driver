## 1. Establish the Preloaded Design Contract

- [x] 1.1 Add the version-controlled `work/design/README.md` submission asset with complete, self-contained contest requirements
- [x] 1.2 Replace source-README input configuration with the fixed `work/design/README.md` contract and remove production fallback configuration
- [x] 1.3 Add preflight validation for a readable, non-empty regular design file and explicit blocked-report issue codes
- [x] 1.4 Compute and propagate the design README canonical path and SHA-256 digest through runtime evidence

## 2. Decouple Source Discovery and Runtime Consumers

- [x] 2.1 Refactor project-root resolution so README presence is neither required nor scored and ambiguous layouts produce candidate diagnostics
- [x] 2.2 Update task-packet construction and requirement parsing to consume only the selected preloaded design path
- [x] 2.3 Update analysis, verification gates, traces, and final reporting to use `design_readme` terminology and evidence
- [x] 2.4 Audit runtime write destinations and enforce that generated or modified artifacts cannot target paths under `SOURCE_ROOT`

## 3. Remove Non-Submission Dependencies

- [x] 3.1 Remove production references and fallback behavior for `work/code/README.md` from runtime code and configuration
- [x] 3.2 Update rules, skills, profiles, subagent contracts, and user documentation to define `work/design/README.md + SOURCE_ROOT` as the formal input model
- [x] 3.3 Remove statements that require `SOURCE_ROOT/README*` and document that source-project README files are non-authoritative if present
- [x] 3.4 Add a repository validation check that rejects forbidden README dependencies in production assets while allowing explicitly scoped test fixtures

## 4. Verification and Submission Readiness

- [x] 4.1 Update resolver and task-packet unit tests for README-free source projects and fixed design input
- [x] 4.2 Add negative tests for missing, empty, unreadable, and non-regular `work/design/README.md`
- [x] 4.3 Add mutation-detection coverage proving successful and failed runs leave `SOURCE_ROOT` unchanged
- [x] 4.4 Update Windows and Linux smoke tests to run with a README-free source fixture
- [x] 4.5 Add a package-shaped end-to-end test with `work/code/` absent and verify successful preflight, design digest evidence, and source discovery
- [x] 4.6 Run unit, smoke, cross-platform, repository-scan, and packaging gates and record the final verification evidence
