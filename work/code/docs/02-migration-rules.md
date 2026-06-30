# Migration Rules

## Priority Order

1. Preserve documented FlashDB behavior.
2. Preserve the callable API shape needed by the selected compatibility layer.
3. Keep the Rust project compiling with Cargo.
4. Keep regression tests passing.
5. Reduce undefined-behavior exposure relative to the C baseline.
6. Narrow unsafe usage where locally justified.
7. Improve idiomatic structure only after equivalence is protected.

## General Rules

- Base the migration on `code/FlashDB/inc/*.h` and `code/FlashDB/src/*.c`, not on placeholder examples.
- Treat `code/FlashDB/tests/*.c` as normative regression evidence for observable behavior.
- Keep KVDB and TSDB as separate logical modules in Rust.
- Keep file-mode support because the C tests configure file-backed databases.
- Do not remove power-loss, rollover, GC, or status-transition semantics from the design without explicit evidence.

## API Compatibility Rules

- Preserve the public concepts exposed by `flashdb.h`: KVDB, TSDB, blob, iterator, time callback, status enums, and control commands.
- If a safe Rust API is introduced, document how it maps to the original C API.
- If C ABI compatibility is required, preserve `extern "C"` entrypoints and `#[repr(C)]` types for exposed FFI structs.
- Do not silently drop command-control behaviors such as sector size, file mode, max size, rollover, or not-format flags.

## Storage and Behavior Rules

- Preserve KVDB semantics for set, overwrite, delete-marking, default reset, and iteration ordering expectations used by tests.
- Preserve TSDB semantics for append, forward iteration, reverse iteration, time-range iteration, query count, status transitions, and clean.
- Preserve the distinction between logical deletion and physical reclamation when GC behavior is part of the test baseline.
- Preserve time-based ordering semantics for TSDB records.

## Refactoring Limits

- Large-scale redesign is allowed only if a traceability mapping back to FlashDB concepts is maintained.
- Do not replace FlashDB with a generic Rust embedded database crate.
- Do not optimize storage format before a correct behavioral baseline exists.
