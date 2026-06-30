# INSTRUCTION.md — Windows Local Debug Entry

> This file is the temporary root `INSTRUCTION.md` for local Windows debugging.
> The official Linux evaluator version is provided separately as `INSTRUCTION.linux.md`.
> Before final contest packaging, copy the Linux version back to root `INSTRUCTION.md` if the evaluator requires Linux-only execution.

## 1. Purpose

This repository contains a source-readme-driven C-to-Rust migration harness.

During local Windows debugging, this entry uses the PowerShell wrapper:

```powershell
work\scripts\run.ps1
```

The harness reads the C source project path from `SOURCE_ROOT` or the `-SourceRoot` argument, derives migration requirements from the source README/READNE and the bundled task requirement file, then runs the migration pipeline.

## 2. Local Windows Environment Requirements

Use Windows PowerShell or PowerShell 7.

Required tools must be available in `PATH`:

```powershell
python --version
cargo --version
rustc --version
```

Do not use `bash work/scripts/run.sh` in plain Windows PowerShell unless Bash is installed and available. For this Windows debug instruction, use `run.ps1`.

## 3. Source Root

The source root must point to the real C source project root.

Recommended local layout:

```text
<repo-root>\
├── .code\
│   └── FlashDB\
│       ├── README.md / READNE.md
│       ├── src\
│       └── tests\
├── work\
├── result\
└── logs\
```

The local task requirement file is:

```text
work/code/README.md
```

It is only the bundled contest requirement document. It is not the source project root.

## 4. Execute on Windows

From repository root:

```powershell
$env:SOURCE_ROOT = ".code\FlashDB"
powershell -ExecutionPolicy Bypass -File work\scripts\run.ps1
```

Equivalent explicit argument form:

```powershell
powershell -ExecutionPolicy Bypass -File work\scripts\run.ps1 -SourceRoot ".code\FlashDB"
```

The current `run.ps1` calls:

```text
work/runtime/loopforge_runner.py
```

and passes:

```text
--work-dir work
--result-dir result
--log-dir logs
--source-root <resolved-source-root>
--run
```

## 5. Clean Local Artifacts Before a New Debug Run

Use this before collecting a fresh run:

```powershell
Remove-Item -Recurse -Force flashDB_rust -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force logs\trace\c2rust -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force logs\trace\c-to-rust -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force logs\trace\experiments\run-001 -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force result\issues | Out-Null
New-Item -ItemType Directory -Force logs\trace | Out-Null
```

Then run:

```powershell
$env:SOURCE_ROOT = ".code\FlashDB"
powershell -ExecutionPolicy Bypass -File work\scripts\run.ps1
```

## 6. Expected Runtime Outputs

The harness must write:

```text
result/output.md
result/issues/00-summary.md
logs/interaction.md
logs/trace/
```

For the current contest task, the generated Rust project is expected to be:

```text
flashDB_rust/
├── Cargo.toml
├── src/
└── tests/
```

The generated Rust project should be verifiable by:

```powershell
cd flashDB_rust
cargo build
cargo test
cd ..
```

The unsafe ratio must be lower than 10%.

## 7. Completion Status

The run is complete when `result/output.md` exists and reports one of:

```text
READY_FOR_EVALUATION
BLOCKED_WITH_REPORT
```

If the status is `BLOCKED_WITH_REPORT`, the first blocking reason must be recorded in:

```text
result/issues/00-summary.md
```

## 8. Local Failure Classification

If PowerShell starts successfully but the harness fails later, classify by the first blocking point:

```text
A: source root / README discovery failed
B: task requirement parsing failed
C: C source analysis failed
D: Rust project generation failed
E: cargo build failed
F: cargo test / semantic equivalence failed
G: launcher / reporting / environment failure
```

If `flashDB_rust/Cargo.toml` is not generated, do not analyze Cargo or semantic gates first. Check launcher, source root, requirement parsing, and generation logs first.

## 9. Forbidden Runtime Behavior

The harness must not:

- require manual interaction during `--run`
- modify evaluator-provided source files or tests
- write runtime artifacts into the source tree
- rely on prebuilt Rust binaries instead of generated Rust source
- report `READY_FOR_EVALUATION` without generating the required Rust project
- report semantic equivalence based only on structural smoke tests

## 10. Files to Inspect After Failure

Inspect these files first:

```text
result/output.md
result/issues/00-summary.md
logs/trace/
logs/interaction.md
```

If present, also inspect:

```text
logs/trace/c2rust/01-source-inventory.json
logs/trace/c2rust/02-api-mapping.json
logs/trace/c2rust/04-test-mapping.json
logs/trace/c2rust/06-verification-report.md
logs/trace/c2rust/repair-rounds.json
```

or, after generic trace migration:

```text
logs/trace/c-to-rust/01-source-inventory.json
logs/trace/c-to-rust/02-api-mapping.json
logs/trace/c-to-rust/04-test-mapping.json
logs/trace/c-to-rust/06-verification-report.md
logs/trace/c-to-rust/repair-rounds.json
```

## 11. Final Packaging Note

This file is for Windows local debugging. For Linux contest submission, use `INSTRUCTION.linux.md` as the root `INSTRUCTION.md`.
