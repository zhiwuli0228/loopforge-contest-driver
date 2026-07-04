# LoopForge Official Linux Evaluation Entry

This file is the Linux backup of the official root `INSTRUCTION.md`.

## Prerequisites

Required in `PATH`: `bash`, `python3`, `cargo`, `rustc`, and `node` (for OpenSpec).

## Toolchain Setup

The workflow uses [OpenSpec](https://www.npmjs.com/package/@fission-ai/openspec) for schema-driven artifact management. If `openspec` is not globally installed, the bundled fallback handles it automatically.

### Quick check

```bash
bash work/scripts/openspec.sh --version
```

### If openspec is not available globally

The wrapper auto-installs from the bundled tarball when Node.js is present:

```bash
bash work/vendor/openspec/install.sh
```

Verify:

```bash
bash work/scripts/openspec.sh schemas --json
```

### Fallback mode (no Node.js)

If Node.js is unavailable, `work/scripts/openspec.sh` falls back to a bash-based parser that supports: `schemas`, `status`, `instructions`. This is sufficient for the agent to drive the workflow, but with reduced fidelity.

## SuperPower Guards

Before each migration phase, the agent MUST read the permission boundaries:

```text
work/profiles/superpower/c-to-rust-migration-guards.yaml
```

This file defines allowed tools, filesystem access patterns, and forbidden actions per phase.

## Official execution

```bash
SOURCE_ROOT="E:/001code/csource/FlashDB" bash work/scripts/run.sh --run
```

Requirements come from the preloaded `work/design/README.md`. The harness does not require a README under `SOURCE_ROOT` and never writes into it.

## Generated Rust project

General location:

```text
work/output/<output_project_name>/
```

Current task:

```text
work/output/flashDB_rust/
```

Manual verification:

```bash
cd work/output/flashDB_rust
cargo build --locked
cargo test --locked -- --nocapture
```

## Reports and completion

```text
result/output.md
result/issues/00-summary.md
logs/interaction.md
logs/trace/
logs/trace/c-to-rust/semantic-audit-report.md
```

Completion status is `READY_FOR_EVALUATION` or `BLOCKED_WITH_REPORT`.

When READY, `result/output.md` should point to:

```text
rust_project: work/output/flashDB_rust
cargo_toml: work/output/flashDB_rust/Cargo.toml
semantic_audit_report: logs/trace/c-to-rust/semantic-audit-report.md
```
