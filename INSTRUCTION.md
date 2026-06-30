# Contest Execution Instruction

This repository is a generic source-readme-driven C-to-Rust migration harness.

The only required external input is the source tree root, exposed as `SOURCE_ROOT` or passed by `--source-root`.

## Expected Source Layout

The runner reads the task requirements from the README near `SOURCE_ROOT`.

Supported requirement file names:

- `${SOURCE_ROOT}/README.md`
- `${SOURCE_ROOT}/README`
- `${SOURCE_ROOT}/READNE.md`
- `${SOURCE_ROOT}/readme.md`
- `${SOURCE_ROOT}/Readme.md`

The source project must provide:

- source directories such as `${SOURCE_ROOT}/src` or another README-derived source directory
- test directories such as `${SOURCE_ROOT}/tests` or another README-derived test directory

## Expected Output

After execution, the driver must generate a Rust project in a runtime-derived output directory:

```text
<runtime-derived-output-project>/
├── Cargo.toml
├── src/
└── tests/
```

The generated project must pass:

```bash
cd <runtime-derived-output-project>
cargo build
cargo test
```

The unsafe usage ratio must be lower than 10%.

## Environment

Required tools:

- Python 3
- Rust toolchain with `cargo`
- bash on Linux or PowerShell on Windows

## Source Root Resolution

Resolution priority:

1. contest platform explicit source path
2. `--source-root <path>`
3. `SOURCE_ROOT`
4. Linux fallback: `/__CONTEST_PLATFORM_SOURCE_ROOT__/source`
5. Linux fallback: `/__CONTEST_PLATFORM_SOURCE_ROOT__`
6. local fallback: generic source candidate under `.code/`, `work/code/`, or `code/`

## Run

Linux:

```bash
SOURCE_ROOT="/path/to/source-project" bash work/scripts/run.sh
```

Linux with explicit argument:

```bash
bash work/scripts/run.sh --source-root "/path/to/source-project"
```

Windows PowerShell:

```powershell
$env:SOURCE_ROOT="C:\path\to\source-project"
powershell -ExecutionPolicy Bypass -File work/scripts/run.ps1
```

## Results

Primary evaluator output:

- `result/output.md`

Issue summary:

- `result/issues/00-summary.md`

Trace logs:

- `logs/trace/`
- `logs/trace/c-to-rust/`

Interaction log:

- `logs/interaction.md`

No manual interaction is required during execution.

## Forbidden Runtime Behavior

The driver must not:

- require manual interaction
- modify platform-provided C source or tests
- write runtime artifacts into the source tree
- rely on prebuilt Rust binaries instead of source
- finish without generating an output `Cargo.toml`
- treat `work/code/README.md` as the source root
