# Rust Unsafe and FFI Rules

## Unsafe Principle

`unsafe` does not remove the obligation to uphold Rust's safety rules.

Every non-trivial unsafe block must have a clear safety reason.

## Required Safety Notes

For each unsafe block added or modified, record or document:

1. pointer validity;
2. alignment;
3. initialization;
4. aliasing;
5. lifetime;
6. nullability;
7. thread-safety;
8. ownership and deallocation responsibility.

Use a `// SAFETY:` comment when appropriate.

## Raw Pointers

Do not dereference raw pointers unless:

1. the pointer is non-null when required;
2. the pointer is aligned;
3. the pointed-to memory is initialized;
4. the lifetime is valid for the access;
5. aliasing rules are upheld;
6. mutability assumptions are valid.

## FFI Boundary

For FFI code:

1. keep unsafe at the boundary;
2. expose safe wrappers where feasible;
3. validate input pointers before use;
4. preserve ABI;
5. preserve `repr(C)` for FFI-visible structs;
6. avoid panics crossing FFI boundaries;
7. document ownership transfer.

## Slices From Raw Parts

Before using `slice::from_raw_parts` or `from_raw_parts_mut`, prove:

1. pointer is valid for `len` elements;
2. memory is initialized;
3. memory is not mutated through another alias for immutable slice;
4. memory is uniquely accessible for mutable slice;
5. total size does not overflow `isize::MAX`.

## MaybeUninit

When using `MaybeUninit`:

1. do not assume initialized memory before initialization;
2. initialize all fields before `assume_init`;
3. avoid reading uninitialized memory;
4. preserve drop safety.

## Transmute

Avoid `transmute`.

If unavoidable, document:

1. source and target layout compatibility;
2. alignment;
3. validity invariants;
4. lifetime effects.

Prefer safer conversions when available.

## Panic and FFI

Do not allow Rust panics to cross C ABI boundaries.

Use controlled boundary handling for `extern "C"` functions.
