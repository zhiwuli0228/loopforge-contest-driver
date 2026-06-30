# Unsafe Boundary

## Expected Unsafe Areas

Unsafe Rust may be needed for these FlashDB migration concerns:

1. raw pointer compatibility for an FFI-facing API;
2. `#[repr(C)]` data layout preservation;
3. in-place byte parsing or serialization of storage records;
4. callbacks crossing C ABI boundaries;
5. manual buffer and slice reconstruction from persisted records.

## Areas That Should Prefer Safe Rust

- high-level KVDB and TSDB public APIs exposed to Rust callers;
- iterator state management;
- time-range filtering logic;
- status transition validation;
- path, file, and user-facing configuration plumbing.

## Required Safety Notes

Every non-trivial unsafe block must document:

1. pointer validity assumptions;
2. alignment assumptions;
3. initialization guarantees;
4. aliasing constraints;
5. lifetime ownership;
6. nullability handling;
7. who owns deallocation responsibility.

## ABI Preservation Rules

If the migration provides a C-compatible layer, preserve:

- `extern "C"` calling convention for exported ABI;
- `#[repr(C)]` on FFI-visible structs and enums where layout matters;
- field order and scalar width compatibility for exposed types;
- caller-owned buffer semantics for blob reads and writes.

## Unsafe Minimization Goal

Unsafe code is acceptable for correctness-preserving compatibility work, but the preferred architecture is:

- safe Rust core logic;
- small, audited unsafe boundary at serialization or FFI edges.
