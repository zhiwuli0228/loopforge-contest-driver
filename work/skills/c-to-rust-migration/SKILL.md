---
name: c-to-rust-migration
description: Convert a README-described C source project and its tests into a buildable Rust project. Use for source-readme-driven C-to-Rust migration tasks where SOURCE_ROOT is read-only.
---

# C-To-Rust Migration Skill

## Mission

Serve the execution orchestrator by generating a Rust rewrite project at the runtime-derived output directory from the C source tree provided by `SOURCE_ROOT`.

## Mandatory Inputs

Read, in order:

1. `INSTRUCTION.md`
2. `work/loopforge.config.yaml`
3. `work/profiles/examples/c-to-rust-migration.yaml`
4. `SOURCE_ROOT/README.md` or `SOURCE_ROOT/READNE.md` or another configured README candidate
5. the source and test directories resolved from the active README contract
6. `work/rules/loopforge/adapters/c-to-rust/`

## Write Scope

Allowed:

- runtime-derived Rust output project directory
- `result/**`
- `logs/**`

Forbidden:

- `SOURCE_ROOT/**`
- runtime artifacts inside `SOURCE_ROOT`
- platform-provided C source files
- platform-provided C test files
- git operations

## Required Workflow

### 1. Source Inventory

Produce:

- `logs/trace/c-to-rust/01-source-inventory.md`

Must include:

- selected README path
- resolved source project root
- C source files under resolved source directories
- C test files under resolved test directories
- detected public APIs, structs, macros, include graph, file and I/O boundaries

### 2. API and Behavior Mapping

Produce:

- `logs/trace/c-to-rust/02-api-mapping.md`

Must include:

- C API to Rust module/function mapping
- data model mapping
- error/result strategy
- ownership/lifetime strategy
- unsafe avoidance strategy

### 3. Migration Plan

Produce:

- `logs/trace/c-to-rust/03-migration-plan.md`

Must include:

- crate layout
- module list
- test migration list
- unsupported or degraded behaviors, if any

### 4. Rust Project Generation

Create:

```text
<runtime-derived-output-project>/
├── Cargo.toml
├── src/
└── tests/
```

Rules:

- Rust source must be provided, not only build artifacts.
- Prefer safe Rust.
- `unsafe` must be avoided unless strictly required and documented.
- The output crate must be buildable by `cargo build`.
- Empty crates are forbidden.
- `todo!()` and `unimplemented!()` are forbidden.

### 5. Test Migration

Create Rust tests under:

```text
<runtime-derived-output-project>/tests/
```

Each important C test scenario must be migrated or equivalently covered.
Rust tests must contain assertions.

Produce:

- `logs/trace/c-to-rust/04-test-mapping.md`

### 6. Verification

## Semantic Self-Audit Requirement

Do not claim semantic equivalence only because the generated Rust project builds and existing tests pass. Derive semantic invariants from C source and source tests, including reset behavior, capacity, lookup not-found, insert/update, deletion, and state preservation after errors when applicable.

Generate and execute invariant-derived tests for normal, boundary, error, reset-after-mutation, failed-operation preservation, and head/middle/tail deletion paths. Missing required invariant tests is a blocking failure. If a semantic test fails, repair the implementation, record the repair round, and rerun verification. Never weaken or delete a derived test to make verification pass.

Run inside the runtime-derived Rust output project:

```bash
cargo build
cargo test
```

Produce:

- `logs/trace/c-to-rust/06-verification-report.md`
- `logs/trace/c-to-rust/unsafe-ratio.json`
- semantic gate evidence inside the verification report

### 7. Final Reporting

Produce:

- `result/output.md`
- `result/issues/00-summary.md`
- `logs/trace/final-report.md`

`result/output.md` must include:

- final Rust project path
- build result
- test result
- unsafe ratio
- semantic gate result
- test migration summary

`result/issues/00-summary.md` must include:

- known missing behavior
- failed tests, if any
- degraded compatibility, if any
- serious risks

## Completion Gate

Return `READY_FOR_EVALUATION` only if:

- the runtime-derived Rust project `Cargo.toml` exists
- the runtime-derived Rust project `src` exists
- the runtime-derived Rust project `tests` exists
- `cargo build` passes
- `cargo test` passes
- unsafe ratio is lower than 10%
- semantic gate passes
- semantic invariants were extracted and every required derived test passes
- the repair loop has no unresolved semantic failures
- `result/output.md` exists
- `result/issues/00-summary.md` exists

Return `BLOCKED_WITH_REPORT` if source layout cannot be resolved or required tools are missing.
