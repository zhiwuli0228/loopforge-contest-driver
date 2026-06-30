# Rust API Design Rules

## API Stability

Do not change public APIs unless the repair plan requires it.

Before changing an API, check:

1. callers;
2. tests;
3. FFI visibility;
4. crate exports;
5. downstream compatibility.

## Type Safety

Prefer type-safe representations.

Use:

1. enums for finite states;
2. newtypes for domain-specific IDs;
3. `NonZero*` types when non-zero is an invariant;
4. `NonNull<T>` for non-null raw pointers when appropriate;
5. `Result` and `Option` for failure and absence.

Avoid:

1. stringly typed states;
2. ambiguous booleans;
3. integer codes without typed meaning;
4. broad generic abstractions without need.

## Naming

Follow Rust naming conventions:

1. snake_case for functions and variables;
2. PascalCase for types and traits;
3. SCREAMING_SNAKE_CASE for constants;
4. clear names over overly short names.

## Visibility

Prefer the narrowest visibility that works.

Use `pub(crate)` when external public API is not required.

## Documentation

Document safety requirements for unsafe APIs.

Document behavior changes when the repair plan changes public behavior.
