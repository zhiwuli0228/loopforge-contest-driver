# Spec: TSL Status Management and Cleanup

## Capability Overview

This capability provides post-write TSL status management: transitions TSLs to user-defined statuses (USER_STATUS1, USER_STATUS2) or DELETED. Includes irreversible full-database cleanup (`tsl_format_all`) that erases all sectors, and the TSDB control API for runtime configuration (sector size, lock/unlock, rollover, file mode).

## Key Functions

| C Function | C File:Line | Rust Equivalent | Behavior Summary |
|------------|-------------|-----------------|------------------|
| `fdb_tsl_set_status` | `src/fdb_tsdb.c:816` | `fn fdb_tsl_set_status(tsdb: &mut FdbTsdb, tsl: &mut FdbTsl, status: FdbTslStatus, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Set TSL status to a user-defined value (USER_STATUS1, USER_STATUS2, DELETED) |
| `fdb_tsl_clean` | `src/fdb_tsdb.c:902` | `fn fdb_tsl_clean(tsdb: &mut FdbTsdb, flash: &mut dyn FlashStorage)` | Erase all data in TSDB (irreversible) |
| `fdb_tsl_to_blob` | `src/fdb_tsdb.c:835` | `fn fdb_tsl_to_blob(tsl: &FdbTsl, blob: &mut FdbBlob)` | Convert TSL object to blob for reading log data |
| `fdb_tsdb_control` | `src/fdb_tsdb.c:916` | `fn fdb_tsdb_control(tsdb: &mut FdbTsdb, cmd: u32, arg: usize)` | Runtime configuration (set/get sector size, rollover, file mode, lock/unlock) |
| `tsl_format_all` | `src/fdb_tsdb.c:880` | `fn tsl_format_all(tsdb: &mut FdbTsdb, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Format (erase) all sectors |

## Data Structures

N/A -- Uses existing `FdbTsl`, `FdbBlob`, `FdbTsdb`.

## Requirements

### REQ-tsl-status-cleanup-001: fdb_tsl_set_status SHALL write a new status to flash via status table

C source reference: `src/fdb_tsdb.c:816`

Scenario (normal path):
  GIVEN a TSL currently at WRITE status, and the caller wants to mark it USER_STATUS1
  WHEN `fdb_tsl_set_status(&mut tsdb, &mut tsl, FdbTslStatus::UserStatus1, &mut flash)` is called
  THEN the TSL's status table at `tsl.addr_index` SHALL be updated with a write, `tsl.status` SHALL become `UserStatus1`, and the function SHALL return `Ok(())`

Scenario (error path):
  GIVEN a flash write failure during status update
  WHEN `fdb_write_status` returns an error
  THEN the function SHALL propagate the error -- the TSL status SHALL NOT be partially updated in the `tsl` struct

Scenario (boundary condition):
  GIVEN a TSL already at DELETED status and the caller tries to set USER_STATUS1
  WHEN `fdb_tsl_set_status` is called
  THEN the status table transition SHALL NOT be possible (status is monotonic; DELETED is terminal), and the function SHALL return an error or be a no-op

### REQ-tsl-status-cleanup-002: fdb_tsl_clean SHALL irreversibly erase all data

C source reference: `src/fdb_tsdb.c:902`

Scenario (normal path):
  GIVEN a TSDB with 4 sectors containing TSL data
  WHEN `fdb_tsl_clean(&mut tsdb, &mut flash)` is called
  THEN `tsl_format_all` SHALL be called, erasing all sectors, `tsdb.cur_sec` SHALL be reset, `tsdb.last_time` SHALL be reset to 0, and all TSL data SHALL be irreversibly gone

Scenario (error path):
  GIVEN a flash erase failure during `tsl_format_all`
  WHEN `fdb_tsl_clean` is called
  THEN the function SHALL NOT fail (best-effort cleanup in C; Rust may log warnings and continue)

Scenario (boundary condition):
  GIVEN an already-empty database (all sectors unformatted or empty)
  WHEN `fdb_tsl_clean` is called
  THEN `tsl_format_all` SHALL still format all sectors (ensuring a clean state), and the function SHALL complete without error

### REQ-tsl-status-cleanup-003: fdb_tsl_to_blob SHALL set blob metadata for reading TSL log data

C source reference: `src/fdb_tsdb.c:835`

Scenario (normal path):
  GIVEN a TSL with `log_len=128`, `addr_log=0x2000`
  WHEN `fdb_tsl_to_blob(&tsl, &mut blob)` is called
  THEN `blob.size` SHALL be set to `128`, `blob.saved_addr` SHALL be set to `tsl.addr_log`, and `blob.saved_len` SHALL be set to `128`

Scenario (error path):
  N/A -- This is a pure metadata assignment function. No I/O or validation.

Scenario (boundary condition):
  GIVEN a TSL with `log_len=0` (zero-length TSL, though unlikely)
  WHEN `fdb_tsl_to_blob` is called
  THEN `blob.size` SHALL be `0` and no data SHALL be readable

### REQ-tsl-status-cleanup-004: fdb_tsdb_control SHALL support runtime configuration commands

C source reference: `src/fdb_tsdb.c:916`

Scenario (normal path):
  GIVEN a TSDB instance and a control command to set `rollover=true`
  WHEN `fdb_tsdb_control(&mut tsdb, FDB_TSDB_CTRL_SET_ROLLOVER, 1)` is called
  THEN `tsdb.rollover` SHALL be set to `true`

Scenario (error path):
  GIVEN an unrecognized control command code
  WHEN `fdb_tsdb_control` is called
  THEN the function SHALL be a no-op (silently ignore in C; Rust may log a warning)

Scenario (boundary condition):
  GIVEN a control command to set `max_len` to a value >= sector size
  WHEN `fdb_tsdb_control` applies the setting
  THEN it SHALL be applied (validation at append time is the responsibility of `tsl_append`)

## Invariants

- **INV-tsl-status-cleanup-001**: TSL status transitions via `fdb_tsl_set_status` SHALL be monotonic (status index only increases). Once a TSL reaches DELETED, it cannot be changed to a user status.
- **INV-tsl-status-cleanup-002**: `fdb_tsl_clean` SHALL be irreversible. After calling this function, all previously stored TSL data is permanently erased (filled with 0xFF).
- **INV-tsl-status-cleanup-003**: `tsl_format_all` SHALL format every sector in the database, regardless of their current state. After formatting, `tsdb.last_time` SHALL be 0 and `tsdb.cur_sec` SHALL be set to the first sector.

## Dependencies

- `foundational-types` -- Uses `FdbTsdb`, `FdbTsl`, `FdbBlob`, `FdbTslStatus`, `FdbTime`, `FdbError`.
- `flash-io-dispatch` -- Flash writes for status updates, flash erases for cleanup.
- `flash-status-table` -- TSL status transitions use status tables.
- `tsl-append` -- `fdb_tsl_set_status` operates on TSLs that were written by `tsl_append`.
- `tsdb-sector-layout` -- `tsl_format_all` uses sector formatting and address iteration.
