# Java Secure Coding Reference

## Input Validation

Validate external input before business processing when it affects persistence, authorization, query conditions, or business decisions.

Required validation categories:

1. Required fields
2. Enum-like fields
3. Numeric ranges
4. ID existence
5. Relationship consistency
6. Length and format where relevant

Prefer allowlist validation for enum-like fields.

## Error Handling

Forbidden:

1. returning raw exception messages to API consumers
2. exposing stack traces
3. swallowing exceptions silently
4. catching `Exception` and returning success
5. converting validation or security failures into normal success responses

Required:

1. use controlled error responses
2. preserve diagnostic traceability in server-side logs
3. avoid leaking internal implementation details

## Logging

Forbidden:

1. logging passwords
2. logging tokens
3. logging cookies
4. logging authorization headers
5. logging certificates or private keys
6. logging full request bodies when sensitive fields may exist

Required:

1. log only necessary diagnostic context
2. mask or omit sensitive fields
3. avoid excessive logging in normal control flow

## SQL And Data Access

Forbidden:

1. SQL built by string concatenation with untrusted input
2. untrusted MyBatis `${}` interpolation
3. dynamic table names from request parameters
4. dynamic column names from request parameters
5. unvalidated order-by fields

Required:

1. use parameter binding
2. validate dynamic query parameters
3. keep mapper changes minimal

## Authentication And Authorization

Forbidden:

1. removing existing authentication checks
2. bypassing permission checks
3. hardcoding user identity
4. hardcoding tenant identity
5. weakening security filters or interceptors

## Reflection And Dynamic Execution

Forbidden:

1. reflection based on untrusted class names
2. reflection based on untrusted method names
3. runtime command execution from request input
4. unsafe deserialization
5. dynamic script execution
