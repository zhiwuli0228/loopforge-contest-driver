# Source Inventory

- selected_readme: `.code/FlashDB/README.md`
- fallback_readme: `work/code/README.md`
- source_root: `.code/FlashDB`
- resolved_project_root: `.code/FlashDB`
- source_project_name: `FlashDB Local Fallback`

## Source Files

- `src/flashdb.c`
- `src/flashdb.h`

## Test Files

- `tests/test_flashdb.c`

## Public APIs

- `flashdb_count`
- `flashdb_delete`
- `flashdb_new`
- `flashdb_set`

## Types

- `flashdb_handle`
- `flashdb_record`

## Macros

- `FLASHDB_H`

## Include Graph

- `src/flashdb.c` -> flashdb.h, stddef.h, string.h
- `src/flashdb.h` -> stddef.h
- `tests/test_flashdb.c` -> flashdb.h
