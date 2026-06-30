# Scope

## Goal

Migrate the provided FlashDB C implementation to a Rust project while preserving externally observable behavior for the selected FlashDB feature set.

The migration target is not a toy example. It is the FlashDB codebase under `code/FlashDB/`.

## Source Baseline

- Main C headers: `code/FlashDB/inc/*.h`
- Main C implementation: `code/FlashDB/src/*.c`
- Behavior references: `code/FlashDB/docs/*.md`
- Regression references: `code/FlashDB/tests/fdb_kvdb_tc.c`
- Regression references: `code/FlashDB/tests/fdb_tsdb_tc.c`

## Required Rust Output

- `code/Cargo.toml`
- `code/src/**`
- `code/tests/**`
- optional FFI shim files if C ABI compatibility is preserved

## Migration Target

The Rust project must cover these FlashDB capabilities:

1. Blob helper behavior used by both database modes.
2. KVDB initialization, control, set, get, delete, reset, and iteration APIs.
3. TSDB initialization, control, append, iteration, query-count, status update, and clean APIs.
4. File-mode behavior sufficient to model the current test and demo expectations.

## Out of Scope

- Do not migrate STM32, RT-Thread, or vendor HAL demo trees as direct Rust rewrites.
- Do not preserve internal sector layout byte-for-byte unless required for a chosen compatibility path.
- Do not expand API scope beyond the C headers and tests without documenting it.
- Do not claim full FlashDB parity unless KVDB and TSDB behavior is both covered.

## Current Input Gaps

The repository currently contains the C baseline and frozen requirements, but does not yet contain:

- `code/Cargo.toml`
- `code/src/`
- `code/tests/`

Those files are expected to be created by the Rust migration work, not treated as pre-existing inputs.
