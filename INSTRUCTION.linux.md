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
result/output.md
result/issues/00-summary.md
logs/interaction.md
logs/trace/
logs/trace/c-to-rust/semantic-audit-report.md
```

Completion status is `READY_FOR_EVALUATION` or `BLOCKED_WITH_REPORT`.

For Windows-only local debugging, use `work/scripts/run-e2e-win.ps1`; it derives the generated project path from `result/output.md` or `logs/trace/run-summary.json`.
