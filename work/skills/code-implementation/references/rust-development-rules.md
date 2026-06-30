# Rust Development Rules

## Core Priority

Rust changes must be:

1. correct;
2. memory-safe where feasible;
3. idiomatic;
4. minimal;
5. verifiable.

For migration tasks, correctness and semantic preservation take priority over idiomatic rewriting.

## Correctness-First Workflow

Use this order:

1. Compile.
2. Test.
3. Lint.
4. Optimize only when correctness is proven.

Do not optimize before correctness is established.

## Idiomatic Rust

Prefer:

1. `Result<T, E>` for recoverable failures;
2. `Option<T>` for nullable or absent values;
3. enums for finite states;
4. newtypes for domain-specific IDs;
5. iterators when they improve clarity;
6. narrow visibility;
7. explicit ownership boundaries.

Avoid:

1. unnecessary `clone`;
2. unnecessary allocation;
3. unnecessary `Box<dyn Trait>`;
4. stringly typed states;
5. ambiguous boolean parameters;
6. broad public API expansion.

## Allocation Discipline

Before introducing allocation, check whether a borrow or iterator is sufficient.

Be careful with:

1. `.to_string()`;
2. `.to_owned()`;
3. `.to_vec()`;
4. `.clone()`;
5. `format!`;
6. intermediate `Vec` collections.

## Module and Visibility

Keep visibility narrow.

Prefer:

1. private by default;
2. `pub(crate)` over `pub` when external exposure is not needed;
3. small modules with clear ownership;
4. no broad re-export unless required.

## Performance

Do not introduce performance-oriented complexity unless:

1. correctness is already verified;
2. the repair plan requires it;
3. the patch summary records why it is needed.
