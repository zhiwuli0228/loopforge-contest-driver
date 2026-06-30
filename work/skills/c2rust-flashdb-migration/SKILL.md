---
name: c2rust-flashdb-migration
description: Convert FlashDB C source and tests into a buildable Rust project named flashDB_rust. Use for README-driven C-to-Rust migration tasks where SOURCE_ROOT is read-only.
---

# C2Rust FlashDB Migration Skill

## Mission

Generate a Rust rewrite project at `flashDB_rust/` from the FlashDB C source tree provided by `SOURCE_ROOT`.

## Mandatory Inputs

Read, in order:

1. `INSTRUCTION.md`
2. `work/loopforge.config.yaml`
3. `work/profiles/examples/c2rust-flashdb-migration.yaml`
4. `SOURCE_ROOT/README.md` or `SOURCE_ROOT/READNE.md` or another configured README candidate
5. `SOURCE_ROOT/src` and `SOURCE_ROOT/tests`, or `SOURCE_ROOT/FlashDB/src` and `SOURCE_ROOT/FlashDB/tests`

## Write Scope

Allowed:

- `flashDB_rust/**`
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

- `logs/trace/c2rust/01-source-inventory.md`

Must include:

- selected README path
- resolved FlashDB root
- C source files under `src/`
- C test files under `tests/`
- detected public APIs, structs, macros, storage abstractions, file/flash I/O boundaries

### 2. API and Behavior Mapping

Produce:

- `logs/trace/c2rust/02-api-mapping.md`

Must include:

- C API to Rust module/function mapping
- data model mapping
- error/result strategy
- ownership/lifetime strategy
- unsafe avoidance strategy

### 3. Migration Plan

Produce:

- `logs/trace/c2rust/03-migration-plan.md`

Must include:

- crate layout
- module list
- test migration list
- unsupported or degraded behaviors, if any

### 4. Rust Project Generation

Create:

```text
flashDB_rust/
├── Cargo.toml
├── src/
└── tests/
```

Rules:

- Rust source must be provided, not only build artifacts.
- Prefer safe Rust.
- `unsafe` must be avoided unless strictly required and documented.
- The output crate must be buildable by `cargo build`.

### 5. Test Migration

Create Rust tests under:

```text
flashDB_rust/tests/
```

Each important C test scenario must be migrated or equivalently covered.

Produce:

- `logs/trace/c2rust/04-test-mapping.md`

### 6. Verification

Run inside `flashDB_rust`:

```bash
cargo build
cargo test
```

Produce:

- `logs/trace/c2rust/06-verification-report.md`
- `logs/trace/c2rust/unsafe-ratio.json`

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
- test migration summary

`result/issues/00-summary.md` must include:

- known missing behavior
- failed tests, if any
- degraded compatibility, if any
- serious risks

## Completion Gate

Return `READY_FOR_EVALUATION` only if:

- `flashDB_rust/Cargo.toml` exists
- `flashDB_rust/src` exists
- `flashDB_rust/tests` exists
- `cargo build` passes
- `cargo test` passes
- unsafe ratio is lower than 10%
- `result/output.md` exists
- `result/issues/00-summary.md` exists

Return `BLOCKED_WITH_REPORT` if source layout cannot be resolved or required tools are missing.
