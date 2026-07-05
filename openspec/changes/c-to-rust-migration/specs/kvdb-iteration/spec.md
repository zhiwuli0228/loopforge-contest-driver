# Spec: KVDB Iteration

## Capability Overview

This capability provides iterator APIs for enumerating all valid key-value pairs in the database. It supports external iteration via the init/iterate pattern (returning one KV at a time) and internal callback-based iteration used by find, print, and GC operations. It tracks iteration statistics including total count, object bytes, and value bytes.

## Key Functions

| C Function | C File:Line | Rust Equivalent | Behavior Summary |
|------------|-------------|-----------------|------------------|
| `fdb_kv_iterator_init` | `src/fdb_kvdb.c:1488` | `fn fdb_kv_iterator_init(kvdb: &FdbKvdb) -> FdbKvIterator` | Initialize an iterator starting at the oldest sector address |
| `fdb_kv_iterate` | `src/fdb_kvdb.c:1504` | `fn fdb_kv_iterate(kvdb: &FdbKvdb, itr: &mut FdbKvIterator, flash: &dyn FlashStorage) -> bool` | Advance the iterator to the next valid KV; returns false when done |
| `fdb_kv_print` | `src/fdb_kvdb.c:1558` | `fn fdb_kv_print(kvdb: &FdbKvdb)` | Print all KV entries (debug/diagnostic) |
| `kv_iterator` | `src/fdb_kvdb.c:1468` | `fn kv_iterator(kvdb: &FdbKvdb, cb: fn(&FdbKv, &FdbBlob) -> bool, flash: &dyn FlashStorage)` | Internal: iterate all KVs with a callback |
| `find_kv_no_cache` | `src/fdb_kvdb.c:576` | `fn find_kv_no_cache(kvdb: &FdbKvdb, key: &str, kv: &mut FdbKv, flash: &dyn FlashStorage) -> bool` | Internal: find KV by name without using cache (linear scan) |

## Data Structures

| C Struct | Fields | Rust Equivalent | Notes |
|----------|--------|----------------|-------|
| `fdb_kv_iterator` | `curr_kv`, `iterated_cnt`, `iterated_obj_bytes`, `iterated_value_bytes`, `sector_addr`, `traversed_len` | `FdbKvIterator { curr_kv: FdbKv, iterated_cnt: u32, iterated_obj_bytes: usize, iterated_value_bytes: usize, sector_addr: u32, traversed_len: u32 }` | Stateful iterator struct |

## Requirements

### REQ-kvdb-iteration-001: fdb_kv_iterator_init SHALL start at the oldest sector

C source reference: `src/fdb_kvdb.c:1488`

Scenario (normal path):
  GIVEN an initialized KVDB with `oldest_addr=0x1000`
  WHEN `fdb_kv_iterator_init(&kvdb)` is called
  THEN the returned iterator SHALL have `sector_addr=0x1000`, `iterated_cnt=0`, and all `curr_kv` fields SHALL be default (Unused)

Scenario (error path):
  N/A -- Initialization cannot fail; it creates a zeroed/default iterator struct.

Scenario (boundary condition):
  GIVEN `oldest_addr` is 0 (database has no valid data)
  WHEN `fdb_kv_iterator_init` is called
  THEN `sector_addr` SHALL be 0, and the first call to `fdb_kv_iterate` SHALL return false

### REQ-kvdb-iteration-002: fdb_kv_iterate SHALL traverse all sectors and return KVs in address order

C source reference: `src/fdb_kvdb.c:1504`

Scenario (normal path):
  GIVEN a database with 3 KVs across 2 sectors
  WHEN `fdb_kv_iterate` is called repeatedly
  THEN each call SHALL return one KV in address order, `iterated_cnt` SHALL increment, and the final call SHALL return false when no more KVs exist

Scenario (error path):
  GIVEN a sector with corrupted header (magic mismatch)
  WHEN `fdb_kv_iterate` encounters the bad sector during `read_sector_info`
  THEN the iterator SHALL skip the bad sector and continue to the next one

Scenario (boundary condition):
  GIVEN an empty database (no valid KVs, all sectors empty or unformatted)
  WHEN `fdb_kv_iterate` is first called
  THEN the function SHALL return false immediately, and `iterated_cnt` SHALL be 0

### REQ-kvdb-iteration-003: kv_iterator SHALL skip KVs with DELETED or ERR_HDR status

C source reference: `src/fdb_kvdb.c:1468`

Scenario (normal path):
  GIVEN a sector containing KVs with statuses WRITE, DELETED, and WRITE
  WHEN `kv_iterator` traverses the sector
  THEN only the two WRITE-status KVs SHALL be passed to the callback; the DELETED KV SHALL be skipped

Scenario (error path):
  GIVEN a KV with ERR_HDR status (corrupted header)
  WHEN `kv_iterator` encounters it
  THEN the KV SHALL be skipped (not passed to callback), and iteration SHALL continue to the next KV

Scenario (boundary condition):
  GIVEN a sector containing only DELETED/ERR_HDR KVs (no valid data)
  WHEN `kv_iterator` traverses the sector
  THEN no callback invocations SHALL occur for that sector, and `iterated_cnt` SHALL NOT increase

### REQ-kvdb-iteration-004: find_kv_no_cache SHALL match KV by name via byte comparison

C source reference: `src/fdb_kvdb.c:576`

Scenario (normal path):
  GIVEN a database with KV "alpha" at address 0x1100
  WHEN `find_kv_no_cache(&kvdb, "alpha", &mut kv, &flash)` is called
  THEN the function SHALL iterate all sectors, find the KV with matching name bytes, populate `kv` with the KV metadata, and return `true`

Scenario (error path):
  GIVEN a key "gamma" that does not exist in any sector
  WHEN `find_kv_no_cache` scans all sectors
  THEN the function SHALL return `false` without populating `kv`

Scenario (boundary condition):
  GIVEN two KVs with the same name (should not normally happen, but possible after crash)
  WHEN `find_kv_no_cache` scans
  THEN the first match in address order SHALL be returned; the duplicate in a later sector SHALL be ignored

## Invariants

- **INV-kvdb-iteration-001**: Forward iteration SHALL proceed in address order from `oldest_addr` to `max_size`, wrapping if needed. Within each sector, KVs SHALL be visited in address order from sector top (after header) downward.
- **INV-kvdb-iteration-002**: KVs with status `DELETED`, `ERR_HDR`, or `UNUSED` SHALL be skipped during iteration. Only `PRE_WRITE` and `WRITE` KVs may be returned (PRE_WRITE KVs represent an interrupted write).
- **INV-kvdb-iteration-003**: `iterated_obj_bytes` and `iterated_value_bytes` SHALL track the cumulative size of all KV headers+names and values, respectively, for all KVs iterated.
- **INV-kvdb-iteration-004**: The iterator SHALL NOT cache KV data between `fdb_kv_iterate` calls. Each call re-reads the current position and advances.

## Dependencies

- `foundational-types` -- Uses `FdbKvdb`, `FdbKv`, `FdbKvIterator`, `FdbKvStatus`, `FdbBlob`.
- `flash-io-dispatch` -- Flash reads for sector headers and KV data.
- `kvdb-sector-management` -- `read_sector_info` for sector header validation and space computation.
- `kv-crud` -- `get_kv` for reading KV value data at a given address.
