## 1. Evidence Contracts and Neutrality Baseline

- [x] 1.1 Define versioned Repair IR, repair-attempt, exception-ledger and integrity-summary schemas with run identity, content hashes and evidence references
- [x] 1.2 Implement adapters that normalize compiler, targeted-test, full-regression and differential diagnostics without project-name or symbol-name dispatch
- [x] 1.3 Add schema and non-vacuity validators that reject missing evidence, stale run identities and aggregate/detail count mismatches
- [x] 1.4 Inventory and remove any repair profile, target-project constant, domain-specific rule, fixed business count or specialized repair template from the submission path

## 2. Repair Planning and Isolated Patch Execution

- [x] 2.1 Implement evidence-driven repair task planning for type, borrow, unresolved-symbol and observable semantic diagnostics
- [x] 2.2 Compute allowed edit scopes from diagnostic locations plus direct call/type graph dependencies, with generated Rust output as the only writable root
- [x] 2.3 Apply candidate patches in isolated project copies and atomically commit only fully verified patches
- [x] 2.4 Generate per-attempt repair task, patch, changed-lines and provenance evidence for accepted and rejected candidates
- [x] 2.5 Add bounded local repair-loop configuration and deterministic attempt identifiers without embedding target-project defaults

## 3. Non-Failing Degradation and Final Retry

- [x] 3.1 Implement a structured exception ledger covering parse, generation, conflict, launch, timeout, targeted-verification and regression failures
- [x] 3.2 Change stage orchestration to convert all repair exceptions into deferred records and continue every independently executable coding or validation stage
- [x] 3.3 Track dependency-caused skipped work separately from root exceptions to prevent misleading cascading diagnostics
- [x] 3.4 Implement exactly one end-of-run retry pass over deferred items using newly available same-run evidence without relaxing any gate
- [x] 3.5 Mark final retry outcomes as repaired or unresolved and preserve complete attempt history, evidence and affected scope
- [x] 3.6 Add top-level fallback handling that completes execution and atomically publishes a minimal valid exception report even when normal report generation fails

## 4. Repair Integrity Gates

- [x] 4.1 Implement pre/post test inventory and source-test mapping comparison that rejects removed or reduced test coverage
- [x] 4.2 Implement assertion AST comparison that rejects deletion, weakening, constant-true, self-comparison and wildcard-match assertions
- [x] 4.3 Implement `unsafe` delta auditing with per-site necessity evidence and enforcement of the existing strict ratio gate
- [x] 4.4 Run targeted verification followed by locked full regression and applicable differential validation for every candidate patch
- [x] 4.5 Reject and preserve evidence for candidates that edit read-only input, submission rules, tests without mechanical justification or graph-unrelated files

## 5. Zero-Customization Compliance

- [x] 5.1 Implement static scanning of repair code, rules, templates, configuration and fixtures for FlashDB names/variants, domain knowledge, symbols, paths, APIs, error codes and fixed business expectations
- [x] 5.2 Audit configuration sources and AST/control-flow branches to reject indirect project profiles, identity defaults and target-name dispatch that keyword scanning alone cannot prove
- [x] 5.3 Record runtime decision provenance for every repair strategy and edit-scope choice, traceable only to Repair IR, current-run diagnostics and source relationship evidence
- [x] 5.4 Build domain-neutral minimal fixtures that test repair categories without copying FlashDB APIs, layout, behavior or identifiers
- [x] 5.5 Add a submission compliance test that fails the compliance gate and reports a direct disqualification exception when any target-specific asset or decision is injected

## 6. Fault Injection Verification

- [x] 6.1 Implement AST/IR-based injectors for Rust type mismatch, borrow conflict and unresolved-symbol defects
- [x] 6.2 Implement evidence-selected injectors for return-value, state-transition and boundary off-by-one semantic defects
- [x] 6.3 Execute each of the six defect categories at least three times with recorded seed, baseline hash and isolated evidence directory
- [x] 6.4 Verify every injection is detected, repaired through the normal path, passes targeted and full regression checks, and retains all required per-round artifacts
- [x] 6.5 Route injection or repair failures through deferred final retry and prove unsuccessful repetitions remain explicit unresolved exceptions rather than being averaged away

## 7. Reporting and Runner Integration

- [x] 7.1 Publish separate execution and compliance statuses so normal pipeline completion cannot imply repair or evaluation readiness
- [x] 7.2 Generate atomic aggregate reports with attempt, repaired, deferred, final-retry-repaired, unresolved and rejected-patch counts plus evidence paths
- [x] 7.3 Wire the repair loop after generated-project testing/differential validation and expose its evidence to the later Linux E2E gate
- [x] 7.4 Ensure unresolved exceptions prevent a false compliant result while the runner still exits normally with complete reports
- [x] 7.5 Add clean-run, partial-tool-failure, timeout, report-write-failure and multiple-unresolved-exception integration tests

## 8. End-to-End Acceptance

- [x] 8.1 Run the complete coding and validation pipeline against a project-neutral fixture and verify local repair, degradation, final retry and unresolved reporting paths
- [x] 8.2 Verify source inputs and submission rules remain byte-for-byte unchanged across all repair and fault-injection runs
- [x] 8.3 Validate every required per-round artifact exists, references the current run and agrees with the aggregate report
- [x] 8.4 Run the zero-customization audit across the final submission tree and archive its machine-readable evidence for Change 6
