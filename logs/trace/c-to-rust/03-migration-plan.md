# Migration Plan

- support_level: `source-driven-c`
- output_project_dir: `flashDB_rust`
- semantic_equivalence_claim: `not_claimed`

## Crate Layout

- `flashDB_rust/src/lib.rs`
- `flashDB_rust/src/flashdb.rs`
- `flashDB_rust/tests/source_migration.rs`

## Test Migration List

- `tests/test_flashdb.c`

## Unsupported Or Degraded Behaviors

- Semantic equivalence is not claimed. The generated crate is source-driven but requires additional manual migration.
