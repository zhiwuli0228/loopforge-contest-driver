# Rust Error Handling Rules

## Basic Rule

Avoid panics in production logic.

Do not introduce `.unwrap()` or `.expect()` unless the invariant is explicit, local, and documented.

## Preferred Patterns

Use:

1. `Result<T, E>` for recoverable errors;
2. `Option<T>` for absence;
3. `?` for propagation;
4. project-local error types;
5. `From` / `Into` conversions when they simplify error flow.

## Unwrap / Expect Policy

Allowed:

1. test code;
2. examples;
3. impossible-by-construction invariants;
4. one-time initialization with clear failure semantics.

Forbidden:

1. parsing external input;
2. file or network I/O;
3. FFI boundaries;
4. user-controlled data;
5. production request paths.

## Error Messages

Error messages must be useful but not leak sensitive internal state.

For FFI and C2Rust tasks, preserve existing error semantics unless the repair plan explicitly changes them.

## Panic Boundaries

Panics must not cross FFI boundaries.

For extern-callable functions, convert panics to controlled error behavior when needed.
