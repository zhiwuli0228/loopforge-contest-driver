# LoopForge Official Linux Evaluation Entry

This file is the Linux backup of the official root `INSTRUCTION.md`.

## Prerequisites

Required in `PATH`: `bash`, `python3`, `cargo`, and `rustc`.

## Official execution

```bash
SOURCE_ROOT="/absolute/path/to/source/project" bash work/scripts/run.sh --run
```

The harness never writes into `SOURCE_ROOT`.

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
work/result/output.md
work/result/issues/00-summary.md
work/logs/interaction.md
work/logs/trace/
work/logs/trace/c-to-rust/semantic-audit-report.md
```

Completion status is `READY_FOR_EVALUATION` or `BLOCKED_WITH_REPORT`.

When READY, `work/result/output.md` should point to:

```text
rust_project: work/output/flashDB_rust
cargo_toml: work/output/flashDB_rust/Cargo.toml
semantic_audit_report: work/logs/trace/c-to-rust/semantic-audit-report.md
```

For Windows-only local debugging, use `work/scripts/run-e2e-win.ps1`; it derives the generated project path from `work/result/output.md` or `work/logs/trace/run-summary.json`.
