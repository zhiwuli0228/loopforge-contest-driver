# Spec: Database Lifecycle Management

## Capability Overview

This capability implements the shared initialization and deinitialization lifecycle for both KVDB and TSDB databases. It validates sector and max size alignment, configures the storage backend (file mode directory), sets the `init_ok` flag, and handles cleanup. Path resolution is provided for logging and diagnostics. This is the P1 layer that both KVDB and TSDB init functions call before their type-specific initialization.

## Key Functions

| C Function | C File:Line | Rust Equivalent | Behavior Summary |
|------------|-------------|-----------------|------------------|
| `_fdb_init_ex` | `src/fdb.c:31` | `fn fdb_init_ex(db: &mut FdbDb, name: &str, path: &str, db_type: FdbDbType) -> Result<(), FdbError>` | Core initialization: validate params, configure storage backend, validate sector/max size alignment |
| `_fdb_init_finish` | `src/fdb.c:102` | `fn fdb_init_finish(db: &mut FdbDb, result: FdbError)` | Post-initialization: sets `init_ok` flag if no error |
| `_fdb_deinit` | `src/fdb.c:118` | `fn fdb_deinit(db: &mut FdbDb)` | Clean shutdown: close all cached files (file mode), set `init_ok = false` |
| `_fdb_db_path` | `src/fdb.c:141` | `fn fdb_db_path(db: &FdbDb) -> &str` | Resolve the database storage path for logging/diagnostics |

## Data Structures

| C Struct | Fields | Rust Equivalent | Notes |
|----------|--------|----------------|-------|
| `fdb_db` | `name[], type, storage, sec_size, max_size, oldest_addr, init_ok, file_mode, not_formatable, cur_file_sec[], cur_file[], lock, unlock, user_data` | `FdbDb { name: String, db_type: FdbDbType, storage_path: String, sec_size: u32, max_size: u32, oldest_addr: u32, init_ok: bool, file_mode: bool, not_formatable: bool }` | File cache and lock callbacks deferred. `oldest_addr` set by KVDB/TSDB init, not by lifecycle module. |

## Requirements

### REQ-database-lifecycle-001: fdb_init_ex SHALL validate sector size is a power of 2

C source reference: `src/fdb.c:31`

Scenario (normal path):
  GIVEN an `FdbDb` with `sec_size=4096` and `max_size=32768`
  WHEN `fdb_init_ex(&mut db, "test", "/data", FdbDbType::Kv)` is called
  THEN the function SHALL verify `sec_size & (sec_size - 1) == 0`, `max_size % sec_size == 0`, and `max_size / sec_size >= 2`, returning `Ok(())`

Scenario (error path):
  GIVEN `sec_size=5000` (not a power of 2)
  WHEN `fdb_init_ex` is called
  THEN the function SHALL return `Err(FdbError::InitFailed)`

Scenario (boundary condition):
  GIVEN `sec_size=0` in file mode with `max_size=0`
  WHEN `fdb_init_ex` is called
  THEN the function SHALL return `Err(FdbError::InitFailed)` because sector size and max size are required in file mode

### REQ-database-lifecycle-002: fdb_init_ex SHALL require at least 2 sectors

C source reference: `src/fdb.c:31`

Scenario (normal path):
  GIVEN `sec_size=4096` and `max_size=16384` (4 sectors)
  WHEN `fdb_init_ex` validates the sector count
  THEN `max_size / sec_size >= 2` SHALL pass, returning `Ok(())`

Scenario (error path):
  GIVEN `sec_size=4096` and `max_size=4096` (only 1 sector)
  WHEN `fdb_init_ex` is called
  THEN the function SHALL return `Err(FdbError::InitFailed)` -- at least 2 sectors are required for GC and ring-buffer operation

Scenario (boundary condition):
  GIVEN exactly 2 sectors (`max_size / sec_size == 2`)
  WHEN `fdb_init_ex` validates the count
  THEN the check SHALL pass (2 is the minimum valid count)

### REQ-database-lifecycle-003: fdb_init_ex SHALL be idempotent when init_ok is true

C source reference: `src/fdb.c:31`

Scenario (normal path):
  GIVEN a database with `init_ok == true`
  WHEN `fdb_init_ex` is called a second time
  THEN the function SHALL return `Ok(())` immediately without re-validating or re-configuring

Scenario (error path):
  N/A -- When `init_ok == true`, no validation occurs, so no error can be returned.

Scenario (boundary condition):
  GIVEN `init_ok == false` but a prior init configured `name` and `storage_path`
  WHEN `fdb_init_ex` is called again
  THEN the function SHALL re-run full validation as if it were the first call

### REQ-database-lifecycle-004: fdb_init_finish SHALL set init_ok only on success

C source reference: `src/fdb.c:102`

Scenario (normal path):
  GIVEN a database with `init_ok == false` and `result == FDB_NO_ERR`
  WHEN `fdb_init_finish(&mut db, FDB_NO_ERR)` is called
  THEN `db.init_ok` SHALL be set to `true`

Scenario (error path):
  GIVEN `result != FDB_NO_ERR` (any error)
  WHEN `fdb_init_finish` is called
  THEN `db.init_ok` SHALL remain `false` -- the database SHALL NOT be marked as initialized

Scenario (boundary condition):
  GIVEN `init_ok` is already `true` and `result == FDB_NO_ERR`
  WHEN `fdb_init_finish` is called
  THEN `init_ok` SHALL remain `true` (no-op)

### REQ-database-lifecycle-005: fdb_deinit SHALL set init_ok to false and clean up

C source reference: `src/fdb.c:118`

Scenario (normal path):
  GIVEN an initialized database (`init_ok == true`)
  WHEN `fdb_deinit(&mut db)` is called
  THEN all cached file handles SHALL be closed, and `db.init_ok` SHALL be set to `false`

Scenario (error path):
  N/A -- `fdb_deinit` does not return an error; it performs best-effort cleanup.

Scenario (boundary condition):
  GIVEN `init_ok == false` (already deinitialized)
  WHEN `fdb_deinit` is called
  THEN the function SHALL still set `init_ok = false` (idempotent) without attempting file cleanup

## Invariants

- **INV-database-lifecycle-001**: After successful init, `db.sec_size` SHALL be a power of 2, `db.max_size` SHALL be a multiple of `db.sec_size`, and `db.max_size / db.sec_size >= 2`.
- **INV-database-lifecycle-002**: `db.init_ok` SHALL be `true` if and only if init completed successfully and `_fdb_init_finish` received `FDB_NO_ERR`. All CRUD operations SHALL check `init_ok` before proceeding.
- **INV-database-lifecycle-003**: After `fdb_deinit`, `db.init_ok` SHALL be `false`. The database can be re-initialized by calling `fdb_init_ex` again.
- **INV-database-lifecycle-004**: In file mode, `db.sec_size` and `db.max_size` SHALL be explicitly set before `fdb_init_ex` is called; they cannot be derived from a partition table (FAL-only feature).

## Dependencies

- `foundational-types` -- Uses `FdbDb`, `FdbDbType`, `FdbError`.
- `flash-io-dispatch` -- In file mode, file handles are cached and used through the `FlashStorage` trait; cleanup calls file close operations.
