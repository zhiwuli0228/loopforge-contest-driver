# Rust Ownership and Borrowing Rules

## Ownership Analysis Order

When facing ownership or borrow checker issues, analyze in this order:

1. What is the domain meaning of the value?
2. Who logically owns the value?
3. Is the value mutable or immutable?
4. Is sharing required?
5. Is duplication semantically correct?
6. Can a borrow express the relationship?
7. Is shared ownership required?
8. Is interior mutability required?

Do not apply `.clone()` as the first solution.

## Clone Policy

Use `.clone()` only when:

1. duplication is semantically required;
2. the value is cheap and intentionally copied;
3. ownership must diverge across independent lifetimes;
4. the repair plan accepts it.

Avoid `.clone()` when:

1. a borrow would work;
2. `Arc<T>` better represents shared immutable ownership;
3. the clone hides a design issue;
4. the cloned value is large or expensive;
5. the clone is only used to silence the compiler.

## Borrowing

Prefer borrowing when:

1. the callee does not need ownership;
2. the value outlives the call;
3. mutation is not needed;
4. lifetime remains local and clear.

Use `&str` instead of `&String` unless `String`-specific behavior is required.

Use `&[T]` instead of `&Vec<T>` unless vector-specific behavior is required.

## Shared Ownership

Use `Arc<T>` when:

1. data is shared across threads;
2. immutable shared ownership is intended;
3. clone cost of the payload is high.

Use `Rc<T>` only for single-threaded shared ownership.

Use interior mutability only when the mutation model requires it.

## Lifetimes

Do not widen lifetimes unnecessarily.

Prefer local lifetime inference unless explicit lifetimes improve API clarity or are required.
