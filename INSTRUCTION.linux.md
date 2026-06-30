# INSTRUCTION.linux.md — Official Linux Contest Entry

> This is the Linux evaluator entry version.
> Before final contest packaging, copy this file to root `INSTRUCTION.md` if the official evaluator requires `/INSTRUCTION.md` as the only entrypoint.

## 1. Purpose

This repository contains a source-readme-driven C-to-Rust migration harness.

The harness reads a C source project from the evaluator-provided source path, derives migration requirements from the source README/READNE and bundled task requirement file, generates a Rust rewrite project, runs verification, and writes result reports.

## 2. Official Execution Environment

The official execution environment is Linux.

Required tools must be available in `PATH`:

```bash
bash --version
python3 --version || python --version
cargo --version
rustc --version
```

No manual interaction is required during execution.

## 3. Input Source Root

The evaluator should provide the source project path through either:

```bash
SOURCE_ROOT="/absolute/path/to/source/project"
```

or:

```bash
bash work/scripts/run.sh --run --source-root "/absolute/path/to/source/project"
```

The source root should contain the source project README/READNE and C source/test directories.

Supported README/requirement file names near `SOURCE_ROOT`:

```text
README.md
README
READNE.md
readme.md
Readme.md
```

The harness must derive source layout and migration requirements from the source README/READNE and bundled task requirement file:

```text
work/code/README.md
```

## 4. Linux Source Root Resolution

Resolution priority:

```text
1. explicit evaluator-provided source path
2. --source-root <path>
3. SOURCE_ROOT environment variable
4. /__CONTEST_PLATFORM_SOURCE_ROOT__/source
5. /__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB
6. /__CONTEST_PLATFORM_SOURCE_ROOT__
7. local fallback .code/FlashDB
8. local fallback code/FlashDB
```

`work/code/README.md` is the bundled contest requirement file. It is not the source project root.

## 5. Execute

Recommended official command:

```bash
SOURCE_ROOT="/absolute/path/to/source/project" bash work/scripts/run.sh --run
```

Explicit source-root form:

```bash
bash work/scripts/run.sh --run --source-root "/absolute/path/to/source/project"
```

If the evaluator injects the source path through platform fallback directories, run:

```bash
bash work/scripts/run.sh --run
```

## 6. Expected Generated Rust Project

The generated Rust project name, source directories, test directories, build commands, and unsafe threshold are derived from the source README/READNE and task requirement file.

For the current C-to-Rust contest task, the expected generated Rust project is:

```text
flashDB_rust/
├── Cargo.toml
├── src/
└── tests/
```

The generated project must be verifiable by:

```bash
cd flashDB_rust
cargo build
cargo test
```

The unsafe ratio must be lower than 10%.

## 7. Required Outputs

After execution, the harness must write:

```text
result/output.md
result/issues/00-summary.md
logs/interaction.md
logs/trace/
```

Trace outputs may include either the current task trace path:

```text
logs/trace/c2rust/
```

or the generic migration trace path:

```text
logs/trace/c-to-rust/
```

The result report must include:

```text
generated Rust project path
source root used
build result
test result
unsafe ratio result
semantic/test migration status
known unsupported behavior or blocking reason
```

## 8. Completion Criteria

The run is complete when `result/output.md` exists and reports one of:

```text
READY_FOR_EVALUATION
BLOCKED_WITH_REPORT
```

`READY_FOR_EVALUATION` is valid only when all required gates pass:

```text
source discovery
source inventory
Rust project generation
cargo build
cargo test
unsafe ratio
test migration / semantic gate
result report generation
```

`BLOCKED_WITH_REPORT` is valid only when the first blocking reason is recorded in:

```text
result/issues/00-summary.md
```

## 9. Forbidden Runtime Behavior

The harness must not:

- require manual interaction during execution
- modify platform-provided source files or tests
- write runtime artifacts into the source tree
- rely on prebuilt Rust binaries instead of generated Rust source
- finish without writing `result/output.md`
- report `READY_FOR_EVALUATION` without generating a Rust project with `Cargo.toml`
- claim semantic equivalence based only on placeholder tests or structural smoke tests

## 10. Failure Diagnosis Standard

If execution fails, diagnose the first blocking point only:

```text
A: source root / README discovery failed
B: task requirement parsing failed
C: C source analysis failed
D: Rust project generation failed
E: cargo build failed
F: cargo test / semantic equivalence failed
G: launcher / reporting / environment failure
```

Do not treat downstream historical reports as the current run result. The current run is determined by the latest process stderr/stdout, `result/output.md`, `result/issues/00-summary.md`, and `logs/trace/`.

## 11. Clean Re-run Command

For a clean Linux re-run:

```bash
rm -rf flashDB_rust
rm -rf logs/trace/c2rust
rm -rf logs/trace/c-to-rust
mkdir -p result/issues logs/trace
touch logs/interaction.md

SOURCE_ROOT="/absolute/path/to/source/project" bash work/scripts/run.sh --run
```

## 12. Minimal Post-run Checks

```bash
test -f result/output.md
test -f result/issues/00-summary.md
test -d logs/trace
test -f flashDB_rust/Cargo.toml
test -d flashDB_rust/src
test -d flashDB_rust/tests
```

If `flashDB_rust/Cargo.toml` does not exist, inspect `result/issues/00-summary.md` and `logs/trace/` before running Cargo manually.
