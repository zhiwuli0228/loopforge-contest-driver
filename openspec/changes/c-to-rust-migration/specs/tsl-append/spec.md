# Spec: TSL Append and Storage

## Capability Overview

This capability implements appending time-stamped log entries to the TSDB ring buffer. It validates monotonically increasing timestamps and blob size constraints. Handles sector-full transitions (recording end_info for crash resilience), sector rollover (formatting oldest sector when the ring wraps), and the 3-phase write sequence (PRE_WRITE status, index+data write, WRITE status). Data is stored with index entries growing from the sector top and data from the sector bottom.

## Key Functions

| C Function | C File:Line | Rust Equivalent | Behavior Summary |
|------------|-------------|-----------------|------------------|
| `fdb_tsl_append` | `src/fdb_tsdb.c:509` | `fn fdb_tsl_append(tsdb: &mut FdbTsdb, blob: &FdbBlob, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Append TSL with auto-timestamp (get_time callback or last_time+1) |
| `fdb_tsl_append_with_ts` | `src/fdb_tsdb.c:533` | `fn fdb_tsl_append_with_ts(tsdb: &mut FdbTsdb, blob: &FdbBlob, timestamp: FdbTime, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Append TSL with explicit timestamp |
| `tsl_append` | `src/fdb_tsdb.c:451` | `fn tsl_append(tsdb: &mut FdbTsdb, blob: &FdbBlob, timestamp: FdbTime, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Core append: validate, check space, handle rollover, write |
| `write_tsl` | `src/fdb_tsdb.c:350` | `fn write_tsl(tsdb: &mut FdbTsdb, blob: &FdbBlob, timestamp: FdbTime, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Write TSL index+data to flash with 3-phase status |
| `read_tsl` | `src/fdb_tsdb.c:147` | `fn read_tsl(tsdb: &FdbTsdb, addr: u32, tsl: &mut FdbTsl, flash: &dyn FlashStorage) -> Result<(), FdbError>` | Read TSL index data from flash at given address |
| `update_sec_status` | `src/fdb_tsdb.c:379` | `fn tsdb_update_sec_status(tsdb: &mut FdbTsdb, sec: &mut TsdbSecInfo, blob: &FdbBlob, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Check sector space, handle sector-full transitions and rollover |

## Data Structures

| C Struct | Fields | Rust Equivalent | Notes |
|----------|--------|----------------|-------|
| `fdb_tsl` | `status, time, log_len, addr.index, addr.log` | `FdbTsl { status: FdbTslStatus, time: FdbTime, log_len: u32, addr_index: u32, addr_log: u32 }` | `#[repr(C)]` |
| `log_idx_data` | (in-code struct) | `LogIdxData` | Internal struct for TSL index entry on flash |

## Requirements

### REQ-tsl-append-001: tsl_append SHALL validate timestamp is strictly greater than last_time

C source reference: `src/fdb_tsdb.c:451`

Scenario (normal path):
  GIVEN `db.last_time=100` and a blob with timestamp `200`
  WHEN `tsl_append` is called
  THEN the timestamp validation SHALL pass (`200 > 100`), and the TSL SHALL be written

Scenario (error path):
  GIVEN `db.last_time=100` and a timestamp `50` (not monotonically increasing)
  WHEN `tsl_append` is called
  THEN the function SHALL return `Err(FdbError::WriteErr)` with an error log

Scenario (boundary condition):
  GIVEN `db.last_time=0` (fresh database with no data)
  WHEN `tsl_append` is called with `timestamp=0`
  THEN validation SHALL fail because `0 <= 0` is not strictly greater; the caller SHALL use a timestamp > 0

### REQ-tsl-append-002: write_tsl SHALL use 3-phase write: PRE_WRITE, index+data, WRITE

C source reference: `src/fdb_tsdb.c:350`

Scenario (normal path):
  GIVEN a blob of 128 bytes at the current sector write position
  WHEN `write_tsl` is called
  THEN the TSL index SHALL be written at `cur_sec.empty_idx`, TSL data SHALL be written at `cur_sec.empty_data`, with status transitions: set PRE_WRITE, write index+data, set WRITE

Scenario (error path):
  GIVEN a flash write failure during the index or data write phase
  WHEN `write_tsl` encounters the error
  THEN the TSL SHALL be left in PRE_WRITE status (crash recovery will discard or repair it), and the error SHALL be propagated

Scenario (boundary condition):
  GIVEN the TSL data exactly fills the remaining space in the current sector (`blob.size + idx_size == remain`)
  WHEN `write_tsl` completes
  THEN `cur_sec.remain` SHALL become 0 after the write, and the next append SHALL trigger a sector transition

### REQ-tsl-append-003: update_sec_status SHALL handle sector-full transitions

C source reference: `src/fdb_tsdb.c:379`

Scenario (normal path):
  GIVEN a USING sector with 50 bytes remaining and a blob requiring 200 bytes
  WHEN `tsdb_update_sec_status` checks space
  THEN the current sector SHALL be written with end_info (timestamp, index), marked FULL, and `tsdb.cur_sec` SHALL advance to the next sector

Scenario (error path):
  GIVEN all sectors are FULL and `rollover == false`
  WHEN `tsdb_update_sec_status` tries to find a new sector
  THEN the function SHALL return `Err(FdbError::SavedFull)` -- database is full and rollover is disabled

Scenario (boundary condition):
  GIVEN `rollover == true` and the next sector is the oldest (ring wrap)
  WHEN `tsdb_update_sec_status` advances to the next sector
  THEN the oldest sector SHALL be formatted (erased) before it becomes the new current sector

### REQ-tsl-append-004: TSL data and index SHALL grow from opposite ends of the sector

C source reference: `src/fdb_tsdb.c:350`

Scenario (normal path):
  GIVEN a newly formatted sector
  WHEN the first TSL is written
  THEN the index entry SHALL be written at the top of the sector (`addr + SECTOR_HDR_DATA_SIZE`), and the blob data SHALL be written at the bottom (`addr + sec_size - data_len`)

Scenario (error path):
  N/A -- The layout is determined by the write logic; no separate error path.

Scenario (boundary condition):
  GIVEN multiple TSLs have been written and index and data regions are approaching each other
  WHEN `cur_sec.remain < idx_size + aligned_blob_size`
  THEN `tsdb_update_sec_status` SHALL declare the sector FULL and advance to the next sector

## Invariants

- **INV-tsl-append-001**: Timestamps SHALL be strictly monotonically increasing within a TSDB instance: each appended timestamp SHALL be > `db.last_time`.
- **INV-tsl-append-002**: Each TSL SHALL use a 3-phase write sequence: (1) write PRE_WRITE status, (2) write index entry at `empty_idx` and blob data at `empty_data`, (3) write WRITE status. This enables crash recovery.
- **INV-tsl-append-003**: Index entries SHALL grow forward from the sector top (`addr + SECTOR_HDR_DATA_SIZE`). Data entries SHALL grow backward from the sector bottom (`addr + sec_size`).
- **INV-tsl-append-004**: On sector-full transition, the current sector's `end_info` (timestamp + end_idx + end_info_stat dual slot) SHALL be written before moving to the next sector.
- **INV-tsl-append-005**: In rollover mode, the oldest sector SHALL be erased (formatted) before being reused as the current sector, preventing data accumulation beyond `max_size`.

## Dependencies

- `foundational-types` -- Uses `FdbTsdb`, `FdbTsl`, `TsdbSecInfo`, `FdbTslStatus`, `FdbTime`, `FdbError`.
- `flash-io-dispatch` -- Flash writes for index and data.
- `flash-status-table` -- TSL status transitions use status tables.
- `blob-abstraction` -- Blob data for TSL content.
- `database-lifecycle` -- Requires `init_ok == true`.
- `tsdb-sector-layout` -- Sector formatting, address wrapping, sector info reading.
