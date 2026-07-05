# Implementation Plan: FlashDB C-to-Rust Migration

## Plan Overview

| Property | Value |
|----------|-------|
| Total batches | 17 |
| P0 batches | 6 (Batches 1-6) |
| P1 batches | 7 (Batches 7-13) |
| P2 batches | 3 (Batches 14-16) |
| Integration batch | 1 (Batch 17) |
| Total implementation tasks | ~120 |
| Total test tasks | ~75 |
| Estimated completed tasks | ~45 (~40%: P0 foundation + lifecycle) |
| Estimated remaining tasks | ~150 |
| Output directory | E:/009workspace/codex/loopforge-contest-driver/work/output/flashDB_rust |

## OUTPUT_DIR Layout

```
output/flashDB_rust/
├── Cargo.toml                     (crate metadata, edition 2021)
├── src/
│   ├── lib.rs                     (module declarations, re-exports via pub use)
│   ├── fdb_def.rs                 (Batch 1: all type definitions, enums, structs)
│   ├── fdb_low_lvl.rs             (Batch 1: alignment const fns, sentinel constants)
│   ├── fdb_cfg_template.rs        (Batch 1: feature flags, WRITE_GRAN, version)
│   ├── fdb_utils.rs               (Batch 2+3+4+6: CRC32, status tables, blob, flash dispatch)
│   ├── ports.rs                   (Batch 6: FlashStorage trait, RamFlash, FileFlash)
│   ├── fdb_file.rs                (Batch 5: file-mode I/O with LRU file cache)
│   ├── fdb.rs                     (Batch 7: init/deinit lifecycle, path resolution)
│   ├── fdb_kvdb.rs                (Batch 8+10+11+14+15: KVDB engine, sector mgmt, CRUD, iter, GC, recovery)
│   ├── fdb_tsdb.rs                (Batch 9+12+13+16: TSDB engine, sector layout, append, iter, cleanup)
│   └── flashdb.rs                 (Public re-exports matching flashdb.h API surface)
└── tests/
    ├── source_migration.rs        (Existing: 13 compiled tests for CRC32/blob/flash/init)
    ├── kvdb_tests.rs              (Batch 17: 15 KVDB test functions + 3 helpers)
    └── tsdb_tests.rs              (Batch 17: 11 TSDB test functions + 1 helper)
```

---

## Batch Execution Plan

### Batch 1: Foundational Data Types and Constants

**Capability**: foundational-types (Priority: P0)
**Spec reference**: specs/foundational-types/spec.md
**C source files**: inc/fdb_def.h (351 lines), inc/fdb_low_lvl.h (71 lines), inc/fdb_cfg_template.h (56 lines)
**Rust target files**: src/fdb_def.rs, src/fdb_low_lvl.rs, src/fdb_cfg_template.rs
**Dependencies**: None (P0 root)

**Implementation status**: 26/26 functions complete. All enums, structs, constants, const fns, and callback types defined.

**Implementation functions**:
1. `enum FdbError { NoErr=0, EraseErr, ReadErr, WriteErr, PartNotFound, KvNameErr, KvNameExist, SavedFull, InitFailed }` -- C equivalent: `fdb_err_t` in fdb_def.h
2. `enum FdbKvStatus { Unused=0, PreWrite, Write, PreDelete, Deleted, ErrHdr }` -- C equivalent: `enum fdb_kv_status` in fdb_def.h
3. `enum FdbTslStatus { Unused=0, PreWrite, Write, UserStatus1, Deleted, UserStatus2 }` -- C equivalent: `enum fdb_tsl_status` in fdb_def.h
4. `enum FdbSectorStoreStatus { Unused=0, Empty, Using, Full }` -- C equivalent: `enum fdb_sector_store_status` in fdb_def.h
5. `enum FdbSectorDirtyStatus { Unused=0, False, True, Gc }` -- C equivalent: `enum fdb_sector_dirty_status` in fdb_def.h
6. `enum FdbDbType { Kv=0, Ts=1 }` -- C equivalent: `typedef enum { FDB_DB_TYPE_KV, FDB_DB_TYPE_TS }` in fdb_def.h

**Data structures**:
| C Struct | Rust Equivalent | Field Mapping |
|----------|----------------|---------------|
| `struct fdb_db` | `struct FdbDb` | name: String, db_type: FdbDbType, storage_path: String, sec_size: u32, max_size: u32, oldest_addr: u32, init_ok: bool, file_mode: bool, not_formatable: bool |
| `struct fdb_kvdb` | `struct FdbKvdb` | parent: FdbDb (composition), default_kvs: FdbDefaultKv, gc_request: bool, in_recovery_check: bool, cur_kv: FdbKv, cur_sector: KvdbSecInfo, last_is_complete_del: bool, kv_cache_table: Vec<KvCacheNode>, sector_cache_table: Vec<KvdbSecInfo>, ver_num: u32 |
| `struct fdb_tsdb` | `struct FdbTsdb` | parent: FdbDb (composition), cur_sec: TsdbSecInfo, last_time: FdbTime, max_len: usize, rollover: bool |
| `struct fdb_kv` | `struct FdbKv` | status: FdbKvStatus, crc_is_ok: bool, name_len: u8, magic: u32, len: u32, value_len: u32, name: [u8; 64], addr_start: u32, addr_value: u32 |
| `struct fdb_tsl` | `struct FdbTsl` | status: FdbTslStatus, time: FdbTime, log_len: u32, addr_index: u32, addr_log: u32 |
| `struct fdb_blob` | `struct FdbBlob` | buf: Vec<u8>, size: usize, saved_meta_addr: u32, saved_addr: u32, saved_len: usize |
| `struct kvdb_sec_info` | `struct KvdbSecInfo` | check_ok: bool, store_status: FdbSectorStoreStatus, dirty_status: FdbSectorDirtyStatus, addr: u32, magic: u32, combined: u32, remain: usize, empty_kv: u32 |
| `struct tsdb_sec_info` | `struct TsdbSecInfo` | check_ok: bool, status: FdbSectorStoreStatus, addr: u32, magic: u32, start_time: FdbTime, end_time: FdbTime, end_idx: u32, end_info_stat: [FdbTslStatus; 2], remain: usize, empty_idx: u32, empty_data: u32 |
| `struct kv_cache_node` | `struct KvCacheNode` | name_crc: u16, active: u16, addr: u32 |
| `struct fdb_kv_iterator` | `struct FdbKvIterator` | curr_kv: FdbKv, iterated_cnt: u32, iterated_obj_bytes: usize, iterated_value_bytes: usize, sector_addr: u32, traversed_len: u32 |

**Remaining unit tests**:
1. `#[test] fn test_fdb_error_discriminants()` -- covers scenario: FdbError discriminant values match C fdb_err_t
2. `#[test] fn test_kv_status_default_is_unused()` -- covers scenario: Default variant == Unused with discriminant 0

**Build command**: `cargo build`
**Test command**: `cargo test types`
**Completion criteria**:
- [x] `cargo build` passes
- [x] `cargo test` -- all existing tests pass
- [ ] All discriminant values verified against C `fdb_err_t` and status enums
- [ ] FdbKv/FdbTsl/KvdbSecInfo/TsdbSecInfo annotated `#[repr(C)]`

---

### Batch 2: CRC32 Checksum Computation

**Capability**: crc32-computation (Priority: P0)
**Spec reference**: specs/crc32-computation/spec.md
**C source files**: src/fdb_utils.c (fdb_calc_crc32 at line 77)
**Rust target files**: src/fdb_utils.rs
**Dependencies**: None (P0 standalone)

**Implementation status**: 2/2 functions complete. CRC32_TABLE and fdb_calc_crc32 match C implementation.

**Implementation functions**:
1. `static CRC32_TABLE: [u32; 256]` -- C equivalent: `static uint32_t crc32_table[256]` in fdb_utils.c:21-76
2. `fn fdb_calc_crc32(init_crc: u32, buf: &[u8]) -> u32` -- C equivalent: `uint32_t fdb_calc_crc32(uint32_t init_crc, const void *buf, size_t size)` in fdb_utils.c:77

**Data structures**: None (pure function with static lookup table)

**Unit tests**:
1. `#[test] fn test_crc32_known_values()` -- covers scenario: "123456789" => 0xCBF43926 (standard CRC32 check value)
2. `#[test] fn test_crc32_empty()` -- covers scenario: empty buffer returns 0x00000000
3. `#[test] fn test_crc32_incremental()` -- covers scenario: incremental computation matches single-shot

**Build command**: `cargo build`
**Test command**: `cargo test crc32`
**Completion criteria**:
- [x] `cargo build` passes
- [x] `cargo test crc32` -- all 3 tests pass
- [x] CRC32_TABLE 256 entries match C `crc32_table[]` byte-for-byte
- [x] Known-answer test: fdb_calc_crc32(0, b"123456789") == 0xCBF43926

---

### Batch 3: Flash Status Table Management

**Capability**: flash-status-table (Priority: P0)
**Spec reference**: specs/flash-status-table/spec.md
**C source files**: src/fdb_utils.c (lines 91-218)
**Rust target files**: src/fdb_utils.rs
**Dependencies**: Batch 1 (foundational-types)

**Implementation status**: 4/5 functions have basic implementations. fdb_get_status needs full C-equivalent logic. WRITE_GRAN variability support missing.

**Implementation functions**:
1. `fn fdb_set_status(status_table: &mut [u8], status_num: usize, status_index: usize) -> usize` -- C equivalent: `_fdb_set_status` in fdb_utils.c:91
2. `fn fdb_get_status(status_table: &[u8], status_num: usize) -> usize` -- C equivalent: `_fdb_get_status` in fdb_utils.c:126 -- **NEEDS FIX**: current implementation is simplified stub
3. `fn fdb_write_status(flash: &mut dyn FlashStorage, addr: u32, status_table: &mut [u8], status_num: usize, status_index: usize) -> Result<(), FdbError>` -- C equivalent: `_fdb_write_status` in fdb_utils.c:147
4. `fn fdb_read_status(flash: &dyn FlashStorage, addr: u32, status_table: &mut [u8], total_num: usize) -> Result<usize, FdbError>` -- C equivalent: `_fdb_read_status` in fdb_utils.c:173
5. `fn fdb_continue_ff_addr(flash: &dyn FlashStorage, start: u32, end: u32) -> Result<u32, FdbError>` -- C equivalent: `_fdb_continue_ff_addr` in fdb_utils.c:185

**Data structures**: None (raw `&[u8]`/`&mut [u8]` slices)

**Unit tests**:
1. `#[test] fn test_status_table_all_gran()` -- covers scenario: WRITE_GRAN in {1,8,32,64,128,256} round-trip set/get
2. `#[test] fn test_get_status_erased_table()` -- covers scenario: all-0xFF table returns 0 (UNUSED)
3. `#[test] fn test_get_status_full_table()` -- covers scenario: fully-written table returns status_num-1
4. `#[test] fn test_continue_ff_addr_boundary()` -- covers scenario: all-erased returns aligned start; fully-written returns end

**Build command**: `cargo build`
**Test command**: `cargo test status`
**Completion criteria**:
- [ ] `cargo build` passes
- [ ] `cargo test status` -- all 4 tests pass
- [ ] fdb_get_status matches C algorithm: scan from highest index downward, return count of written bytes + 1
- [ ] FDB_WRITE_GRAN support verified for all 6 values via parametrized tests

---

### Batch 4: Blob Data Abstraction

**Capability**: blob-abstraction (Priority: P0)
**Spec reference**: specs/blob-abstraction/spec.md
**C source files**: src/fdb_utils.c (lines 221-254)
**Rust target files**: src/fdb_utils.rs
**Dependencies**: Batch 1 (foundational-types)

**Implementation status**: 2/2 functions complete. Blob create and read match C implementation.

**Implementation functions**:
1. `fn fdb_blob_make(buf: Vec<u8>) -> FdbBlob` -- C equivalent: `void fdb_blob_make(fdb_blob_t blob, const void *value_buf, size_t buf_len)` in fdb_utils.c:221
2. `fn fdb_blob_read(blob: &mut FdbBlob, flash: &dyn FlashStorage) -> usize` -- C equivalent: `size_t fdb_blob_read(fdb_db_t db, fdb_blob_t blob)` in fdb_utils.c:237

**Data structures**:
| C Struct | Rust Equivalent | Field Mapping |
|----------|----------------|---------------|
| `struct fdb_blob` | `struct FdbBlob` | buf: Vec<u8> (C void* -> owned), size: usize, saved_meta_addr: u32, saved_addr: u32, saved_len: usize |

**Unit tests**:
1. `#[test] fn test_blob_read_empty()` -- covers scenario: size=0 or saved_len=0 skips flash read
2. `#[test] fn test_blob_read_truncation()` -- covers scenario: blob.size < saved_len truncates without overflow
3. `#[test] fn test_blob_make_empty_buffer()` -- covers scenario: empty Vec creates blob with size=0

**Build command**: `cargo build`
**Test command**: `cargo test blob`
**Completion criteria**:
- [x] `cargo build` passes
- [x] `cargo test blob` -- existing test passes
- [ ] New blob edge-case tests pass: empty buffer, truncation, zero-size read

---

### Batch 5: File-based Storage Backend

**Capability**: file-storage-backend (Priority: P0)
**Spec reference**: specs/file-storage-backend/spec.md
**C source files**: src/fdb_file.c (all 317 lines)
**Rust target files**: src/fdb_file.rs
**Dependencies**: Batch 1 (foundational-types)

**Implementation status**: 0/7 functions complete. Current fdb_file.rs contains only stub functions returning Err for all operations.

**Implementation functions**:
1. `fn get_db_file_path(dir: &str, name: &str, sec_addr: u32, sec_size: u32) -> String` -- C equivalent: `get_db_file_path` in fdb_file.c:19
2. `fn get_file_from_cache(db: &FdbDb, sec_addr: u32) -> Option<usize>` -- C equivalent: `get_file_from_cache` in fdb_file.c:45
3. `fn update_file_cache(db: &mut FdbDb, sec_addr: u32, file: std::fs::File)` -- C equivalent: `update_file_cache` in fdb_file.c:55
4. `fn open_db_file(db: &mut FdbDb, sec_addr: u32, clean: bool) -> Result<std::fs::File, FdbError>` -- C equivalent: `open_db_file` in fdb_file.c:86
5. `fn fdb_file_read(db: &mut FdbDb, addr: u32, buf: &mut [u8], size: usize) -> Result<(), FdbError>` -- C equivalent: `_fdb_file_read` in fdb_file.c:122
6. `fn fdb_file_write(db: &mut FdbDb, addr: u32, buf: &[u8], size: usize) -> Result<(), FdbError>` -- C equivalent: `_fdb_file_write` in fdb_file.c:138
7. `fn fdb_file_erase(db: &mut FdbDb, addr: u32, size: usize) -> Result<(), FdbError>` -- C equivalent: `_fdb_file_erase` in fdb_file.c:157

**Data structures**:
| C Struct | Rust Equivalent | Field Mapping |
|----------|----------------|---------------|
| File cache (cur_file_sec[], cur_file[]) | FileCache struct with Vec<(u32, Option<File>)> of size FDB_FILE_CACHE_TABLE_SIZE | LRU: shift entries on new access, oldest at end |

**Unit tests**:
1. `#[test] fn test_get_db_file_path()` -- covers scenario: "dir/name.fdb.2" where sector index = addr/sec_size
2. `#[test] fn test_file_cache_lru_eviction()` -- covers scenario: 2-slot cache full, oldest evicted on third access
3. `#[test] fn test_file_read_write_in_temp_dir()` -- covers scenario: temp directory file create, write, read-back
4. `#[test] fn test_file_erase_fills_ff()` -- covers scenario: erase fills all bytes with 0xFF
5. `#[test] fn test_open_clean_truncates_and_fills()` -- covers scenario: clean=true truncates to sec_size, fills 0xFF

**Build command**: `cargo build --features file-mode`
**Test command**: `cargo test file`
**Completion criteria**:
- [ ] `cargo build` passes
- [ ] `cargo test file` -- all 5 tests pass
- [ ] File path pattern matches C: `<dir>/<name>.fdb.<sector_index>`
- [ ] File cache never exceeds FDB_FILE_CACHE_TABLE_SIZE (2) open files

---

### Batch 6: Flash I/O Dispatch Layer

**Capability**: flash-io-dispatch (Priority: P0)
**Spec reference**: specs/flash-io-dispatch/spec.md
**C source files**: src/fdb_utils.c (lines 257-350)
**Rust target files**: src/fdb_utils.rs, src/ports.rs
**Dependencies**: Batch 1 (foundational-types), Batch 5 (file-storage-backend)

**Implementation status**: 6/7 functions complete. FlashStorage trait, RamFlash, and all dispatch functions implemented. FileFlash backend missing.

**Implementation functions**:
1. `trait FlashStorage { fn read(...) -> Result; fn erase(...) -> Result; fn write(...) -> Result; }` -- C equivalent: dispatch via `#ifdef FDB_USING_FAL_MODE`/`FDB_USING_FILE_MODE` in fdb_utils.c
2. `struct RamFlash { data: Vec<u8>, size: usize }` with FlashStorage impl -- in-memory test backend
3. `fn fdb_flash_read(flash: &dyn FlashStorage, addr: u32, buf: &mut [u8], size: usize) -> Result<(), FdbError>` -- C equivalent: `_fdb_flash_read` in fdb_utils.c:257
4. `fn fdb_flash_erase(flash: &mut dyn FlashStorage, addr: u32, size: usize) -> Result<(), FdbError>` -- C equivalent: `_fdb_flash_erase` in fdb_utils.c:278
5. `fn fdb_flash_write(flash: &mut dyn FlashStorage, addr: u32, buf: &[u8], size: usize) -> Result<(), FdbError>` -- C equivalent: `_fdb_flash_write` in fdb_utils.c:299
6. `fn fdb_flash_write_align(flash: &mut dyn FlashStorage, addr: u32, buf: &[u8], size: usize) -> Result<(), FdbError>` -- C equivalent: `_fdb_flash_write_align` in fdb_utils.c:322
7. `struct FileFlash` with FlashStorage impl for file-mode (NEW -- integrates Batch 5 functions)

**Data structures**: None (trait-based dispatch)

**Unit tests**:
1. `#[test] fn test_flash_write_align_padding()` -- covers scenario: 3 bytes padded to 4 with 0xFF when WRITE_GRAN=32
2. `#[test] fn test_flash_read_write_errors()` -- covers scenario: out-of-bounds address returns ReadErr/WriteErr

**Build command**: `cargo build`
**Test command**: `cargo test flash`
**Completion criteria**:
- [x] `cargo build` passes
- [x] `cargo test flash` -- existing RamFlash tests pass
- [ ] FileFlash backend implemented and tested
- [ ] fdb_flash_write_align correctly pads to FDB_WRITE_GRAN boundary

---

### Batch 7: Database Lifecycle Management

**Capability**: database-lifecycle (Priority: P1)
**Spec reference**: specs/database-lifecycle/spec.md
**C source files**: src/fdb.c (all 157 lines)
**Rust target files**: src/fdb.rs
**Dependencies**: Batch 1 (foundational-types), Batch 6 (flash-io-dispatch)

**Implementation status**: 8/8 functions complete. Init validation (power-of-2, >=2 sectors, idempotency), deinit, and KVDB/TSDB wrappers all implemented.

**Implementation functions**:
1. `fn fdb_init_ex(db: &mut FdbDb, name: &str, path: &str, db_type: FdbDbType) -> Result<(), FdbError>` -- C equivalent: `_fdb_init_ex` in fdb.c:31
2. `fn fdb_init_finish(db: &mut FdbDb, result: FdbError)` -- C equivalent: `_fdb_init_finish` in fdb.c:102
3. `fn fdb_deinit(db: &mut FdbDb)` -- C equivalent: `_fdb_deinit` in fdb.c:118
4. `fn fdb_db_path(db: &FdbDb) -> &str` -- C equivalent: `_fdb_db_path` in fdb.c:141
5. `fn fdb_kvdb_init(kvdb: &mut FdbKvdb, name: &str, path: &str) -> Result<(), FdbError>` -- C equivalent: `fdb_kvdb_init` in fdb_kvdb.c:1753
6. `fn fdb_kvdb_deinit(kvdb: &mut FdbKvdb)` -- C equivalent: `fdb_kvdb_deinit` in fdb_kvdb.c:1825
7. `fn fdb_tsdb_init(tsdb: &mut FdbTsdb, name: &str, path: &str, max_len: usize) -> Result<(), FdbError>` -- C equivalent: `fdb_tsdb_init` in fdb_tsdb.c:1004
8. `fn fdb_tsdb_deinit(tsdb: &mut FdbTsdb)` -- C equivalent: `fdb_tsdb_deinit` in fdb_tsdb.c:1091

**Data structures**: Uses `FdbDb` from Batch 1

**Unit tests**:
1. `#[test] fn test_init_idempotent()` -- covers scenario: second init with init_ok=true returns Ok without re-validation
2. `#[test] fn test_init_requires_two_sectors()` -- covers scenario: max_size/sec_size must be >= 2

**Build command**: `cargo build`
**Test command**: `cargo test init`
**Completion criteria**:
- [x] `cargo build` passes
- [x] `cargo test init` -- existing init/deinit tests pass
- [ ] Idempotency test passes: double-init returns Ok

---

### Batch 8: KVDB Sector Management

**Capability**: kvdb-sector-management (Priority: P1)
**Spec reference**: specs/kvdb-sector-management/spec.md
**C source files**: src/fdb_kvdb.c (sector management functions: lines 416-508, 769-950, 1069-1182)
**Rust target files**: src/fdb_kvdb.rs
**Dependencies**: Batch 1 (foundational-types), Batch 6 (flash-io-dispatch), Batch 3 (flash-status-table), Batch 7 (database-lifecycle)

**Implementation status**: 0/10 functions complete. All sector management functions are stubs or missing.

**Implementation functions**:
1. `fn format_sector(kvdb: &mut FdbKvdb, addr: u32, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `format_sector` in fdb_kvdb.c:769
2. `fn read_sector_info(kvdb: &FdbKvdb, sec: &mut KvdbSecInfo, flash: &dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `read_sector_info` in fdb_kvdb.c:416
3. `fn update_sec_status(kvdb: &mut FdbKvdb, sec: &mut KvdbSecInfo, new_status: FdbSectorStoreStatus, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `update_sec_status` in fdb_kvdb.c:829
4. `fn get_next_sector_addr(kvdb: &FdbKvdb, cur_addr: u32) -> u32` -- C equivalent: `get_next_sector_addr` in fdb_kvdb.c:504
5. `fn alloc_kv(kvdb: &mut FdbKvdb, size: usize, flash: &mut dyn FlashStorage) -> Result<u32, FdbError>` -- C equivalent: `alloc_kv` in fdb_kvdb.c:915
6. `fn new_kv(kvdb: &mut FdbKvdb, size: usize, flash: &mut dyn FlashStorage) -> Result<u32, FdbError>` -- C equivalent: `new_kv` in fdb_kvdb.c:1069
7. `fn new_kv_ex(kvdb: &mut FdbKvdb, kv_len: u32, value_len: u32, flash: &mut dyn FlashStorage) -> Result<u32, FdbError>` -- C equivalent: `new_kv_ex` in fdb_kvdb.c:1091
8. `fn sector_iterator(kvdb: &FdbKvdb, cb: fn(&FdbKvdb, u32) -> bool, flash: &dyn FlashStorage)` -- C equivalent: `sector_iterator` in fdb_kvdb.c:863
9. `fn find_next_kv_addr(kvdb: &FdbKvdb, sec: &KvdbSecInfo, flash: &dyn FlashStorage) -> u32` -- C equivalent: `find_next_kv_addr` in fdb_kvdb.c:488
10. `fn get_next_kv_addr(kvdb: &FdbKvdb, sec: &KvdbSecInfo, kv: &FdbKv, flash: &dyn FlashStorage) -> u32` -- C equivalent: `get_next_kv_addr` in fdb_kvdb.c:498

**Data structures**:
| C Struct | Rust Equivalent | Field Mapping |
|----------|----------------|---------------|
| `struct sector_hdr_data` (12 bytes) | `#[repr(C)] struct SectorHdrData` | magic: u32, store_status_table: [u8; STORE_STATUS_TABLE_SIZE], dirty_status_table: [u8; DIRTY_STATUS_TABLE_SIZE], combined/remain: u32 |

**Unit tests**: 6 tests covering format, read, status transition, allocation, sector addr wrapping

**Build command**: `cargo build`
**Test command**: `cargo test sector`
**Completion criteria**:
- [ ] `cargo build` passes
- [ ] `cargo test sector` -- all 6 tests pass
- [ ] Sector magic word 0x30424446 written correctly
- [ ] EMPTY->USING->FULL status transitions work via status tables

---

### Batch 9: TSDB Sector Layout and Initialization

**Capability**: tsdb-sector-layout (Priority: P1)
**Spec reference**: specs/tsdb-sector-layout/spec.md
**C source files**: src/fdb_tsdb.c (sector layout functions: lines 147-389, 950-1095)
**Rust target files**: src/fdb_tsdb.rs
**Dependencies**: Batch 1 (foundational-types), Batch 6 (flash-io-dispatch), Batch 3 (flash-status-table), Batch 7 (database-lifecycle)

**Implementation status**: 0/8 functions complete. All TSDB sector layout functions are stubs.

**Implementation functions**:
1. `fn tsdb_read_sector_info(tsdb: &FdbTsdb, sec: &mut TsdbSecInfo, flash: &dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `read_sector_info` in fdb_tsdb.c:229
2. `fn tsdb_format_sector(tsdb: &FdbTsdb, addr: u32, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `format_sector` in fdb_tsdb.c:320
3. `fn tsdb_get_next_sector_addr(tsdb: &FdbTsdb, cur_addr: u32) -> u32` -- C equivalent: `get_next_sector_addr` in fdb_tsdb.c:177
4. `fn tsdb_get_last_sector_addr(tsdb: &FdbTsdb, cur_addr: u32) -> u32` -- C equivalent: `get_last_sector_addr` in fdb_tsdb.c:227
5. `fn tsdb_sector_iterator(tsdb: &FdbTsdb, cb: fn(u32) -> bool, flash: &dyn FlashStorage)` -- C equivalent: `sector_iterator` in fdb_tsdb.c:950
6. `fn check_sec_hdr_cb(tsdb: &FdbTsdb, addr: u32, flash: &dyn FlashStorage) -> bool` -- C equivalent: `check_sec_hdr_cb` in fdb_tsdb.c:990
7. `fn fdb_tsdb_init(tsdb: &mut FdbTsdb, name: &str, path: &str, max_len: usize) -> Result<(), FdbError>` (full version with sector scan) -- C equivalent: `fdb_tsdb_init` in fdb_tsdb.c:1004
8. `fn fdb_tsdb_deinit(tsdb: &mut FdbTsdb)` (full version with file cleanup) -- C equivalent: `fdb_tsdb_deinit` in fdb_tsdb.c:1091

**Data structures**:
| C Struct | Rust Equivalent | Field Mapping |
|----------|----------------|---------------|
| `struct tsdb_sec_info` | `struct TsdbSecInfo` | start_time: FdbTime, end_time: FdbTime, end_idx: u32, end_info_stat: [FdbTslStatus; 2] (dual slot for crash resilience), empty_idx: u32, empty_data: u32 |

**Unit tests**: 4 tests covering TSDB format, read, address wrapping, fresh init

**Build command**: `cargo build`
**Test command**: `cargo test tsdb_init`
**Completion criteria**:
- [ ] `cargo build` passes
- [ ] `cargo test tsdb_init` -- all 4 tests pass
- [ ] TSDB magic word 0x33424446 distinct from KVDB's 0x30424446
- [ ] Dual end_info slots correctly parsed; corrupted slot falls back to valid slot

---

### Batch 10: KV CRUD Operations

**Capability**: kv-crud (Priority: P1)
**Spec reference**: specs/kv-crud/spec.md
**C source files**: src/fdb_kvdb.c (CRUD functions: lines 585-950, 1184-1490)
**Rust target files**: src/fdb_kvdb.rs
**Dependencies**: Batch 1, 6, 3, 2, 4, 7, 8

**Implementation status**: 0/14 functions complete. All KV CRUD operations are stubs returning Ok/None/0.

**Implementation functions**:
1. `fn find_kv(kvdb: &FdbKvdb, key: &str, kv: &mut FdbKv, flash: &dyn FlashStorage) -> bool` -- C equivalent: `find_kv` in fdb_kvdb.c:585 (cache-first, then full scan)
2. `fn get_kv(kvdb: &FdbKvdb, kv_addr: u32, blob: &mut FdbBlob, flash: &dyn FlashStorage) -> Result<usize, FdbError>` -- C equivalent: `get_kv` in fdb_kvdb.c:622
3. `fn write_kv_hdr(kvdb: &FdbKvdb, addr: u32, kv: &FdbKv, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `write_kv_hdr` in fdb_kvdb.c:1440 (CRC32 over header+name+value)
4. `fn create_kv_blob(kvdb: &mut FdbKvdb, kv: &FdbKv, blob: &FdbBlob, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `create_kv_blob` in fdb_kvdb.c:1184
5. `fn del_kv(kvdb: &mut FdbKvdb, key: &str, old_kv: Option<&FdbKv>, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `del_kv` in fdb_kvdb.c:940 (PRE_DELETE -> DELETED)
6. `fn set_kv(kvdb: &mut FdbKvdb, key: &str, blob: &FdbBlob, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `set_kv` in fdb_kvdb.c:1295
7-14. Public API: `fdb_kv_set`, `fdb_kv_get`, `fdb_kv_set_blob`, `fdb_kv_get_blob`, `fdb_kv_del`, `fdb_kv_get_obj`, `fdb_kv_to_blob`, `fdb_kv_set_default`

**Data structures**: Uses `FdbKv`, `FdbBlob`, `FdbKvdb` from Batch 1

**Unit tests**: 7 tests covering set/get, overwrite, delete, name validation, blob truncation, CRC32 integrity, defaults

**Build command**: `cargo build`
**Test command**: `cargo test kv_crud`
**Completion criteria**:
- [ ] `cargo build` passes
- [ ] `cargo test kv_crud` -- all 7 tests pass
- [ ] 2-phase delete (PRE_DELETE -> DELETED) implemented correctly
- [ ] CRC32 integrity verified on every read
- [ ] KV cache updated on find/write/delete

---

### Batch 11: KVDB Iteration

**Capability**: kvdb-iteration (Priority: P1)
**Spec reference**: specs/kvdb-iteration/spec.md
**C source files**: src/fdb_kvdb.c (iteration functions: lines 576-585, 1468-1660)
**Rust target files**: src/fdb_kvdb.rs
**Dependencies**: Batch 1, 6, 8, 10

**Implementation status**: 1/4 functions partially complete (iterator_init sets sector_addr). fdb_kv_iterate is a stub returning false.

**Implementation functions**:
1. `fn kv_iterator(kvdb: &FdbKvdb, cb: fn(&FdbKv, &FdbBlob) -> bool, flash: &dyn FlashStorage)` -- C equivalent: `kv_iterator` in fdb_kvdb.c:1468
2. `fn fdb_kv_iterator_init(kvdb: &FdbKvdb) -> FdbKvIterator` (complete: add remaining field initialization) -- C equivalent: `fdb_kv_iterator_init` in fdb_kvdb.c:1488
3. `fn fdb_kv_iterate(kvdb: &FdbKvdb, itr: &mut FdbKvIterator, flash: &dyn FlashStorage) -> bool` (FULL implementation needed) -- C equivalent: `fdb_kv_iterate` in fdb_kvdb.c:1504
4. `fn fdb_kv_print(kvdb: &FdbKvdb)` -- C equivalent: `fdb_kv_print` in fdb_kvdb.c:1558

**Data structures**: Uses `FdbKvIterator`, `FdbKv`, `FdbBlob` from Batch 1

**Unit tests**: 4 tests covering init, empty DB, skip deleted, multi-sector traversal

**Build command**: `cargo build`
**Test command**: `cargo test iterate`
**Completion criteria**:
- [ ] `cargo build` passes
- [ ] `cargo test iterate` -- all 4 tests pass
- [ ] Iterator returns KVs in address order from oldest_addr
- [ ] DELETED/ERR_HDR/UNUSED KVs skipped during iteration

---

### Batch 12: TSL Append and Storage

**Capability**: tsl-append (Priority: P1)
**Spec reference**: specs/tsl-append/spec.md
**C source files**: src/fdb_tsdb.c (append functions: lines 147-555)
**Rust target files**: src/fdb_tsdb.rs
**Dependencies**: Batch 1, 6, 3, 4, 7, 9

**Implementation status**: 0/6 functions complete. All TSL append functions are stubs.

**Implementation functions**:
1. `fn read_tsl(tsdb: &FdbTsdb, addr: u32, tsl: &mut FdbTsl, flash: &dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `read_tsl` in fdb_tsdb.c:147
2. `fn write_tsl(tsdb: &mut FdbTsdb, blob: &FdbBlob, timestamp: FdbTime, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `write_tsl` in fdb_tsdb.c:350 (3-phase: PRE_WRITE, index+data, WRITE)
3. `fn tsdb_update_sec_status(tsdb: &mut FdbTsdb, sec: &mut TsdbSecInfo, blob: &FdbBlob, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `update_sec_status` in fdb_tsdb.c:379
4. `fn tsl_append(tsdb: &mut FdbTsdb, blob: &FdbBlob, timestamp: FdbTime, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `tsl_append` in fdb_tsdb.c:451
5. `fn fdb_tsl_append(tsdb: &mut FdbTsdb, blob: &FdbBlob, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `fdb_tsl_append` in fdb_tsdb.c:509
6. `fn fdb_tsl_append_with_ts(tsdb: &mut FdbTsdb, blob: &FdbBlob, timestamp: FdbTime, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `fdb_tsl_append_with_ts` in fdb_tsdb.c:533

**Data structures**: Uses `FdbTsl`, `FdbBlob`, `TsdbSecInfo` from Batch 1

**Unit tests**: 5 tests covering basic append, monotonic timestamp, sector-full transition, rollover, index/data layout

**Build command**: `cargo build`
**Test command**: `cargo test tsl_append`
**Completion criteria**:
- [ ] `cargo build` passes
- [ ] `cargo test tsl_append` -- all 5 tests pass
- [ ] 3-phase write sequence preserved: PRE_WRITE -> index+data -> WRITE
- [ ] Index entries grow forward from sector top; data grows backward from sector bottom

---

### Batch 13: TSL Iteration and Query

**Capability**: tsl-iteration-query (Priority: P1)
**Spec reference**: specs/tsl-iteration-query/spec.md
**C source files**: src/fdb_tsdb.c (iteration functions: lines 192-227, 556-810)
**Rust target files**: src/fdb_tsdb.rs
**Dependencies**: Batch 1, 6, 9

**Implementation status**: 0/7 functions complete. All TSL iteration/query functions are stubs.

**Implementation functions**:
1. `fn get_next_tsl_addr(tsdb: &FdbTsdb, cur_addr: u32, flash: &dyn FlashStorage) -> u32` -- C equivalent: `get_next_tsl_addr` in fdb_tsdb.c:192
2. `fn get_last_tsl_addr(tsdb: &FdbTsdb, cur_addr: u32, sec: &TsdbSecInfo, flash: &dyn FlashStorage) -> u32` -- C equivalent: `get_last_tsl_addr` in fdb_tsdb.c:210
3. `fn search_start_tsl_addr(tsdb: &FdbTsdb, sec: &TsdbSecInfo, from: FdbTime, to: FdbTime, flash: &dyn FlashStorage) -> Option<u32>` -- C equivalent: `search_start_tsl_addr` in fdb_tsdb.c:654 (binary search within sector)
4. `fn fdb_tsl_iter(tsdb: &FdbTsdb, cb: FdbTslCb, cb_arg: usize, flash: &dyn FlashStorage)` -- C equivalent: `fdb_tsl_iter` in fdb_tsdb.c:556
5. `fn fdb_tsl_iter_reverse(tsdb: &FdbTsdb, cb: FdbTslCb, cb_arg: usize, flash: &dyn FlashStorage)` -- C equivalent: `fdb_tsl_iter_reverse` in fdb_tsdb.c:606
6. `fn fdb_tsl_iter_by_time(tsdb: &FdbTsdb, from: FdbTime, to: FdbTime, cb: FdbTslCb, cb_arg: usize, flash: &dyn FlashStorage)` -- C equivalent: `fdb_tsl_iter_by_time` in fdb_tsdb.c:691
7. `fn fdb_tsl_query_count(tsdb: &FdbTsdb, from: FdbTime, to: FdbTime, status: FdbTslStatus, flash: &dyn FlashStorage) -> usize` -- C equivalent: `fdb_tsl_query_count` in fdb_tsdb.c:790

**Data structures**: Uses `FdbTsl`, `TsdbSecInfo`, `FdbTslCb` from Batch 1

**Unit tests**: 7 tests covering forward, reverse, by_time (forward/reverse), query count, binary search edge cases, empty DB

**Build command**: `cargo build`
**Test command**: `cargo test tsl_iter`
**Completion criteria**:
- [ ] `cargo build` passes
- [ ] `cargo test tsl_iter` -- all 7 tests pass
- [ ] Binary search correctly handles single-TSL sector
- [ ] Reverse iteration correctly crosses sector boundaries

---

### Batch 14: KVDB Garbage Collection

**Capability**: kvdb-garbage-collection (Priority: P2)
**Spec reference**: specs/kvdb-garbage-collection/spec.md
**C source files**: src/fdb_kvdb.c (GC functions: lines 1006-1182)
**Rust target files**: src/fdb_kvdb.rs
**Dependencies**: Batch 8, 10, 11

**Implementation status**: 0/5 functions complete. GC functions are not yet implemented.

**Implementation functions**:
1. `fn move_kv(kvdb: &mut FdbKvdb, from_addr: u32, to_addr: u32, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `move_kv` in fdb_kvdb.c:1006
2. `fn gc_check_cb(kvdb: &FdbKvdb, addr: u32, flash: &dyn FlashStorage) -> bool` -- C equivalent: `gc_check_cb` in fdb_kvdb.c:1098
3. `fn do_gc(kvdb: &mut FdbKvdb, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `do_gc` in fdb_kvdb.c:1112
4. `fn gc_collect(kvdb: &mut FdbKvdb, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `gc_collect` in fdb_kvdb.c:1178
5. `fn gc_collect_by_free_size(kvdb: &mut FdbKvdb, size: usize, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `gc_collect_by_free_size` in fdb_kvdb.c:1153

**Data structures**: Uses `FdbKvdb`, `KvdbSecInfo`, `FdbKv` from Batch 1

**Unit tests**: 4 tests covering move valid KVs, all-deleted sector, collect-by-size, DIRTY_GC recovery

**Build command**: `cargo build`
**Test command**: `cargo test gc`
**Completion criteria**:
- [ ] `cargo build` passes
- [ ] `cargo test gc` -- all 4 tests pass
- [ ] Source sector marked DIRTY_GC before KV move (crash recovery invariant)
- [ ] Moved KVs have identical name/value/CRC32/status

---

### Batch 15: KVDB Crash Recovery and Integrity

**Capability**: kvdb-recovery (Priority: P2)
**Spec reference**: specs/kvdb-recovery/spec.md
**C source files**: src/fdb_kvdb.c (recovery functions: lines 1563-1895)
**Rust target files**: src/fdb_kvdb.rs
**Dependencies**: Batch 8, 10, 14, 11

**Implementation status**: 2/7 functions have partial implementations (init/deinit wrappers). Recovery logic not yet implemented.

**Implementation functions**:
1. `fn check_sec_hdr_cb(kvdb: &mut FdbKvdb, sec_addr: u32, flash: &mut dyn FlashStorage) -> bool` -- C equivalent: `check_sec_hdr_cb` in fdb_kvdb.c:1563
2. `fn check_and_recovery_kv_cb(kvdb: &mut FdbKvdb, kv: &mut FdbKv, blob: &FdbBlob, flash: &mut dyn FlashStorage) -> bool` -- C equivalent: `check_and_recovery_kv_cb` in fdb_kvdb.c:1594
3. `fn check_and_recovery_gc_cb(kvdb: &mut FdbKvdb, sec_addr: u32, flash: &mut dyn FlashStorage) -> bool` -- C equivalent: `check_and_recovery_gc_cb` in fdb_kvdb.c:1604
4. `fn fdb_kv_load(kvdb: &mut FdbKvdb, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `_fdb_kv_load` in fdb_kvdb.c:1616
5. `fn fdb_kvdb_init(kvdb: &mut FdbKvdb, name: &str, path: &str) -> Result<(), FdbError>` (full version with fdb_kv_load) -- C equivalent: `fdb_kvdb_init` in fdb_kvdb.c:1753
6. `fn fdb_kvdb_check(kvdb: &FdbKvdb, flash: &dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `fdb_kvdb_check` in fdb_kvdb.c:1876
7. `fn fdb_kvdb_control(kvdb: &mut FdbKvdb, cmd: u32, arg: usize)` -- C equivalent: `fdb_kvdb_control` in fdb_kvdb.c:1895

**Data structures**: Uses `FdbKvdb`, `FdbKv`, `KvdbSecInfo` from Batch 1

**Unit tests**: 6 tests covering PRE_WRITE repair, PRE_DELETE move, DIRTY_GC resume, auto-format, integrity check, idempotency

**Build command**: `cargo build`
**Test command**: `cargo test recovery`
**Completion criteria**:
- [ ] `cargo build` passes
- [ ] `cargo test recovery` -- all 6 tests pass
- [ ] PRE_WRITE -> ERR_HDR transition correct
- [ ] PRE_DELETE -> move KV to new location preserves data
- [ ] DIRTY_GC -> do_gc resume completes interrupted GC
- [ ] Recovery runs automatically on init, before init_ok flag

---

### Batch 16: TSL Status Management and Cleanup

**Capability**: tsl-status-cleanup (Priority: P2)
**Spec reference**: specs/tsl-status-cleanup/spec.md
**C source files**: src/fdb_tsdb.c (status/cleanup functions: lines 816-1092)
**Rust target files**: src/fdb_tsdb.rs
**Dependencies**: Batch 12, 9

**Implementation status**: 2/5 functions have partial implementations. tsl_to_blob sets blob.size (needs saved_addr). tsl_set_status, tsl_clean, tsl_format_all, tsdb_control are stubs.

**Implementation functions**:
1. `fn fdb_tsl_set_status(tsdb: &mut FdbTsdb, tsl: &mut FdbTsl, status: FdbTslStatus, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `fdb_tsl_set_status` in fdb_tsdb.c:816
2. `fn tsl_format_all(tsdb: &mut FdbTsdb, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` -- C equivalent: `tsl_format_all` in fdb_tsdb.c:880
3. `fn fdb_tsl_clean(tsdb: &mut FdbTsdb, flash: &mut dyn FlashStorage)` -- C equivalent: `fdb_tsl_clean` in fdb_tsdb.c:902
4. `fn fdb_tsl_to_blob(tsl: &FdbTsl, blob: &mut FdbBlob)` (complete: add saved_addr/saved_len) -- C equivalent: `fdb_tsl_to_blob` in fdb_tsdb.c:835
5. `fn fdb_tsdb_control(tsdb: &mut FdbTsdb, cmd: u32, arg: usize)` -- C equivalent: `fdb_tsdb_control` in fdb_tsdb.c:916

**Data structures**: Uses `FdbTsl`, `FdbBlob`, `FdbTsdb` from Batch 1

**Unit tests**: 5 tests covering set_status, clean irreversibility, to_blob metadata, control commands

**Build command**: `cargo build`
**Test command**: `cargo test tsl_status`
**Completion criteria**:
- [ ] `cargo build` passes
- [ ] `cargo test tsl_status` -- all 5 tests pass
- [ ] Status transitions monotonic; DELETED is terminal
- [ ] fdb_tsl_clean irreversibly erases all data

---

### Batch 17: Test Migration and Integration

**Capability**: test-migration (Priority: Integration)
**Spec reference**: specs/test-migration/spec.md
**C source files**: tests/fdb_kvdb_tc.c (979 lines, 15 test + 3 helper + 2 infra), tests/fdb_tsdb_tc.c (518 lines, 11 test + 1 helper + 2 infra)
**Rust target files**: tests/kvdb_tests.rs, tests/tsdb_tests.rs
**Dependencies**: Batches 1-16 (all capabilities must be complete)

**Implementation status**: 0/30 test functions migrated. 13 existing unit tests in tests/source_migration.rs for P0 capabilities.

**C test functions to migrate**:

KVDB (15 tests + 3 helpers):
1. test_fdb_kvdb_init -> test_kvdb_init
2. test_fdb_kvdb_init_by_8_sectors -> test_kvdb_init_by_8_sectors
3. test_fdb_kvdb_init_by_sector_num -> test_kvdb_init_by_sector_num
4. test_fdb_kvdb_init_check -> test_kvdb_init_check
5. test_fdb_kvdb_deinit -> test_kvdb_deinit
6. test_fdb_create_kv_blob -> test_kvdb_create_kv_blob
7. test_fdb_change_kv_blob -> test_kvdb_change_kv_blob
8. test_fdb_del_kv_blob -> test_kvdb_del_kv_blob
9. test_fdb_create_kv -> test_kvdb_create_kv
10. test_fdb_change_kv -> test_kvdb_change_kv
11. test_fdb_del_kv -> test_kvdb_del_kv
12. test_fdb_gc -> test_kvdb_gc
13. test_fdb_gc2 -> test_kvdb_gc2
14. test_fdb_kvdb_set_default -> test_kvdb_set_default
15. test_fdb_scale_up -> test_kvdb_scale_up
    + helpers: test_save_fdb_by_kvs, test_check_fdb_by_kvs, test_fdb_by_kvs

TSDB (11 tests + 1 helper):
1. test_fdb_tsdb_init_ex -> test_tsdb_init_ex
2. test_fdb_tsdb_deinit -> test_tsdb_deinit
3. test_fdb_tsl_append -> test_tsl_append
4. test_fdb_tsl_iter -> test_tsl_iter
5. test_fdb_tsl_iter_by_time -> test_tsl_iter_by_time
6. test_fdb_tsl_iter_by_time_1 -> test_tsl_iter_by_time_1
7. test_fdb_tsl_query_count -> test_tsl_query_count
8. test_fdb_tsl_set_status -> test_tsl_set_status
9. test_fdb_tsl_clean -> test_tsl_clean
10. test_fdb_tsl_sector_bound_test -> test_tsl_sector_bound
11. test_fdb_github_issue_249 -> test_tsl_github_issue_249
    + helper: test_tsdb_data_by_time

**Test infrastructure**:
- RT-Thread utest (C) -> Rust `#[test]` + setup/teardown via temp directories
- FAL partition simulation (C) -> RamFlash (in-memory FlashStorage)
- uassert_* macros (C) -> assert!/assert_eq! macros (Rust)

**Build command**: `cargo build`
**Test command**: `cargo test`
**Completion criteria**:
- [ ] `cargo build` passes (no warnings)
- [ ] `cargo test kvdb` -- all 15 migrated KVDB tests + 3 helpers pass
- [ ] `cargo test tsdb` -- all 11 migrated TSDB tests + 1 helper pass
- [ ] `cargo test` -- full suite: 24 migrated tests + 13 existing unit tests all pass
- [ ] Additional crash recovery tests (REQ-TEST-008 through 010) optionally added

---

## Gate Summary

| Gate | Batch | Build | Test | Criteria |
|------|-------|-------|------|----------|
| Gate A | 1-2 | cargo build | cargo test | Types and CRC32 compile and test |
| Gate B | 3-6 | cargo build | cargo test status/blob/file/flash | P0 utilities compile and test |
| Gate C | 7 | cargo build | cargo test init | Lifecycle compiles and tests |
| Gate D | 8-11 | cargo build | cargo test sector/kv_crud/iterate | KVDB operations compile and test |
| Gate E | 9, 12-13 | cargo build | cargo test tsdb_init/tsl_append/tsl_iter | TSDB operations compile and test |
| Gate F | 14-16 | cargo build | cargo test gc/recovery/tsl_status | P2 features compile and test |
| Gate G | 17 | cargo test | Full suite | All 30+ migrated tests pass |

## Unsafe Budget Tracking

| Module | Target Lines | Target Unsafe Lines | Target % |
|--------|-------------|--------------------|----|
| fdb_def.rs | 300 | 0 | 0% |
| fdb_low_lvl.rs | 40 | 0 | 0% |
| fdb_cfg_template.rs | 15 | 0 | 0% |
| fdb_utils.rs | 500 | 0 | 0% |
| ports.rs | 80 | 0 | 0% |
| fdb_file.rs | 300 | 0 | 0% |
| fdb.rs | 150 | 0 | 0% |
| fdb_kvdb.rs | 1,800 | 20 | 1.1% |
| fdb_tsdb.rs | 1,000 | 15 | 1.5% |
| flashdb.rs | 30 | 0 | 0% |
| **Total** | **~4,215** | **~35** | **~0.83%** |
