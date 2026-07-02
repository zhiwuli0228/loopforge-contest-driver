## 1. Canonical Evidence Contract

- [ ] 1.1 Define the versioned canonical manifest schema for source tests, assertions, public APIs, behavior contracts, invariants, source identity, and entity-set digests
- [ ] 1.2 Publish the canonical manifest atomically after verified planning and bind generation, test migration, semantic audit, and final reporting to its digest
- [ ] 1.3 Replace stage-local denominator derivation with stable-ID references to the canonical manifest
- [ ] 1.4 Add negative fixtures for equal counts with different IDs, removed entities, added entities, mixed runs, stale manifests, and legacy synthetic reports

## 2. Real Adapter Execution

- [ ] 2.1 Define project-neutral C and Rust adapter descriptors, observation schema, controlled environment, and allowed normalization rules
- [ ] 2.2 Implement isolated adapter execution with identical input images, seeds, failure plans, timeouts, command logs, and independent execution identities
- [ ] 2.3 Discover or generate the C Oracle build adapter from source/build evidence without project-name, path, API-prefix, or golden-output dispatch
- [ ] 2.4 Generate the Rust adapter from test IR and behavior contracts with explicit vector and entity IDs
- [ ] 2.5 Reject missing, stale, copied, schema-invalid, or non-independent observations instead of synthesizing values
- [ ] 2.6 Implement comparison of contract-linked return, error, visible state, ordering, boundary, persistence, recovery, GC, and side-effect observations
- [ ] 2.7 Add positive generic-fixture and negative one-side failure, missing output, copied output, mismatch, timeout, and stale-output tests

## 3. Real Mutation Campaign

- [ ] 3.1 Define mutation descriptors with target selection, patch preconditions, mutation class, and expected linked detection surfaces
- [ ] 3.2 Apply each mutation in an isolated project copy and verify the source digest changes at the intended target
- [ ] 3.3 Run baseline and mutated linked tests/differential vectors and classify killed, survived, invalid injection, and compile-only detection
- [ ] 3.4 Remove default-all-detected behavior and require concrete failing test or vector evidence for every killed mutation
- [ ] 3.5 Add negative tests for no-op injection, wrong-target injection, missing execution, survivor mutation, stale logs, and compile failure incorrectly counted as semantic detection

## 4. Semantic Coverage Mapping

- [ ] 4.1 Generate assertion and comparison IDs that retain source assertion, behavior contract, API, invariant, test, and vector relationships
- [ ] 4.2 Replace first-assertion/first-vector invariant mapping with relationship-based mappings backed by current-run execution records
- [ ] 4.3 Require every canonical source assertion, public API, and semantic invariant to have non-vacuous linked executed coverage or an explicit blocking diagnostic
- [ ] 4.4 Unify semantic audit and test migration coverage inputs and remove analysis/planning denominator divergence
- [ ] 4.5 Add negative tests for arbitrary shared coverage, unrelated assertions, unexecuted tests, dangling IDs, and partial API coverage

## 5. Authoritative Final Verdict

- [ ] 5.1 Define the required gate manifest and implement one pure authoritative final-verdict calculation in the runner
- [ ] 5.2 Change PowerShell and Bash entrypoints to consume and propagate the runner verdict and exit code without writing independent READY results
- [ ] 5.3 Make Cargo-only success, empty evidence, missing gates, contradictory reports, and legacy schema evidence produce `BLOCKED_WITH_REPORT`
- [ ] 5.4 Add integration tests proving all entrypoints agree when Cargo passes but semantic/differential/mutation gates fail
- [ ] 5.5 Atomically publish coherent output, issue summary, run summary, diagnosis, and referenced evidence from the same verdict identity

## 6. Cross-Platform Determinism

- [ ] 6.1 Move generation-provider enablement, model, timeout, and attempt policy to explicit shared configuration with fail-closed unavailability handling
- [ ] 6.2 Isolate Windows and Linux runs so generated projects, Cargo targets, result files, and trace evidence cannot overwrite one another
- [ ] 6.3 Define normalized repeatability manifests excluding only declared time, absolute-path, and platform-toolchain fields
- [ ] 6.4 Verify two clean runs per platform produce identical entity sets, generated source digest, test set, normalized observations, and verdict
- [ ] 6.5 Verify SOURCE_ROOT content, file modes, and links remain unchanged before and after every platform run

## 7. End-to-End Acceptance

- [ ] 7.1 Run all unit and negative tests on Windows and Ubuntu WSL using the same configuration
- [ ] 7.2 Run the complete generic non-FlashDB fixture pipeline with real C/Rust adapters and mutation campaign on both platforms
- [ ] 7.3 Run the complete FlashDB pipeline on Windows and Ubuntu WSL and require the authoritative verdict to match all published reports
- [ ] 7.4 Verify `cargo build --locked`, non-empty `cargo test --locked -- --nocapture`, unsafe ratio, complete semantic coverage, real differential success, and zero surviving critical mutations
- [ ] 7.5 Record cross-platform repeatability and source-integrity evidence and keep the change blocked unless every README acceptance criterion is proven
