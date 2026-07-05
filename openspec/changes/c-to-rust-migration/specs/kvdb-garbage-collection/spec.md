# Spec: KVDB Garbage Collection

## Capability Overview

This capability implements automatic garbage collection to reclaim flash space occupied by deleted KVs. GC is triggered when space allocation fails or a sector becomes full. The multi-pass algorithm: iterates dirty sectors, moves valid (live) KVs to a new location, and formats the old sector. GC supports crash recovery by resuming interrupted GC when a `DIRTY_GC` sector is detected on init.

## Key Functions

| C Function | C File:Line | Rust Equivalent | Behavior Summary |
|------------|-------------|-----------------|------------------|
| `gc_collect` | `src/fdb_kvdb.c:1178` | `fn gc_collect(kvdb: &mut FdbKvdb, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Trigger GC: collect dirty sectors to reclaim space |
| `gc_collect_by_free_size` | `src/fdb_kvdb.c:1153` | `fn gc_collect_by_free_size(kvdb: &mut FdbKvdb, size: usize, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | GC with target: collect until enough free space is available |
| `do_gc` | `src/fdb_kvdb.c:1112` | `fn do_gc(kvdb: &mut FdbKvdb, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Core GC logic: scan dirty sectors, move valid KVs to new sector, format old |
| `move_kv` | `src/fdb_kvdb.c:1006` | `fn move_kv(kvdb: &mut FdbKvdb, from_addr: u32, to_addr: u32, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Move a single KV from one flash address to another |
| `gc_check_cb` | `src/fdb_kvdb.c:1098` | `fn gc_check_cb(kvdb: &FdbKvdb, addr: u32, flash: &dyn FlashStorage) -> bool` | Callback: count empty sectors to determine if GC is needed |

## Data Structures

| C Struct | Fields | Rust Equivalent | Notes |
|----------|--------|----------------|-------|
| `gc_cb_args` | (in-code struct) | (inline or closure-based) | Internal struct tracking moved KV count and space freed during GC |

## Requirements

### REQ-kvdb-garbage-collection-001: do_gc SHALL iterate dirty sectors and move valid KVs

C source reference: `src/fdb_kvdb.c:1112`

Scenario (normal path):
  GIVEN a database with 3 sectors: S0 (USING, DIRTY_TRUE, 2 valid KVs + 1 deleted KV), S1 (USING), S2 (EMPTY)
  WHEN `do_gc` is called on S0
  THEN the 2 valid KVs SHALL be moved to another sector (S1 or S2), S0 SHALL be formatted (erased + new header), and S0's dirty status SHALL be set to DIRTY_FALSE

Scenario (error path):
  GIVEN a flash write failure during `move_kv` (moving a valid KV)
  WHEN `do_gc` encounters the error
  THEN the function SHALL return the error -- the source sector SHALL remain with DIRTY_GC status (indicating interrupted GC), enabling crash recovery on next init

Scenario (boundary condition):
  GIVEN a sector with ALL KVs deleted (no valid KVs to move)
  WHEN `do_gc` processes the sector
  THEN no KVs SHALL be moved, the sector SHALL be formatted directly, and dirty status SHALL be set to DIRTY_FALSE

### REQ-kvdb-garbage-collection-002: gc_collect_by_free_size SHALL collect until target free size is met

C source reference: `src/fdb_kvdb.c:1153`

Scenario (normal path):
  GIVEN a database where freed space is 200 bytes and the target is 500 bytes
  WHEN `gc_collect_by_free_size(&mut kvdb, 500, &mut flash)` is called
  THEN `do_gc` SHALL be called repeatedly on dirty sectors until freed space >= 500 bytes, or no more dirty sectors remain

Scenario (error path):
  GIVEN GC fails partway through (flash write error)
  WHEN `do_gc` returns an error
  THEN `gc_collect_by_free_size` SHALL propagate the error immediately

Scenario (boundary condition):
  GIVEN no dirty sectors exist (all sectors are DIRTY_FALSE or UNUSED)
  WHEN `gc_collect_by_free_size` is called
  THEN the function SHALL return `Ok(())` immediately (nothing to collect)

### REQ-kvdb-garbage-collection-003: move_kv SHALL read KV from old address and write to new address

C source reference: `src/fdb_kvdb.c:1006`

Scenario (normal path):
  GIVEN a valid KV at flash address 0x1100 with name "data" and blob value of 64 bytes
  WHEN `move_kv(&mut kvdb, 0x1100, new_addr, &mut flash)` is called
  THEN the KV SHALL be read from 0x1100, written to `new_addr` with identical header and CRC32, and the old KV at 0x1100 SHALL be marked DELETED

Scenario (error path):
  GIVEN a CRC mismatch when reading the KV from the old address
  WHEN `move_kv` reads and validates the KV
  THEN the KV SHALL be skipped (not moved), and the corrupted KV SHALL be left in place

Scenario (boundary condition):
  GIVEN `old_addr == new_addr` (should not happen normally)
  WHEN `move_kv` is called
  THEN the function SHALL return `Ok(())` as a no-op

### REQ-kvdb-garbage-collection-004: GC SHALL handle interrupted GC recovery

C source reference: `src/fdb_kvdb.c:1112` (DIRTY_GC detection)

Scenario (normal path):
  GIVEN a clean shutdown -- GC completed fully
  WHEN the database is re-initialized
  THEN no sector SHALL have `DIRTY_GC` status -- no GC recovery needed

Scenario (error path):
  GIVEN a crash during GC left sector S1 with `DIRTY_GC` status
  WHEN the database is re-initialized and recovery runs
  THEN `check_and_recovery_gc_cb` SHALL detect `DIRTY_GC`, and `do_gc` SHALL resume moving valid KVs from S1

Scenario (boundary condition):
  GIVEN a sector marked `DIRTY_GC` but all its KVs have already been moved (GC completed but status not updated)
  WHEN recovery runs
  THEN the sector SHALL be formatted (since no valid KVs remain), and `DIRTY_GC` SHALL be cleared

## Invariants

- **INV-kvdb-garbage-collection-001**: During GC, the source sector SHALL be marked `DIRTY_GC` BEFORE any KVs are moved. This ensures crash recovery can detect interrupted GC.
- **INV-kvdb-garbage-collection-002**: GC SHALL NOT modify the source sector until all valid KVs have been successfully moved to their new locations.
- **INV-kvdb-garbage-collection-003**: After successful GC, the source sector SHALL be fully formatted (erased + new header), with `store_status=EMPTY` and `dirty_status=DIRTY_FALSE`.
- **INV-kvdb-garbage-collection-004**: GC SHALL preserve KV data integrity: moved KVs SHALL have identical name, value, CRC32, and status as the originals.

## Dependencies

- `kvdb-sector-management` -- `format_sector`, `read_sector_info`, `update_sec_status`, `alloc_kv`, `new_kv`.
- `kv-crud` -- `move_kv` uses `get_kv`, `create_kv_blob`, `del_kv`.
- `kvdb-iteration` -- `kv_iterator` for scanning valid KVs in dirty sectors.
