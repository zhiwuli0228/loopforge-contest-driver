# Spec: Foundational Data Types and Constants

## Capability Overview

This capability defines all core type definitions shared across the FlashDB codebase: enums for error codes, KV/TSL/sector statuses, and database type; structs for KV nodes, TSL nodes, blobs, sector info, iterators, and the database base structure; and compile-time constants for sector sizes, cache table sizes, name lengths, and write granularity. These types are the foundation upon which all other capabilities build. The Rust equivalent is defined in `fdb_def.rs`, `fdb_low_lvl.rs`, and `fdb_cfg_template.rs`.

## Key Functions

N/A -- This capability defines only types, constants, and data structures. It has no executable functions.

## Data Structures

| C Struct | Fields | Rust Equivalent | Notes |
|----------|--------|----------------|-------|
| `fdb_db` | `name[DB_NAME_MAX]`, `type`, `storage` (union of `fal_part`/`dir`), `sec_size`, `max_size`, `oldest_addr`, `init_ok`, `file_mode`, `not_formatable`, `cur_file_sec[]`, `cur_file[]`, `lock`, `unlock`, `user_data` | `FdbDb { name: String, db_type: FdbDbType, storage_path: String, sec_size: u32, max_size: u32, oldest_addr: u32, init_ok: bool, file_mode: bool, not_formatable: bool }` | C union replaced by `String` for file mode only; FAL mode deferred. `lock`/`unlock` function pointers deferred (single-threaded). `cur_file[]`/`cur_file_sec[]` handled by `FileCache` in `fdb_file.rs`. |
| `fdb_kvdb` | `parent: fdb_db`, `default_kvs`, `gc_request`, `in_recovery_check`, `cur_kv`, `cur_sector`, `last_is_complete_del`, `kv_cache_table[]`, `sector_cache_table[]`, `ver_num`, `user_data` | `FdbKvdb { parent: FdbDb, default_kvs: FdbDefaultKv, gc_request: bool, in_recovery_check: bool, cur_kv: FdbKv, cur_sector: KvdbSecInfo, last_is_complete_del: bool, kv_cache_table: Vec<KvCacheNode>, sector_cache_table: Vec<KvdbSecInfo>, ver_num: u32 }` | C struct "inheritance" via embedding becomes Rust composition (`parent: FdbDb`). Fixed-size arrays become `Vec` for flexibility. |
| `fdb_tsdb` | `parent: fdb_db`, `cur_sec`, `last_time`, `get_time` (fn ptr), `max_len`, `rollover`, `user_data` | `FdbTsdb { parent: FdbDb, cur_sec: TsdbSecInfo, last_time: FdbTime, max_len: usize, rollover: bool }` | `get_time` callback deferred for single-threaded initial release. |
| `fdb_kv` | `status`, `crc_is_ok`, `name_len`, `magic`, `len`, `value_len`, `name[FDB_KV_NAME_MAX]`, `addr.start`, `addr.value` | `FdbKv { status: FdbKvStatus, crc_is_ok: bool, name_len: u8, magic: u32, len: u32, value_len: u32, name: [u8; FDB_KV_NAME_MAX], addr_start: u32, addr_value: u32 }` | `repr(C)` required for byte-buffer deserialization. C nested `addr.start`/`addr.value` flattened to `addr_start`/`addr_value`. |
| `fdb_tsl` | `status`, `time`, `log_len`, `addr.index`, `addr.log` | `FdbTsl { status: FdbTslStatus, time: FdbTime, log_len: u32, addr_index: u32, addr_log: u32 }` | `repr(C)` required. C nested `addr` struct flattened. |
| `fdb_blob` | `buf` (void*), `size`, `saved.meta_addr`, `saved.addr`, `saved.len` | `FdbBlob { buf: Vec<u8>, size: usize, saved_meta_addr: u32, saved_addr: u32, saved_len: usize }` | C `void*` buffer replaced by owned `Vec<u8>`. |
| `fdb_kv_iterator` | `curr_kv`, `iterated_cnt`, `iterated_obj_bytes`, `iterated_value_bytes`, `sector_addr`, `traversed_len` | `FdbKvIterator { curr_kv: FdbKv, iterated_cnt: u32, iterated_obj_bytes: usize, iterated_value_bytes: usize, sector_addr: u32, traversed_len: u32 }` | |
| `kvdb_sec_info` | `check_ok`, `status.store`, `status.dirty`, `addr`, `magic`, `combined`, `remain`, `empty_kv` | `KvdbSecInfo { check_ok: bool, store_status: FdbSectorStoreStatus, dirty_status: FdbSectorDirtyStatus, addr: u32, magic: u32, combined: u32, remain: usize, empty_kv: u32 }` | `repr(C)` required. |
| `tsdb_sec_info` | `check_ok`, `status`, `addr`, `magic`, `start_time`, `end_time`, `end_idx`, `end_info_stat[2]`, `remain`, `empty_idx`, `empty_data` | `TsdbSecInfo { check_ok: bool, status: FdbSectorStoreStatus, addr: u32, magic: u32, start_time: FdbTime, end_time: FdbTime, end_idx: u32, end_info_stat: [FdbTslStatus; 2], remain: usize, empty_idx: u32, empty_data: u32 }` | `repr(C)` required. |
| `kv_cache_node` | `name_crc: u16`, `active: u16`, `addr: u32` | `KvCacheNode { name_crc: u16, active: u16, addr: u32 }` | |
| `fdb_default_kv` | `kvs: *fdb_default_kv_node`, `num: size_t` | `FdbDefaultKv { kvs: Vec<FdbDefaultKvNode>, num: usize }` | C pointer array replaced by `Vec`. |

### Scalar Mappings

| C Type | Rust Type |
|--------|----------|
| `fdb_err_t` (enum) | `FdbError` (enum, `#[repr(i32)]` implicit by discriminant) |
| `fdb_kv_status_t` | `FdbKvStatus` |
| `fdb_tsl_status_t` | `FdbTslStatus` |
| `fdb_sector_store_status_t` | `FdbSectorStoreStatus` |
| `fdb_sector_dirty_status_t` | `FdbSectorDirtyStatus` |
| `fdb_db_type` | `FdbDbType` |
| `fdb_time_t` | `FdbTime` (type alias: `i64` for 64-bit, `i32` for 32-bit) |
| `uint32_t` | `u32` |
| `uint16_t` | `u16` |
| `uint8_t` | `u8` |
| `size_t` | `usize` |
| `bool` | `bool` |
| `char*` | `String` (owned) |
| `const char*` | `&str` |
| `void*` | `usize` (opaque user_data) |

### Key Constants

| C Constant | Rust Equivalent | Value |
|------------|----------------|-------|
| `FDB_KV_NAME_MAX` | `FDB_KV_NAME_MAX` | 64 |
| `FDB_KV_CACHE_TABLE_SIZE` | `FDB_KV_CACHE_TABLE_SIZE` | 64 |
| `FDB_SECTOR_CACHE_TABLE_SIZE` | `FDB_SECTOR_CACHE_TABLE_SIZE` | 8 |
| `FDB_FILE_CACHE_TABLE_SIZE` | `FDB_FILE_CACHE_TABLE_SIZE` | 2 |
| `SECTOR_MAGIC_WORD` (0x30424446) | `SECTOR_MAGIC_WORD` | `0x30424446u32` |
| `KV_MAGIC_WORD` (0x32424446) | `KV_MAGIC_WORD` | `0x32424446u32` |
| `TSL_MAGIC_WORD` (0x33424446) | `TSL_MAGIC_WORD` | `0x33424446u32` |
| `FDB_WRITE_GRAN` | `FDB_WRITE_GRAN` | configurable: 1, 8, 32, 64, 128, or 256 |

## Requirements

### REQ-foundational-types-001: FdbError enum SHALL map one-to-one with C `fdb_err_t` values

C source reference: `inc/fdb_def.h`

Scenario (normal path):
  GIVEN any operation that produces a known error code in C
  WHEN the Rust equivalent operation runs
  THEN the returned `FdbError` discriminant SHALL equal the C `fdb_err_t` integer value

Scenario (error path):
  GIVEN an unknown or unexpected error code value
  WHEN converting from a raw integer to `FdbError`
  THEN the conversion SHALL either produce a valid variant or panic for truly invalid values (undefined behavior like C)

Scenario (boundary condition):
  GIVEN the discriminant value `FDB_NO_ERR == 0`
  WHEN comparing `FdbError::NoErr as i32`
  THEN it SHALL equal `0`

### REQ-foundational-types-002: FdbDb struct SHALL represent all required fields for file-mode operation

C source reference: `inc/fdb_def.h` (struct `fdb_db`)

Scenario (normal path):
  GIVEN an `FdbDb` is created with `Default`
  WHEN all required fields (name, sec_size, max_size, storage_path) are set
  THEN `fdb_init_ex` SHALL validate and accept the configuration

Scenario (error path):
  GIVEN an `FdbDb` is created with zero `sec_size` in file mode
  WHEN `fdb_init_ex` is called
  THEN the function SHALL return `Err(FdbError::InitFailed)`

Scenario (boundary condition):
  GIVEN `sec_size` is `4096` and `max_size` is `8192`
  WHEN `init_ok` is set to `true`
  THEN `oldest_addr` SHALL default to `0` until sector layout is determined

### REQ-foundational-types-003: Status enums SHALL preserve all C enum discriminants

C source reference: `inc/fdb_def.h`

Scenario (normal path):
  GIVEN `FdbKvStatus::Unused` is the default variant
  WHEN checking `(FdbKvStatus::Unused as i32)`
  THEN it SHALL equal `0`

Scenario (error path):
  GIVEN an unrecognized status byte is read from flash
  WHEN status table decoding returns a value outside the known range
  THEN the system SHALL either map it to a known variant or mark the sector/KV as corrupt (e.g., `FdbKvStatus::ErrHdr`)

Scenario (boundary condition):
  GIVEN `FdbKvStatus` has 6 variants (0-5)
  WHEN `FDB_KV_STATUS_NUM == 6` is used for status table sizing
  THEN status index `5` (`ErrHdr`) SHALL be a valid, settable state

## Invariants

- **INV-foundational-types-001**: All structs read from flash byte buffers (`FdbKv`, `FdbTsl`, `KvdbSecInfo`, `TsdbSecInfo`) SHALL be annotated `#[repr(C)]` with field order matching the C struct layout exactly.
- **INV-foundational-types-002**: `FdbDb` SHALL always have `max_size` as a multiple of `sec_size` after successful initialization.
- **INV-foundational-types-003**: `FdbKv.name` buffer SHALL always be `FDB_KV_NAME_MAX` (64) bytes in size, with unused bytes set to 0.

## Dependencies

None -- This is the root P0 capability. All other capabilities depend on these types.
