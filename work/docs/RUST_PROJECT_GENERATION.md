# Evidence-Driven Rust Project Generation

The Rust generation stage runs after source analysis and semantic planning. It may publish a project for downstream testing only when the independent generation gate passes. A successful Cargo build alone is not a complete-generation claim.

## Inputs and identity

The stage consumes every source-analysis document and `semantic-migration-planning/v3` document required by the preceding gates. Analysis and planning verification must be `PASSED`. Planning documents must share one planning run, source digest, parent analysis run, and semantic IR digest. No target-project profile is accepted. Missing, stale, invalid, legacy, or mixed evidence produces `BLOCKED_WITH_REPORT` without replacing a previously verified project.

The versioned runtime contract is `work/runtime/rust-project-generation.json`. Generation evidence records the analysis run, planning run, source/input/project digests, Rust edition, minimum toolchain, and locked dependency policy. Project names, domain terms, and symbol prefixes never select generation behavior.

## Generated project boundary

The crate has deterministic `Cargo.toml`, `Cargo.lock`, `src/lib.rs`, source-derived modules, and `src/ports.rs`. The ports module is rendered exclusively from verified external-boundary records in the migration plan. Generated state and types use safe Rust by default.

Function-level generation issues do not stop the main project-generation flow. The generator records structured diagnostics, finishes the module tree and evidence skeleton, then runs one final project-neutral repair pass. The final report includes `final_repair_summary` with attempted, resolved, and unresolved counts plus symbol lists. Complex C behavior that still cannot be implemented after that pass is unsupported. It must not be replaced by `todo!()`, `unimplemented!()`, an empty body, or a constant-success function. `unsupported-functions.json` and the final diagnostics are part of the gate, and unresolved entries block downstream test migration.

## Evidence and gates

The stage atomically publishes:

- `implementation-map.json`: stable implementation IDs and concrete Rust symbol locations for the complete source/API denominator.
- `unsupported-functions.json`: every missing or ambiguous implementation; this collection must be empty.
- `module-edge-map.json`: each core C call edge and its planned Rust direct/port-equivalent mapping.
- `unsafe-audit.json`: syntax-node numerator/denominator, ratio, and per-occurrence justification.
- `generation-verification.json`: all checks, metrics, failures, first blocking point, and locked build result.
- `cargo-build.log`: raw stdout/stderr from `cargo build --locked`.

The gate requires non-zero API and core-function denominators, 100% mappings, complete planned call edges, no unresolved generation diagnostics, no unresolved placeholder findings, a non-zero Rust item denominator, `unsafe` ratio strictly below 0.10, and a successful locked build.

## Incremental regeneration

`incremental_regenerate` binds a request to the parent project digest and target module. It stages a full candidate copy, allows changes only in the target/direct-dependency closure, reruns the complete generation gate, and publishes only after all checks pass. `incremental-regeneration-report.json` records pre/post file hashes, the closure, changed files, unchanged files, and boundary result. Unknown targets, stale parents, out-of-bound changes, or candidate validation failures leave the original project untouched.

## Downstream and repair boundaries

The runner sets `rust_generation` after `semantic_planning`. Test migration and semantic repair run only when this gate passes. Change 4 consumes stable implementation/API IDs; Change 5 may repair generated Rust but must rerun this gate and may not weaken its denominators, placeholder rules, or unsafe audit.

Run focused validation with:

```text
python -m unittest work.runtime.tests.test_rust_project_generation -v
```

Any input project that satisfies the analysis and planning schemas uses the same path. Until every core definition and public API in the independently computed denominator is implemented, the correct result is `BLOCKED_WITH_REPORT`.
