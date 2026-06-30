# Contest Execution Instruction

This repository is a contest driver for the FlashDB C-to-Rust migration task.

The only required external input is the source tree root, exposed as `SOURCE_ROOT` or passed by `--source-root`.

## Expected Source Layout

The runner reads the task requirements from the README near `SOURCE_ROOT`.

Supported requirement file names:

- `${SOURCE_ROOT}/README.md`
- `${SOURCE_ROOT}/README`
- `${SOURCE_ROOT}/READNE.md`
- `${SOURCE_ROOT}/readme.md`
- `${SOURCE_ROOT}/Readme.md`

The FlashDB source tree must provide:

- `${SOURCE_ROOT}/src` or `${SOURCE_ROOT}/FlashDB/src`
- `${SOURCE_ROOT}/tests` or `${SOURCE_ROOT}/FlashDB/tests`

## Expected Output

After execution, the driver must generate a Rust project:

```text
flashDB_rust/
├── Cargo.toml
├── src/
└── tests/
```

The generated project must pass:

```bash
cd flashDB_rust
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
5. Linux fallback: `/__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB`
6. Linux fallback: `/__CONTEST_PLATFORM_SOURCE_ROOT__`
7. local fallback: `.code/FlashDB`

## Run

Linux:

```bash
SOURCE_ROOT="/path/to/FlashDB" bash work/scripts/run.sh
```

Linux with explicit argument:

```bash
bash work/scripts/run.sh --source-root "/path/to/FlashDB"
```

Windows PowerShell:

```powershell
$env:SOURCE_ROOT="C:\path\to\FlashDB"
powershell -ExecutionPolicy Bypass -File work/scripts/run.ps1
```

## Results

Primary evaluator output:

- `result/output.md`

Issue summary:

- `result/issues/00-summary.md`

Trace logs:

- `logs/trace/`
- `logs/trace/c2rust/`

Interaction log:

- `logs/interaction.md`

No manual interaction is required during execution.

## Forbidden Runtime Behavior

The driver must not:

- require manual interaction
- modify platform-provided FlashDB source or tests
- write runtime artifacts into the source tree
- rely on prebuilt Rust binaries instead of source
- finish without generating `flashDB_rust/Cargo.toml`
- treat `work/code/README.md` as the source root
