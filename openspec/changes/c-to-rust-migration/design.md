# Design: C-to-Rust Migration for FlashDB

## Context

FlashDB is an ultra-lightweight embedded key-value (KV) and time-series log (TSL) database for microcontrollers, written in C (Apache-2.0 license). It operates on raw flash/partition storage (FAL mode) or flat files (FILE mode), using sector-based storage with garbage collection, wear-leveling via status tables, and CRC32 integrity checks.

### Source Inventory Summary

| File | Lines | Purpose |
|------|-------|---------|
| `inc/flashdb.h` | 79 | Public API (30 function declarations) |
| `inc/fdb_def.h` | 351 | Core types: structs, enums, error codes, control commands |
| `inc/fdb_low_lvl.h` | 71 | Internal macros: alignment, status table sizing, sentinels |
| `inc/fdb_cfg_template.h` | 56 | Compile-time feature flags and write granularity |
| `src/fdb.c` | 157 | Init/deinit lifecycle, path resolution, init-finish logging |
| `src/fdb_kvdb.c` | 1,944 | KVDB engine: sectors, CRUD, cache, GC, iterator, recovery |
| `src/fdb_tsdb.c` | 1,095 | TSDB engine: TSL append, iter, time-range query, cleanup |
| `src/fdb_file.c` | 317 | File-mode I/O backend (POSIX + LIBC variants) |
| `src/fdb_utils.c` | 348 | CRC32, status-table ops, flash dispatch, blob abstraction |
| `tests/fdb_kvdb_tc.c` | 979 | 13 KVDB test functions + helpers |
| `tests/fdb_tsdb_tc.c` | 518 | 11 TSDB test functions + helpers |
| **Total** | **~5,915** | 5 source files, 4 headers, 2 test files, 151 functions (incl. declarations) |

### Key Architectural Patterns

1. **Status tables**: Write-once state machines encoded as bit/byte sequences in flash. `0xFF` (erased) represents unused; each state transition writes one additional byte to `0x00` (written). Encoding depends on `FDB_WRITE_GRAN` (1, 8, 32, 64, 128, or 256 bits). Used for sector store status (4 states), sector dirty status (4 states), KV status (6 states), and TSL status (6 states).

2. **C struct "inheritance"**: `fdb_kvdb` and `fdb_tsdb` embed `fdb_db` as their first member (`parent`), enabling polymorphic init/deinit. The `fdb_db` base holds name, type, storage union (FAL partition or directory path), sector size, init flag, and file cache arrays.

3. **Sector-based storage**: Storage divided into fixed-size sectors (power of 2). Each sector has a 12-byte header with magic word, sector status, dirty status, and combined/next info. KVDB sectors track remaining space and next empty address. TSDB sectors track start/end timestamps with dual end-info slots for crash resilience.

4. **Garbage collection (GC)**: Multi-pass algorithm. When free sectors are exhausted, dirty sectors are scanned; live KVs are moved to a new sector; old sector is erased and reformatted. Triggered by `gc_request` flag after KV writes fill a sector. Handles crash recovery for interrupted GC (DIRTY_GC status).

5. **KV cache**: LRU-like cache using name CRC16 hashing and activity counters. Speeds up repeated KV lookups without scanning all sectors.

6. **Flash I/O dispatch**: `_fdb_flash_read/write/erase` dispatch to FAL partition calls or file-based I/O (POSIX `open/read/write/lseek/fsync` or LIBC `fopen/fread/fwrite/fflush`) depending on compile-time flags.

7. **File descriptor caching**: A small LRU cache (2 slots by default) maps sector addresses to open file descriptors, reducing open/close overhead in file mode.

8. **Conditional compilation**: Heavy use of `#ifdef` for feature selection: `FDB_USING_FAL_MODE`, `FDB_USING_FILE_MODE`, `FDB_USING_FILE_POSIX_MODE`, `FDB_USING_FILE_LIBC_MODE`, `FDB_KV_USING_CACHE`, `FDB_KV_AUTO_UPDATE`, `FDB_TSDB_FIXED_BLOB_SIZE`, `FDB_USING_TIMESTAMP_64BIT`.

### Existing Rust Project State

A skeleton Rust crate exists at `work/output/flashDB_rust/` with:
- Module structure matching C files (`fdb.rs`, `fdb_kvdb.rs`, `fdb_tsdb.rs`, `fdb_file.rs`, `fdb_utils.rs`, plus `fdb_def.rs`, `fdb_low_lvl.rs`, `fdb_cfg_template.rs`, `flashdb.rs`, `ports.rs`)
- Type definitions: `FdbError`, `FdbKvStatus`, `FdbTslStatus`, `FdbSectorStoreStatus`, `FdbSectorDirtyStatus`, `FdbDbType`, `FdbKv`, `FdbKvIterator`, `FdbTsl`, `FdbBlob`, `FdbDb`, `FdbKvdb`, `FdbTsdb`, `KvdbSecInfo`, `TsdbSecInfo`, `KvCacheNode`
- `FlashStorage` trait with `RamFlash` implementation for testing
- CRC32 implementation (functional)
- Status table utilities (partial, needs completion)
- Stub API functions (return `Ok(())` or `None`, need full implementation)
- Basic init/deinit with validation
- 13 compiled tests covering CRC32, blob, flash ops, init/deinit edge cases

## Goals

1. **Complete semantic equivalence**: Every public API function from `flashdb.h` (30 functions) produces identical observable behavior to the C implementation for all valid inputs.

2. **Algorithm preservation**: All core algorithms must be preserved exactly:
   - Status-table state machines for all 6 write-granularity variants
   - Sector header read/write with magic validation
   - KV create/read/update/delete with 2-phase delete (PRE_DELETE -> DELETED)
   - CRC32 integrity checking on every KV read
   - Multi-pass GC algorithm (dirty scan -> move -> erase -> reformat)
   - KV cache with LRU-like eviction
   - TSL append with sector rollover and dual end-info crash resilience
   - Time-range iteration with binary search optimization
   - Iterator patterns for KV and TSL (forward, reverse, by-time)
   - Crash recovery for interrupted writes, deletes, and GC

3. **Test preservation**: All 24 C test functions (13 KVDB + 11 TSDB) plus helpers must be migrated to Rust `#[test]` functions that test the same scenarios with equivalent assertions.

4. **Safe Rust preference**: Maximum 10% of total lines may use `unsafe`. Unsafe blocks must be isolated, documented, and justified.

5. **Build and test**: `cargo build` and `cargo test` must both succeed on the target platform (Windows/Linux x86_64 with POSIX file I/O).

6. **Trait-based storage abstraction**: A `FlashStorage` trait enables FILE_MODE for tests and pluggable backends for embedded targets.

## Non-Goals

1. **No FAL support**: The FAL (Flash Abstraction Layer) partition mode is not implemented. Only FILE_MODE (POSIX) is supported in the initial migration.
2. **No embedded hardware**: No STM32, ESP32, or other MCU BSP/HAL driver support.
3. **No demo applications**: Demo programs (esp32, esp8266, stm32, linux demos) are not ported.
4. **No `FDB_KV_AUTO_UPDATE`**: Version-based auto-update feature is deferred.
5. **No `FDB_TSDB_FIXED_BLOB_SIZE`**: Fixed blob size feature (changes on-flash format) is deferred.
6. **No `FDB_USING_FILE_LIBC_MODE`**: Only POSIX file mode (`open/read/write/lseek/close`) is implemented.
7. **No performance parity**: Rust heap allocations are acceptable; embedded memory optimization is not a goal.
8. **No C ABI compatibility**: The Rust API does not need to match the C ABI for FFI interop.
9. **No RT-Thread framework**: Tests use Rust's native `#[test]` framework, not RT-Thread Utest.

## Capability Mapping

Every capability from the Phase 1 capability map is listed below with its implementation plan.

| Capability ID | Name | Priority | C Source Files | Rust Target Module(s) | Key Functions | Dependencies |
|--------------|------|----------|----------------|----------------------|---------------|--------------|
| foundational-types | Foundational Data Types and Constants | P0 | `fdb_def.h`, `fdb_low_lvl.h`, `fdb_cfg_template.h` | `fdb_def.rs`, `fdb_low_lvl.rs`, `fdb_cfg_template.rs` | (types only, no functions) | (none) |
| crc32-computation | CRC32 Checksum Computation | P0 | `fdb_utils.c` | `fdb_utils.rs` | `fdb_calc_crc32` | (none) |
| flash-status-table | Flash Status Table Management | P0 | `fdb_utils.c` | `fdb_utils.rs` | `_fdb_set_status`, `_fdb_get_status`, `_fdb_write_status`, `_fdb_read_status`, `_fdb_continue_ff_addr` | foundational-types |
| blob-abstraction | Blob Data Abstraction | P0 | `fdb_utils.c` | `fdb_utils.rs` | `fdb_blob_make`, `fdb_blob_read` | foundational-types |
| flash-io-dispatch | Flash I/O Dispatch Layer | P0 | `fdb_utils.c` | `fdb_utils.rs`, `ports.rs` | `_fdb_flash_read`, `_fdb_flash_write`, `_fdb_flash_erase`, `_fdb_flash_write_align` | foundational-types, file-storage-backend |
| file-storage-backend | File-based Storage Backend | P0 | `fdb_file.c` | `fdb_file.rs` | `get_db_file_path`, `open_db_file`, `_fdb_file_read`, `_fdb_file_write`, `_fdb_file_erase`, `get_file_from_cache`, `update_file_cache` | foundational-types |
| database-lifecycle | Database Lifecycle Management | P1 | `fdb.c` | `fdb.rs` | `_fdb_init_ex`, `_fdb_init_finish`, `_fdb_deinit`, `_fdb_db_path` | foundational-types, flash-io-dispatch |
| kv-crud | KV CRUD Operations | P1 | `fdb_kvdb.c` | `fdb_kvdb.rs` | `fdb_kv_set`, `fdb_kv_get`, `fdb_kv_set_blob`, `fdb_kv_get_blob`, `fdb_kv_del`, `fdb_kv_get_obj`, `fdb_kv_to_blob`, `fdb_kv_set_default`, `set_kv`, `get_kv`, `create_kv_blob`, `find_kv`, `del_kv`, `write_kv_hdr` | foundational-types, flash-io-dispatch, flash-status-table, crc32-computation, blob-abstraction, database-lifecycle, kvdb-sector-management |
| kvdb-sector-management | KVDB Sector Management | P1 | `fdb_kvdb.c` | `fdb_kvdb.rs` | `format_sector`, `read_sector_info`, `update_sec_status`, `get_next_sector_addr`, `alloc_kv`, `new_kv`, `new_kv_ex`, `sector_iterator`, `find_next_kv_addr`, `get_next_kv_addr` | foundational-types, flash-io-dispatch, flash-status-table, database-lifecycle |
| kvdb-iteration | KVDB Iteration | P1 | `fdb_kvdb.c` | `fdb_kvdb.rs` | `fdb_kv_iterator_init`, `fdb_kv_iterate`, `fdb_kv_print`, `kv_iterator`, `find_kv_no_cache` | foundational-types, flash-io-dispatch, kvdb-sector-management, kv-crud |
| kvdb-garbage-collection | KVDB Garbage Collection | P2 | `fdb_kvdb.c` | `fdb_kvdb.rs` | `gc_collect`, `gc_collect_by_free_size`, `do_gc`, `move_kv`, `gc_check_cb` | kvdb-sector-management, kv-crud, kvdb-iteration |
| kvdb-recovery | KVDB Crash Recovery and Integrity | P2 | `fdb_kvdb.c` | `fdb_kvdb.rs` | `_fdb_kv_load`, `fdb_kvdb_check`, `fdb_kvdb_init`, `fdb_kvdb_deinit`, `fdb_kvdb_control`, `check_and_recovery_kv_cb`, `check_and_recovery_gc_cb`, `check_sec_hdr_cb`, `kv_auto_update` | kvdb-sector-management, kv-crud, kvdb-garbage-collection, kvdb-iteration |
| tsl-append | TSL Append and Storage | P1 | `fdb_tsdb.c` | `fdb_tsdb.rs` | `fdb_tsl_append`, `fdb_tsl_append_with_ts`, `tsl_append`, `write_tsl`, `read_tsl`, `update_sec_status` | foundational-types, flash-io-dispatch, flash-status-table, blob-abstraction, database-lifecycle, tsdb-sector-layout |
| tsl-iteration-query | TSL Iteration and Query | P1 | `fdb_tsdb.c` | `fdb_tsdb.rs` | `fdb_tsl_iter`, `fdb_tsl_iter_reverse`, `fdb_tsl_iter_by_time`, `fdb_tsl_query_count`, `search_start_tsl_addr`, `get_next_tsl_addr`, `get_last_tsl_addr` | foundational-types, flash-io-dispatch, tsdb-sector-layout |
| tsl-status-cleanup | TSL Status Management and Cleanup | P2 | `fdb_tsdb.c` | `fdb_tsdb.rs` | `fdb_tsl_set_status`, `fdb_tsl_clean`, `fdb_tsl_to_blob`, `fdb_tsdb_control`, `tsl_format_all` | tsl-append, tsdb-sector-layout |
| tsdb-sector-layout | TSDB Sector Layout and Initialization | P1 | `fdb_tsdb.c` | `fdb_tsdb.rs` | `fdb_tsdb_init`, `fdb_tsdb_deinit`, `read_sector_info`, `format_sector`, `check_sec_hdr_cb`, `sector_iterator`, `get_next_sector_addr`, `get_last_sector_addr` | foundational-types, flash-io-dispatch, flash-status-table, database-lifecycle |

### Dependency Graph (from capability map)

```
P0 Layer (no internal deps):
  foundational-types  crc32-computation
          |
  flash-status-table  blob-abstraction
          |                 |
  file-storage-backend -----+
          |
  flash-io-dispatch
          |
P1 Layer:
  database-lifecycle
          |
  kvdb-sector-management  tsdb-sector-layout
          |                      |
  kv-crud                        |
  kvdb-iteration          tsl-append
          |                      |
P2 Layer:                 tsl-iteration-query
  kvdb-garbage-collection       |
  kvdb-recovery           tsl-status-cleanup
```

## Module Mapping

### C Source File to Rust Module

```
C: src/fdb.c              ->  Rust: src/fdb.rs
C: src/fdb_kvdb.c         ->  Rust: src/fdb_kvdb.rs
C: src/fdb_tsdb.c         ->  Rust: src/fdb_tsdb.rs
C: src/fdb_file.c         ->  Rust: src/fdb_file.rs
C: src/fdb_utils.c        ->  Rust: src/fdb_utils.rs
C: inc/flashdb.h          ->  Rust: src/flashdb.rs (re-exports)
C: inc/fdb_def.h          ->  Rust: src/fdb_def.rs (types + enums)
C: inc/fdb_low_lvl.h      ->  Rust: src/fdb_low_lvl.rs (constants + alignment fns)
C: inc/fdb_cfg_template.h ->  Rust: src/fdb_cfg_template.rs (feature flags)
C: (no C equivalent)      ->  Rust: src/ports.rs (FlashStorage trait + RamFlash)
C: (no C equivalent)      ->  Rust: src/lib.rs (module declarations)
```

### Crate Layout

```
flashdb_rust/
  Cargo.toml
  src/
    lib.rs              -- Module declarations, crate root
    fdb_def.rs          -- Core types, enums, structs (from fdb_def.h)
    fdb_low_lvl.rs      -- Alignment macros as const fns, sentinel constants
    fdb_cfg_template.rs -- Feature flags, write granularity, version
    fdb.rs              -- Init/deinit lifecycle, path resolution (from fdb.c)
    fdb_kvdb.rs         -- KVDB engine (from fdb_kvdb.c)
    fdb_tsdb.rs         -- TSDB engine (from fdb_tsdb.c)
    fdb_file.rs         -- File-mode I/O with fd cache (from fdb_file.c)
    fdb_utils.rs        -- CRC32, status tables, flash dispatch, blob (from fdb_utils.c)
    flashdb.rs          -- Public re-exports matching flashdb.h API surface
    ports.rs            -- FlashStorage trait, RamFlash test implementation
  tests/
    kvdb_tests.rs       -- Migrated from tests/fdb_kvdb_tc.c
    tsdb_tests.rs       -- Migrated from tests/fdb_tsdb_tc.c
```

### Rationale

A single `lib` crate with modules is chosen over a workspace of multiple crates because:
- The C codebase (~4,400 lines) is small enough that module-level separation is sufficient
- Core types (`fdb_db`, `fdb_kv`, etc.) are shared between KVDB, TSDB, and utils -- a workspace would require a separate types crate or complex `pub use` chains
- The C code already freely intermixes module calls; a monolithic crate mirrors the existing dependency structure
- `#[cfg(test)]` can gate test-only helpers and integration tests naturally

## Type Mapping

### Enums (C enum -> Rust enum)

```
C: typedef enum { FDB_NO_ERR=0, FDB_ERASE_ERR, ... } fdb_err_t
  -> Rust: #[derive(Debug, Clone, Copy, PartialEq, Eq)] pub enum FdbError { NoErr=0, EraseErr, ... }

C: enum fdb_kv_status { FDB_KV_UNUSED, FDB_KV_PRE_WRITE, FDB_KV_WRITE, FDB_KV_PRE_DELETE, FDB_KV_DELETED, FDB_KV_ERR_HDR }
  -> Rust: #[derive(Debug, Clone, Copy, PartialEq, Eq, Default)] pub enum FdbKvStatus { Unused=0, PreWrite, Write, PreDelete, Deleted, ErrHdr }

C: enum fdb_tsl_status { FDB_TSL_UNUSED, FDB_TSL_PRE_WRITE, FDB_TSL_WRITE, FDB_TSL_USER_STATUS1, FDB_TSL_DELETED, FDB_TSL_USER_STATUS2 }
  -> Rust: #[derive(Debug, Clone, Copy, PartialEq, Eq, Default)] pub enum FdbTslStatus { Unused=0, PreWrite, Write, UserStatus1, Deleted, UserStatus2 }

C: enum fdb_sector_store_status { FDB_SECTOR_STORE_UNUSED, FDB_SECTOR_STORE_EMPTY, FDB_SECTOR_STORE_USING, FDB_SECTOR_STORE_FULL }
  -> Rust: #[derive(Debug, Clone, Copy, PartialEq, Eq, Default)] pub enum FdbSectorStoreStatus { Unused=0, Empty, Using, Full }

C: enum fdb_sector_dirty_status { FDB_SECTOR_DIRTY_UNUSED, FDB_SECTOR_DIRTY_FALSE, FDB_SECTOR_DIRTY_TRUE, FDB_SECTOR_DIRTY_GC }
  -> Rust: #[derive(Debug, Clone, Copy, PartialEq, Eq, Default)] pub enum FdbSectorDirtyStatus { Unused=0, False, True, Gc }

C: typedef enum { FDB_DB_TYPE_KV, FDB_DB_TYPE_TS } fdb_db_type
  -> Rust: #[derive(Debug, Clone, Copy, PartialEq, Eq)] pub enum FdbDbType { Kv=0, Ts }
```

### Structs (C struct -> Rust struct)

```
C: struct fdb_db { name, type, storage union, sec_size, max_size, oldest_addr, init_ok, file_mode, not_formatable, cur_file_sec[], cur_file[], lock/unlock fns, user_data }
  -> Rust: pub struct FdbDb { name: String, db_type: FdbDbType, storage_path: String, sec_size: u32, max_size: u32, oldest_addr: u32, init_ok: bool, file_mode: bool, not_formatable: bool, file_cache: FileCache, lock: Option<Box<dyn Fn()>>, unlock: Option<Box<dyn Fn()>>, user_data: usize }

C: struct fdb_kvdb { parent: fdb_db, default_kvs, gc_request, in_recovery_check, cur_kv, cur_sector, last_is_complete_del, kv_cache_table[], sector_cache_table[], ver_num, user_data }
  -> Rust: pub struct FdbKvdb { parent: FdbDb, default_kvs: FdbDefaultKv, gc_request: bool, in_recovery_check: bool, cur_kv: FdbKv, cur_sector: KvdbSecInfo, last_is_complete_del: bool, kv_cache_table: Vec<KvCacheNode>, sector_cache_table: Vec<KvdbSecInfo>, ver_num: u32, user_data: usize }

C: struct fdb_tsdb { parent: fdb_db, cur_sec, last_time, get_time fn, max_len, rollover, user_data }
  -> Rust: pub struct FdbTsdb { parent: FdbDb, cur_sec: TsdbSecInfo, last_time: FdbTime, get_time: Option<fn() -> FdbTime>, max_len: usize, rollover: bool, user_data: usize }

C: struct fdb_kv { status, crc_is_ok, name_len, magic, len, value_len, name[], addr.start, addr.value }
  -> Rust: pub struct FdbKv { status: FdbKvStatus, crc_is_ok: bool, name_len: u8, magic: u32, len: u32, value_len: u32, name: [u8; FDB_KV_NAME_MAX], addr_start: u32, addr_value: u32 }

C: struct fdb_tsl { status, time, log_len, addr.index, addr.log }
  -> Rust: pub struct FdbTsl { status: FdbTslStatus, time: FdbTime, log_len: u32, addr_index: u32, addr_log: u32 }

C: struct fdb_blob { buf, size, saved.meta_addr, saved.addr, saved.len }
  -> Rust: pub struct FdbBlob { buf: Vec<u8>, size: usize, saved_meta_addr: u32, saved_addr: u32, saved_len: usize }

C: struct fdb_kv_iterator { curr_kv, iterated_cnt, iterated_obj_bytes, iterated_value_bytes, sector_addr, traversed_len }
  -> Rust: pub struct FdbKvIterator { curr_kv: FdbKv, iterated_cnt: u32, iterated_obj_bytes: usize, iterated_value_bytes: usize, sector_addr: u32, traversed_len: u32 }

C: struct kvdb_sec_info { check_ok, status.store, status.dirty, addr, magic, combined, remain, empty_kv }
  -> Rust: pub struct KvdbSecInfo { check_ok: bool, store_status: FdbSectorStoreStatus, dirty_status: FdbSectorDirtyStatus, addr: u32, magic: u32, combined: u32, remain: usize, empty_kv: u32 }

C: struct tsdb_sec_info { check_ok, status, addr, magic, start_time, end_time, end_idx, end_info_stat[2], remain, empty_idx, empty_data }
  -> Rust: pub struct TsdbSecInfo { check_ok: bool, status: FdbSectorStoreStatus, addr: u32, magic: u32, start_time: FdbTime, end_time: FdbTime, end_idx: u32, end_info_stat: [FdbTslStatus; 2], remain: usize, empty_idx: u32, empty_data: u32 }

C: struct kv_cache_node { name_crc: u16, active: u16, addr: u32 }
  -> Rust: pub struct KvCacheNode { name_crc: u16, active: u16, addr: u32 }

C: struct fdb_default_kv { kvs: *fdb_default_kv_node, num: size_t }
  -> Rust: pub struct FdbDefaultKv { kvs: Vec<FdbDefaultKvNode>, num: usize }
```

### Scalar Type Mapping

```
C: fdb_time_t (int32_t or int64_t)  ->  Rust: FdbTime (i32 or i64, controlled by feature flag `timestamp-64bit`)
C: uint32_t                         ->  Rust: u32
C: uint16_t                         ->  Rust: u16
C: uint8_t                          ->  Rust: u8
C: size_t                           ->  Rust: usize
C: bool                             ->  Rust: bool
C: char*                            ->  Rust: String or &str
C: void*                            ->  Rust: usize (opaque user_data)
C: const char*                      ->  Rust: &str
```

### Key Design Decisions for Types

- **C struct "inheritance"**: `fdb_kvdb.parent` and `fdb_tsdb.parent` embed `FdbDb`. In Rust, this is a composition pattern (has-a, not is-a). Functions that take `fdb_db_t` in C take `&mut FdbDb` in Rust, requiring callers to pass `&mut kvdb.parent`.
- **Pointers to owned values**: C `typedef fdb_kv_t` (pointer to `fdb_kv`) becomes owned `FdbKv` struct in Rust. The C pattern of passing a pre-allocated struct to be filled in becomes a method that returns the struct.
- **Storage union**: C's tagged union (`storage.part` or `storage.dir`) becomes a `String` (`storage_path`) for file mode. FAL mode is not implemented.
- **Function pointers**: C's `void (*lock)(fdb_db_t)` and `void (*unlock)(fdb_db_t)` become `Option<Box<dyn Fn()>>` (or omitted for single-threaded use).
- **Get_time function**: C's `fdb_get_time` function pointer becomes `Option<fn() -> FdbTime>`.

## Error Strategy

### Error Enum

All fallible operations return `Result<T, FdbError>` where `FdbError` maps directly from the C error codes:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FdbError {
    NoErr = 0,          // FDB_NO_ERR
    EraseErr = 1,       // FDB_ERASE_ERR
    ReadErr = 2,        // FDB_READ_ERR
    WriteErr = 3,       // FDB_WRITE_ERR
    PartNotFound = 4,   // FDB_PART_NOT_FOUND
    KvNameErr = 5,      // FDB_KV_NAME_ERR
    KvNameExist = 6,    // FDB_KV_NAME_EXIST
    SavedFull = 7,      // FDB_SAVED_FULL
    InitFailed = 8,     // FDB_INIT_FAILED
}
```

### Mapping Rules

1. **C `fdb_err_t` return -> Rust `Result<(), FdbError>`**: Functions that return `fdb_err_t` (where 0 = success) map to `Result<(), FdbError>` with `Ok(())` for `FDB_NO_ERR` and `Err(e)` for all other values.

2. **C pointer return -> Rust `Option<T>`**: Functions that return pointers (`char*`, `fdb_kv_t`, `fdb_blob_t`) map to `Option<T>` where `NULL` becomes `None`.

3. **C `size_t` return (0 = error) -> Rust `Result<usize, FdbError>`**: Functions like `fdb_blob_read` and `fdb_kv_get_blob` that return 0 on failure map to `Result<usize, FdbError>`.

4. **C `bool` return -> Rust `bool`**: Callback-based search functions (`find_kv`, `gc_check_cb`) retain `bool`.

5. **C `FDB_ASSERT` macro -> Rust `assert!` or `debug_assert!`**: Runtime assertions for invariant violations (null pointers, alignment checks). Fatal assertions in C (infinite loop) become Rust panics.

6. **C `FDB_INFO` logging -> Rust `log` crate or `eprintln!`**: Diagnostic output uses the `log` crate (`info!`, `error!`) or direct stderr output for simplicity.

## Memory Strategy

### Ownership Model

| C Pattern | Rust Equivalent | Rationale |
|-----------|----------------|-----------|
| `malloc`/`free` | `Box` or `Vec` | RAII guarantees cleanup; no leaks |
| Fixed-size stack arrays | `[T; N]` or `Vec<T>` | `Vec` for dynamic or large allocations; `[T; N]` for known sizes |
| `static char value[]` (reentrancy bug) | `String` (owned, heap-allocated) | Eliminates the static buffer reentrancy issue in `fdb_kv_get` |
| `memset`/`memcpy` | `copy_from_slice` / `fill` | Safe bounds-checked alternatives |
| `void* user_data` | `usize` opaque pointer | Sufficient for callback context; clients cast as needed |
| Flash data buffers | `Vec<u8>` or `[u8; N]` | Sized appropriately to sector/buffer dimensions |
| Status tables (in-memory `uint8_t[]`) | `Vec<u8>` with pre-calculated length | Status table size depends on `FDB_WRITE_GRAN` and status count |
| KV name cache (fixed-size array) | `Vec<KvCacheNode>` | Configurable via constant; `Vec` simplifies initialization |
| Sector cache (fixed-size array) | `Vec<KvdbSecInfo>` | Same reasoning as KV cache |
| File descriptor cache | `Vec<Option<File>>` or custom `FileCache` struct | Rust `File` handles auto-close on drop |

### Key Memory Decisions

1. **`fdb_kv_get` reentrancy**: The C function uses `static char value[]` making it non-reentrant. The Rust version returns `Option<String>` (heap-allocated). This changes the API semantics slightly but eliminates the thread-safety bug and reentrancy hazard.

2. **Sector data buffers**: The C code uses stack-allocated buffers sized by sector size. In Rust, use `Vec<u8>` with `resize(sector_size, 0)` for sector-sized reads. For the 32-byte probe buffer in `_fdb_continue_ff_addr`, use a stack `[u8; 32]`.

3. **No global state**: C's `static bool log_is_show` in `_fdb_init_finish` becomes a `std::sync::Once` or a simple module-level `AtomicBool` to preserve the one-time log message behavior without mutable statics.

4. **File descriptors**: C's raw `int` fd becomes Rust's `std::fs::File`. The file cache (2 slots by default) stores `(u32, File)` pairs with LRU eviction. `File` auto-closes on drop, handling the cleanup that `_fdb_deinit` does manually in C.

## Unsafe Strategy

### Where `unsafe` is Required

1. **Raw flash data interpretation** (`fdb_kvdb.rs`, `fdb_tsdb.rs`): Reading sector headers and KV/TSL metadata from raw `&[u8]` byte buffers into structs. The C code casts byte pointers to struct pointers. In Rust, we use `unsafe` pointer reads with explicit offset calculations or `bytemuck`/`zerocopy` crates for zero-copy deserialization.
   - **Mitigation**: Isolate all byte-to-struct conversions in a small set of `unsafe` functions (e.g., `read_kv_header(buf: &[u8]) -> FdbKv`). Validate magic words and lengths before any unsafe cast.
   - **Estimated unsafe lines**: ~15 per module

2. **CRC32 table indexing**: The CRC32 lookup uses unchecked array access. This is already safe in the existing implementation (Rust bounds-checks by default).
   - **Estimated unsafe lines**: 0 (safe Rust is sufficient)

3. **Flash I/O (file mode)**: `std::fs::File` operations are safe. No `unsafe` needed for POSIX file I/O.
   - **Estimated unsafe lines**: 0

4. **Alignment-sensitive operations**: `FDB_WG_ALIGN`, `FDB_ALIGN_DOWN` are const fns and entirely safe.
   - **Estimated unsafe lines**: 0

### Where `unsafe` is NOT Required

- CRC32 computation: Pure safe Rust with static lookup table
- Status table get/set/write: Pure safe byte manipulation on `&mut [u8]`
- KV cache management: Pure safe Rust with `Vec` operations
- Iterator state machines: Safe Rust
- Garbage collection logic: Safe Rust
- All public API functions: Safe Rust (delegating to internal `unsafe` helpers)

### Estimated Unsafe Budget

| Module | Estimated Total Lines | Estimated Unsafe Lines | Unsafe % |
|--------|----------------------|----------------------|----------|
| fdb_def.rs | 300 | 0 | 0% |
| fdb.rs | 150 | 0 | 0% |
| fdb_kvdb.rs | 1,800 | 20 | 1.1% |
| fdb_tsdb.rs | 1,000 | 15 | 1.5% |
| fdb_file.rs | 250 | 0 | 0% |
| fdb_utils.rs | 400 | 0 | 0% |
| ports.rs | 60 | 0 | 0% |
| Others | 200 | 0 | 0% |
| **Total** | **~4,160** | **~35** | **~0.84%** |

This is well within the <10% threshold.

### Unsafe Code Guidelines

1. All `unsafe` blocks must have a `// SAFETY:` comment explaining the invariant being upheld.
2. Raw pointer reads must validate buffer lengths beforehand.
3. Magic word validation must precede any struct field access.
4. No transmute of types with different sizes or alignments.
5. `#[repr(C)]` on all structs that are read from byte buffers.

## Risk / Trade-offs

### High Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| **GC algorithm correctness** | Data loss or corruption | Direct algorithm translation; GC tests (`test_fdb_gc`, `test_fdb_gc2`) migrated first as regression tests; manual verification against C test sector layout diagrams |
| **Status-table encoding (6 write-granularity variants)** | Incorrect state transitions, data corruption | Table-driven tests parametrized over `FDB_WRITE_GRAN` values (1, 8, 32, 64, 128, 256); compare status table byte arrays with C output |
| **Alignment-sensitive flash operations** | `FDB_WG_ALIGN` mismatch causes struct misalignment or data loss | `#[repr(C)]` on all structs; alignment tests verifying Rust struct sizes match C `sizeof()`; `FDB_WG_ALIGN` as const fn with test cases |
| **Crash recovery correctness** | Undetected data corruption after simulated crash | No dedicated crash recovery tests exist in C either -- this is an acknowledged gap (severity: high). Consider adding synthetic crash recovery tests in Phase 6 |
| **Timestamp handling (32-bit vs 64-bit)** | Overflow or truncation in time-range queries | `FdbTime` type alias gated by Cargo feature `timestamp-64bit` (off by default); boundary-value tests at `i32::MAX` and `i64::MAX` |

### Medium Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| **`fdb_kv_get` static buffer elimination** | Callers expecting static lifetime will get heap-allocated `String` | Document the API change; provide an alternative `fdb_kv_get_into(dest: &mut [u8])` for callers that need stack buffers |
| **File descriptor caching semantics** | Different fd caching behavior on multi-threaded access | Preserve C's LRU cache exactly; single-threaded design for initial release |
| **MCU-specific features (lock/unlock, get_time callbacks)** | Unused in tests but part of public API | `Option<Box<dyn Fn()>>`; callbacks default to `None` |
| **Combined sector mode (marked TODO in C)** | Feature is incomplete in C source; may have bugs | Preserve existing behavior but mark as `unimplemented!()` with clear error; not used in tests |
| **Reverse iteration binary search** | No dedicated test exists in C for `fdb_tsl_iter_reverse` | Add synthetic tests validating reverse iteration across sector boundaries |

### Low Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Magic word endianness** | Host-native `u32` comparison fails on big-endian targets | Use `u32::from_le_bytes()` or `u32::from_be_bytes()` depending on the target endianness flag |
| **`FDB_KV_AUTO_UPDATE` feature** | Marked as non-goal; excluded from initial migration | Stub with `compile_error!()` or `unimplemented!()` if feature flag is enabled |
| **`FDB_TSDB_FIXED_BLOB_SIZE` feature** | Changes on-flash format; excluded | Stub; variable-size implementation is the default |
| **RT-Thread API replacement in tests** | Test timing differences (`rt_tick_get`, `rt_thread_mdelay`) | Replace with `std::time::Instant` for ticks; `std::thread::sleep` only when strictly needed for ordering; remove real-time delays where possible |

### Known Gaps and Deferred Items

1. **`FDB_KV_AUTO_UPDATE`** (deferred): Version-based automatic KV update feature
2. **`FDB_TSDB_FIXED_BLOB_SIZE`** (deferred): Fixed-size blob optimization
3. **FAL partition mode** (deferred): Flash abstraction layer for real flash hardware
4. **LIBC file mode** (deferred): `fopen`/`fread` variant; POSIX variant is sufficient
5. **Multi-threaded safety** (deferred): Single-threaded; `Mutex` wrapper can be added later
6. **Combined sector mode** (deferred): Marked TODO in C source; low priority
7. **Crash recovery tests** (deferred): No dedicated tests exist in C either; synthetic tests could be added

### Trade-off Decisions

1. **Single crate vs workspace**: Single crate chosen for simplicity; ~4,400 lines is small enough. If the project grows significantly (e.g., FAL backend, embedded HAL impls), splitting into `flashdb-core` + `flashdb-file` + `flashdb-fal` workspaces makes sense.

2. **`Vec` vs fixed-size arrays**: The existing Rust code uses `Vec<KvCacheNode>` for cache tables. This is more flexible than C's fixed-size arrays and is acceptable since embedded memory constraints are a non-goal. For strict embedded use, const-generic fixed-size arrays can be added later via a `heapless` feature.

3. **Trait-based flash I/O vs direct `std::fs`**: The `FlashStorage` trait adds indirection but enables testing with `RamFlash` (in-memory, no filesystem dependency) and future embedded backends. The cost is dynamic dispatch, acceptable for a database library.

4. **Callback-based iteration vs Rust `Iterator` trait**: The C code uses `fdb_tsl_cb` callbacks for iteration. The initial Rust implementation preserves callback-based iteration to minimize behavior changes. A future enhancement could provide `impl Iterator` wrappers that yield `FdbTsl` items.

## Architecture Decisions Summary

| Decision | Choice | Alternative Considered |
|----------|--------|----------------------|
| Crate structure | Single `lib` crate with 11 modules | Multi-crate workspace (rejected: too much overhead for ~4,400 lines) |
| Error handling | `Result<T, FdbError>` | Panics for errors (rejected: C code returns errors gracefully) |
| Flash I/O abstraction | `FlashStorage` trait | Direct `std::fs` calls (rejected: blocks embedded use) |
| Type representation | Owned structs (`Vec`, `String`) | Raw pointers with manual cleanup (rejected: unsafe and unidiomatic) |
| C struct "inheritance" | Composition (`parent: FdbDb`) | Trait with blanket impl (rejected: too complex for two subtypes) |
| Status table encoding | Pure safe byte manipulation | `unsafe` pointer casts (not needed; safe byte ops are sufficient) |
| KV cache | `Vec<KvCacheNode>` with LRU logic | Fixed-size array (rejected: less flexible; can be added later) |
| Test framework | Rust `#[test]` with `assert!` macros | Custom test harness (rejected: Rust's native framework is sufficient) |
| Logging | `log` crate or `eprintln!` | Custom logging trait (rejected: over-engineering; C uses `printf`) |
| Timestamp width | Feature flag `timestamp-64bit` (off by default) | Const generic (rejected: feature flags are simpler for conditional compilation) |

## Migration Phase Order (Implementation Plan)

The dependency graph from the capability map drives the implementation order:

### Phase A: Foundation (P0 capabilities - no deps)
1. `fdb_cfg_template.rs` - Feature flags, constants
2. `fdb_low_lvl.rs` - Alignment const fns, sentinel constants
3. `fdb_def.rs` - All type definitions (enums, structs)
4. `fdb_utils.rs` - CRC32, status tables, blob, flash dispatch
5. `ports.rs` - `FlashStorage` trait, `RamFlash`

### Phase B: I/O and Lifecycle (P0 + P1 base)
6. `fdb_file.rs` - File mode I/O with fd cache (implements `FlashStorage`)
7. `fdb.rs` - Init/deinit lifecycle, path resolution

### Phase C: KVDB (P1 + P2)
8. `fdb_kvdb.rs` - Sector management, KV CRUD, cache
9. `fdb_kvdb.rs` - Iterator, garbage collection
10. `fdb_kvdb.rs` - Crash recovery, control API

### Phase D: TSDB (P1 + P2)
11. `fdb_tsdb.rs` - Sector layout, TSL append
12. `fdb_tsdb.rs` - Iteration (forward, reverse, by_time), query count
13. `fdb_tsdb.rs` - Status management, cleanup, control API

### Phase E: Integration
14. `flashdb.rs` - Public re-exports
15. `lib.rs` - Module declarations
16. `tests/kvdb_tests.rs` - Migrated KVDB test suite
17. `tests/tsdb_tests.rs` - Migrated TSDB test suite

### Build/Test Gates
- **Gate A**: `cargo build` after Phase A -- types and utilities compile
- **Gate B**: `cargo build` + `cargo test` (utils tests) after Phase B -- flash I/O and lifecycle compile and test
- **Gate C**: `cargo test` (KVDB unit tests) after Phase C -- all KVDB operations tested
- **Gate D**: `cargo test` (full suite) after Phase E -- all 24 migrated tests pass
- **Final Gate**: `cargo build && cargo test` succeed; `unsafe` ratio verified < 10%
