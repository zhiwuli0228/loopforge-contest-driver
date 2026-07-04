## 1. Acceptance Schemas and Run Isolation

- [x] 1.1 Define versioned schemas for the Linux run manifest, stage outcomes, exception ledger, customization audit, repeatability comparison and final verification
- [x] 1.2 Implement unique run identities and one-time Linux workspace creation with initially empty output, logs, result, temporary and Cargo target directories
- [x] 1.3 Mount or enforce `SOURCE_ROOT` as read-only and restrict every stage to declared writable roots
- [x] 1.4 Capture kernel, architecture, toolchain, locale, timezone, environment, mount modes and submission digest in `linux-environment.json`
- [x] 1.5 Reject and record any visible stale output, pre-generated Rust source, old report or undeclared mutable cross-run cache

## 2. Generic Source Root Resolution

- [x] 2.1 Refactor project discovery to enumerate and score candidates only from generic C source, header, build, include and test structure evidence
- [x] 2.2 Support the same resolver path when `SOURCE_ROOT` is the project root or an enclosing directory
- [x] 2.3 Remove README dependency and add successful no-README project resolution coverage
- [x] 2.4 Record all candidates and scoring evidence, and convert zero-candidate or tied-candidate results into explicit ledger exceptions without guessing a default
- [x] 2.5 Add project-neutral fixtures for direct, parent, no-README, ambiguous and missing project layouts

## 3. Read-Only Source Integrity

- [x] 3.1 Implement deterministic pre-run and post-run manifests covering relative paths, content hashes, permissions, file types and symbolic-link targets
- [x] 3.2 Publish `source-before.sha256`, `source-after.sha256` and a structured source-integrity comparison bound to the current run
- [x] 3.3 Detect and report added, removed, modified, permission-changed and retargeted-link inputs without aborting final report generation
- [x] 3.4 Add integration tests proving generation, repair, build and test stages cannot write outside their allowed roots

## 4. Non-Failing Stage Orchestration

- [x] 4.1 Model the full analysis, planning, generation, test migration, differential validation, repair, build, test, unsafe and acceptance pipeline as a dependency DAG
- [x] 4.2 Require each stage to declare evidence inputs, outputs, writable roots, timeout and run identity before execution
- [x] 4.3 Normalize launch, timeout, exit, parse, validation, repair and filesystem failures into append-only exception-ledger records
- [x] 4.4 Continue every independently executable stage after an exception and mark dependency-blocked work as `skipped_dependency` linked to the root exception
- [x] 4.5 Add top-level containment for unexpected exceptions so the runner always converges to report publication rather than losing evidence
- [x] 4.6 Add clean-run, stage-crash, timeout, malformed-evidence, missing-tool and multiple-independent-exception orchestration tests

## 5. Deferred Repair and Final Retry

- [x] 5.1 Queue locally unrepairable coding and validation exceptions as deferred with complete first-attempt evidence
- [x] 5.2 Trigger exactly one final retry pass only after every coding and validation stage has completed or degraded
- [x] 5.3 Restrict final retry inputs to same-run evidence and retain the existing writable scope, assertion, test, differential, unsafe, integrity and customization gates
- [x] 5.4 Re-run every affected targeted and full validation after a final-retry patch before marking `final_retry_repaired`
- [x] 5.5 Convert failed final retries to `unresolved` without further looping and preserve both attempts, root cause, impact and evidence paths
- [x] 5.6 Test final-retry success, final-retry failure, invalid patch rejection and absence of deferred work

## 6. Zero-Customization Static and Structural Audit

- [x] 6.1 Generate a complete submission manifest covering code, scripts, rules, skills, prompts, configuration, templates, fixtures, tests and path names
- [x] 6.2 Implement static detection of FlashDB names and variants, domain concepts, symbols and APIs, error codes, specialized paths/layouts, fixed business counts, golden outputs, dedicated patches and project profiles
- [x] 6.3 Audit configuration sources, defaults, lookup tables, encoded constants and AST/control-flow branches for direct or indirect target-identity dispatch
- [x] 6.4 Remove every target-specific constant, rule, fixture, default, profile and branch from the executable submission path
- [x] 6.5 Produce a machine-readable audit with manifest coverage, rule version, file hashes, findings, dispositions and direct-disqualification status
- [x] 6.6 Make missing scope, scanner errors and unresolved findings fail the compliance gate while preserving normal runner completion

## 7. Runtime Neutrality Provenance

- [x] 7.1 Record provenance for root selection, stage selection, generation, tests, differential comparison, repair strategy and final verdict decisions
- [x] 7.2 Mark target names, paths, symbols and other source-derived identity values as external evidence data and trace their propagation
- [x] 7.3 Reject any flow from target-identity data into branch conditions, strategy selection, comparison expectations, patch templates or acceptance outcomes
- [x] 7.4 Verify every accepted decision is derived only from versioned generic configuration and current-run structural, semantic, diagnostic or test evidence
- [x] 7.5 Add neutral positive fixtures and negative injections for name branches, domain rules, symbol maps, path profiles, golden outputs and encoded identity dispatch

## 8. Linux Entrypoint and Full E2E Scenarios

- [x] 8.1 Update the Linux bootstrap and run entrypoints to create the isolated workspace and invoke the DAG unattended with explicit environment prerequisites
- [x] 8.2 Execute a clean E2E run with `SOURCE_ROOT` directly naming the project and verify complete Rust project generation from empty output
- [x] 8.3 Execute a clean E2E run with `SOURCE_ROOT` naming an enclosing directory and verify the same unique project is selected
- [x] 8.4 Execute the formal path when the source contains no README and verify no stage relies on README presence or content
- [x] 8.5 Verify `cargo build --locked` and `cargo test --locked -- --nocapture` logs contain commands, exit states and actual executed test names/counts
- [x] 8.6 Verify unsafe ratio is strictly below 0.10 with per-site evidence and source integrity remains byte-for-byte and metadata-equivalent

## 9. Fresh-Run Repeatability

- [x] 9.1 Run each formal input-layout scenario twice from separate empty directories with distinct run identities
- [x] 9.2 Define and version the minimal project-neutral normalization whitelist for run IDs, timestamps, temporary absolute paths and non-semantic randomness
- [x] 9.3 Compare generated relative paths, content hashes, structured evidence, counts, diagnostics and final states across consecutive runs
- [x] 9.4 Report every non-whitelisted divergence with its minimal evidence and prevent repeatability-gate success
- [x] 9.5 Add a negative test proving normalization cannot hide generated code, test, count, diagnostic or compliance differences

## 10. Non-Vacuous Final Verification

- [x] 10.1 Validate non-zero source file, public API, source test, semantic invariant, differential scenario and executed Rust test counts
- [x] 10.2 Validate complete API and source-test mappings, zero unsupported functions, current-run identity and existence/hash of every referenced artifact
- [x] 10.3 Aggregate locked Cargo results, differential and mutation results, repair integrity, unsafe ratio, source integrity, layout scenarios, repeatability and zero-customization status
- [x] 10.4 Publish separate `execution_status` and `compliance_status`, allowing `READY_FOR_EVALUATION` only when all hard gates pass and unresolved count is zero
- [x] 10.5 Add negative tests for empty, zero-count, missing, stale, cross-run and internally inconsistent evidence to prove the gate cannot pass vacuously

## 11. Atomic Evidence and Exception Reporting

- [x] 11.1 Stage and atomically publish environment, source manifests, build/test logs, unsafe report, customization audit, exception ledger, repeatability report and `final-verification.json`
- [x] 11.2 Generate `result/output.md` and `result/issues/00-summary.md` from the same aggregate model and validate matching status, counts and evidence paths
- [x] 11.3 List every unresolved exception near the final conclusion with ID, stage, root cause, impact, first attempt, final retry and evidence path
- [x] 11.4 Implement an independent minimal fallback publisher and structured stderr summary for primary aggregation, rendering or atomic-write failures
- [x] 11.5 Test normal publication, partial write failure, unwritable primary target, conflicting report state and multiple unresolved exceptions

## 12. Final Submission Acceptance

- [x] 12.1 Run the full zero-customization audit against the exact packaged submission tree and archive its complete machine-readable evidence
- [x] 12.2 Run all direct-root, parent-root, no-README, degradation, final-retry and consecutive-clean-run scenarios in the formal Linux environment
- [ ] 12.3 Verify every required artifact is from the current run, non-empty, schema-valid, hash-addressed and consistent with both human-readable reports
- [x] 12.4 Verify injected customization always yields explicit disqualification while the runner completes and reports normally
- [x] 12.5 Verify unresolved operational exceptions never crash the pipeline and never produce a false `READY_FOR_EVALUATION`
- [ ] 12.6 Archive the final environment manifest, commands, evidence index and acceptance verdict for independent reproduction
