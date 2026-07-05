# Spec: KVDB Sector Management

## Capability Overview

This capability manages the flash sector lifecycle for the Key-Value Database. It handles sector formatting (erase + write magic header), sector info reading (magic validation, remaining space calculation, KV traversal), sector status transitions (EMPTY -> USING -> FULL), dirty status tracking, KV space allocation within sectors, and sector iteration. A sector cache stores recently accessed sector info for fast repeated access.

## Key Functions

| C Function | C File:Line | Rust Equivalent | Behavior Summary |
|------------|-------------|-----------------|------------------|
| `format_sector` | `src/fdb_kvdb.c:769` | `fn format_sector(kvdb: &mut FdbKvdb, addr: u32, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Erase sector and write sector header with magic word and initial status |
| `read_sector_info` | `src/fdb_kvdb.c:416` | `fn read_sector_info(kvdb: &FdbKvdb, sec: &mut KvdbSecInfo, flash: &dyn FlashStorage) -> Result<(), FdbError>` | Read sector header, validate magic, compute remaining space and empty KV address |
| `update_sec_status` | `src/fdb_kvdb.c:829` | `fn update_sec_status(kvdb: &mut FdbKvdb, sec: &mut KvdbSecInfo, new_status: FdbSectorStoreStatus, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Transition sector store status via status table (EMPTY -> USING -> FULL) |
| `get_next_sector_addr` | `src/fdb_kvdb.c:504` | `fn get_next_sector_addr(kvdb: &FdbKvdb, cur_addr: u32) -> u32` | Calculate next sector address, wrapping at DB boundary |
| `alloc_kv` | `src/fdb_kvdb.c:915` | `fn alloc_kv(kvdb: &mut FdbKvdb, size: usize, flash: &mut dyn FlashStorage) -> Result<u32, FdbError>` | Find a sector with enough space for a new KV, return allocated address |
| `new_kv` / `new_kv_ex` | `src/fdb_kvdb.c:1069, 1091` | `fn new_kv(kvdb: &mut FdbKvdb, size: usize, flash: &mut dyn FlashStorage) -> Result<u32, FdbError>`, `fn new_kv_ex(kvdb: &mut FdbKvdb, kv_len: u32, value_len: u32, flash: &mut dyn FlashStorage) -> Result<u32, FdbError>` | Allocate KV space; trigger GC if no space available |
| `sector_iterator` | `src/fdb_kvdb.c:863` | `fn sector_iterator(kvdb: &FdbKvdb, cb: fn(&FdbKvdb, u32) -> bool, flash: &dyn FlashStorage)` | Iterate over all sectors, calling callback for each valid sector header |

## Data Structures

| C Struct | Fields | Rust Equivalent | Notes |
|----------|--------|----------------|-------|
| `kvdb_sec_info` | `check_ok`, `status.store`, `status.dirty`, `addr`, `magic`, `combined`, `remain`, `empty_kv` | `KvdbSecInfo { check_ok: bool, store_status: FdbSectorStoreStatus, dirty_status: FdbSectorDirtyStatus, addr: u32, magic: u32, combined: u32, remain: usize, empty_kv: u32 }` | `#[repr(C)]` for byte-buffer deserialization |

## Requirements

### REQ-kvdb-sector-management-001: format_sector SHALL erase then write the magic header

C source reference: `src/fdb_kvdb.c:769`

Scenario (normal path):
  GIVEN a sector at flash address 0x1000 with `sec_size=4096`
  WHEN `format_sector(&mut kvdb, 0x1000, &mut flash)` is called
  THEN the sector SHALL be erased (all bytes set to 0xFF), then a sector header with magic word `0x30424446` ("FDB1") SHALL be written at the start, and the function SHALL return `Ok(())`

Scenario (error path):
  GIVEN a flash erase failure during `format_sector`
  WHEN `fdb_flash_erase` returns an error
  THEN the function SHALL propagate the error as `Err(FdbError::EraseErr)` without writing the header

Scenario (boundary condition):
  GIVEN a sector address at the highest boundary of the database
  WHEN `format_sector` computes the next empty address
  THEN it SHALL remain within `max_size` boundary

### REQ-kvdb-sector-management-002: read_sector_info SHALL validate magic word and compute space

C source reference: `src/fdb_kvdb.c:416`

Scenario (normal path):
  GIVEN a sector with valid magic word `0x30424446` at address 0x1000
  WHEN `read_sector_info(&kvdb, &mut sec, &flash)` is called
  THEN `sec.check_ok` SHALL be `true`, `sec.magic` SHALL be `0x30424446`, and `sec.remain`/`sec.empty_kv` SHALL be computed from the sector's KV contents

Scenario (error path):
  GIVEN a sector with incorrect magic word (e.g., all 0xFF, never formatted)
  WHEN `read_sector_info` is called
  THEN `sec.check_ok` SHALL be `false`, and the caller SHALL treat the sector as invalid/unformatted

Scenario (boundary condition):
  GIVEN a sector with `combined` value that is neither `SECTOR_NOT_COMBINED (0xFFFFFFFF)` nor `SECTOR_COMBINED (0x00000000)`
  WHEN `read_sector_info` checks the combined value
  THEN `sec.check_ok` SHALL be `false` (invalid sector header)

### REQ-kvdb-sector-management-003: update_sec_status SHALL transition status monotonically

C source reference: `src/fdb_kvdb.c:829`

Scenario (normal path):
  GIVEN a sector currently in `EMPTY` status
  WHEN `update_sec_status` transitions it to `USING`
  THEN the sector store status status table SHALL be updated via `fdb_write_status`, and `sec.store_status` SHALL become `Using`

Scenario (error path):
  GIVEN a flash write failure during status update
  WHEN `fdb_write_status` returns an error
  THEN the function SHALL propagate the error -- the status SHALL NOT be half-updated

Scenario (boundary condition):
  GIVEN a sector already at `FULL` status
  WHEN `update_sec_status` is called with `FULL` again (no transition needed)
  THEN the function SHALL return `Ok(())` without any flash write

### REQ-kvdb-sector-management-004: alloc_kv SHALL find a USING sector with enough remaining space

C source reference: `src/fdb_kvdb.c:915`

Scenario (normal path):
  GIVEN a database with sectors at `EMPTY`, `USING (500 bytes remain)`, and `FULL`
  WHEN `alloc_kv(&mut kvdb, 200, &mut flash)` is called
  THEN the function SHALL find the `USING` sector with 500 bytes remaining, return its `empty_kv` address, and decrement `remain` by 200

Scenario (error path):
  GIVEN all sectors are FULL and no empty sector is available for formatting
  WHEN `alloc_kv` searches for space
  THEN the function SHALL return `Err(FdbError::SavedFull)` and set `gc_request = true`

Scenario (boundary condition):
  GIVEN `size == remain` of a USING sector (exact fit for the last KV)
  WHEN `alloc_kv` is called
  THEN the KV SHALL be allocated, `remain` SHALL become 0, and the sector SHALL be marked `FULL`

## Invariants

- **INV-kvdb-sector-management-001**: Sector status SHALL only transition EMPTY -> USING -> FULL. Reverse transitions SHALL NOT occur (status tables are monotonic).
- **INV-kvdb-sector-management-002**: `sector->empty_kv` SHALL always point to the first byte after all valid KVs in the sector, and `sector->remain = sec_size - (empty_kv - sector->addr)`.
- **INV-kvdb-sector-management-003**: At least 1 sector SHALL always be empty (EMPTY or erased) to serve as GC target. The database requires `>= 2` sectors.
- **INV-kvdb-sector-management-004**: Every formatted sector SHALL begin with a 12-byte header containing the magic word `0x30424446` and sector status tables.

## Dependencies

- `foundational-types` -- Uses `FdbKvdb`, `KvdbSecInfo`, `FdbSectorStoreStatus`, `FdbSectorDirtyStatus`, `FdbError`.
- `flash-io-dispatch` -- All sector I/O (erase, read header, write header, write status) goes through `FlashStorage` trait.
- `flash-status-table` -- Sector store status and dirty status are maintained via status tables.
- `database-lifecycle` -- Sector operations require `init_ok == true`.
