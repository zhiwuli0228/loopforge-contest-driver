# LoopForge Official Linux Evaluation Entry

This is the official unattended Linux entrypoint for the C-to-Rust harness.

## Prerequisites

The following commands must be available in `PATH`:

```text
bash
python3
cargo
rustc
```

## Official execution

Run from the repository root:

```bash
SOURCE_ROOT="/absolute/path/to/source/project" bash work/scripts/run.sh --run
```

`SOURCE_ROOT` must identify the evaluator-provided C project containing its README/READNE, source, and tests. The harness does not write into `SOURCE_ROOT`.

## Generated Rust project

All generated Rust projects are written under:

```text
work/output/<output_project_name>/
```

For the current task the expected location is:

```text
work/output/flashDB_rust/
```

Manual verification:

```bash
cd work/output/flashDB_rust
cargo build --locked
cargo test --locked -- --nocapture
```

## Reports

Inspect:

```text
work/result/output.md
work/result/issues/00-summary.md
work/logs/interaction.md
work/logs/trace/
work/logs/trace/c-to-rust/semantic-audit-report.md
```

`work/result/output.md` records the actual generated project path. Completion is reported as exactly one of:

```text
READY_FOR_EVALUATION
BLOCKED_WITH_REPORT
```

The evaluator should read `work/result/output.md` first. When READY, it must report:

```text
rust_project: work/output/flashDB_rust
cargo_toml: work/output/flashDB_rust/Cargo.toml
semantic_audit_report: work/logs/trace/c-to-rust/semantic-audit-report.md
```

## Windows local debugging

Windows is a local debugging path, not the official evaluator entry. Use:

```powershell
powershell -ExecutionPolicy Bypass -File work\scripts\run-e2e-win.ps1 -SourceRoot "work\code\FlashDB"
```

The PowerShell runner resolves the Rust project from `work/result/output.md` or `work/logs/trace/run-summary.json`; it does not assume a root-level `flashDB_rust` directory.
