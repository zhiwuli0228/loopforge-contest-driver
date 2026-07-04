# Implementation Plan: c2r-flashdb

## Overview

Migrate FlashDB (~3,900 lines C) to Rust crate `flashdb_rust` in 8 batches, each independently buildable.

**Output**: `work/output/flashdb_rust/`  
**Specs**: fdb-core, fdb-utils, fdb-file, fdb-kvdb, fdb-tsdb, test-migration  
**Design**: `design.md`

---

## Batch 0: Project Scaffolding

**Specs mapped**: fdb-core (types, config constants)

**Files to create**:
- `Cargo.toml` — crate metadata, features (`file-mode-posix`, `timestamp-64bit`)
- `src/config.rs` — all compile-time constants
- `src/lib.rs` — module declarations, re-exports (empty modules)
- `tests/` — directory, `tests/mod.rs` (empty)

**Functions/items** (8):
1. `Cargo.toml` with `[lib]`, `[dependencies]`, `[features]`, `[[test]]` sections
2. `config.rs`: `FDB_WRITE_GRAN`, `FDB_KV_NAME_MAX`, `FDB_STR_KV_VALUE_MAX_SIZE`, `SECTOR_MAGIC_WORD`, `SECTOR_NOT_COMBINED`, `FDB_FILE_CACHE_TABLE_SIZE`, `FDB_SECTOR_SIZE`, `BUF_SIZE`, `DB_PATH_MAX`, `FDB_BYTE_ERASED`, `FDB_BYTE_WRITTEN`, `FDB_GC_EMPTY_SEC_THRESHOLD`, `FDB_SEC_REMAIN_THRESHOLD`, `FAILED_ADDR`
3. `config.rs`: `FDB_KV_STATUS_NUM`, `FDB_SECTOR_STORE_STATUS_NUM`, `FDB_SECTOR_DIRTY_STATUS_NUM`, `FDB_TSL_STATUS_NUM`
4. `config.rs`: `FDB_STATUS_TABLE_SIZE(total_num)` macro as const fn
5. `config.rs`: `FDB_WG_ALIGN(addr)` and `FDB_WG_ALIGN_DOWN(size)` const fns
6. `lib.rs`: module declarations (`mod config; mod db; mod kvdb; mod tsdb; mod file; mod utils;`)
7. `lib.rs`: re-exports stub
8. `tests/mod.rs`: empty test module file

**Build gate**:
```bash
cargo build
```

---

## Batch 1: Core Types

**Specs mapped**: fdb-core (FdbError, FdbDbType, FdbDb, FdbBlob, FdbKv, FdbTsl, FdbKvIterator, SectorHdrKv, SectorHdrTs, FdbTime, status enums)

**Dependencies**: Batch 0

**Files to modify/create**:
- `src/config.rs` — add type definitions
- `src/lib.rs` — re-export types

**Functions/items** (11):
1. `FdbError` enum — 9 variants, derive Debug/Clone/Copy/PartialEq/Eq
2. `FdbDbType` enum — Kv, Ts
3. `FdbDb` struct — name, db_type, sec_size, max_size, oldest_addr, init_ok, file_mode, not_formatable, user_data, storage fields
4. `FdbBlob` struct — buf (Vec<u8>), size, saved (meta_addr, addr, len)
5. `FdbKv` struct — status, crc_is_ok, name_len, magic, len, value_len, name (String), addr_start, addr_value
6. `FdbTsl` struct — status, time (FdbTime), log_len, addr_index, addr_log
7. `FdbKvIterator` struct — curr_kv, iterated_cnt, iterated_obj_bytes, iterated_value_bytes, sector_addr, traversed_len
8. `SectorHdrKv` struct — `#[repr(C)]`, store_status, dirty_status, magic, combined, empty_kv, remain
9. `SectorHdrTs` struct — `#[repr(C)]`, store_status, magic, start_time, end_info[2]
10. `TsEndInfo` struct — `#[repr(C)]`, time, index, status
11. Status enums: `FdbKvStatus` (Unused, PreWrite, Write, PreDelete, Deleted, ErrHdr), `FdbTslStatus` (Unused, PreWrite, Write, UserStatus1, Deleted, UserStatus2), `FdbSectorStoreStatus` (Unused, Empty, Using, Full), `FdbSectorDirtyStatus` (Unused, False, True, Gc)

**Build gate**:
```bash
cargo build
```

---

## Batch 2: Core Lifecycle (db.rs)

**Specs mapped**: fdb-core (init_ex, init_finish, deinit, db_path, validation)

**Dependencies**: Batches 0-1

**Files to modify/create**:
- `src/db.rs` — FdbDb impl methods

**Functions** (5):
1. `_fdb_init_ex(db, name, path, db_type, user_data)` — assertions, metadata init, file cache init
2. `_fdb_init_finish(db, result)` — set init_ok, version banner (static Once guard)
3. `_fdb_deinit(db)` — close file descriptors, reset init_ok
4. `_fdb_db_path(db)` — return path for file mode or FAL mode
5. Init validation helpers: `is_power_of_two(n)`, `validate_sector_config(sec_size, max_size)`

**Build gate**:
```bash
cargo build
```

---

## Batch 3: Utils (utils.rs)

**Specs mapped**: fdb-utils (CRC32, status table set/get, write/read status, continue_ff_addr, blob, FlashIo trait, flash dispatch, aligned write)

**Dependencies**: Batches 0-2

**Files to modify/create**:
- `src/utils.rs` — CRC32, status tables, blob, flash abstraction

**Functions** (8):
1. `CRC32_TABLE: [u32; 256]` — static lookup table matching C source
2. `calc_crc32(crc: u32, buf: &[u8]) -> u32`
3. `_fdb_set_status(status_table, status_num, status_index)` — all 6 WRITE_GRAN variants
4. `_fdb_get_status(status_table, status_num)` — all 6 WRITE_GRAN variants
5. `_fdb_write_status(db, addr, status_table, status_num, index, sync)` — set + flash write
6. `_fdb_read_status(db, addr, status_table, total_num)` — flash read + get
7. `_fdb_continue_ff_addr(db, start, end) -> u32`
8. `Blob::new(buf, len)` and `Blob::read(db) -> usize`

**Build gate**:
```bash
cargo build
```

---

## Batch 4: Flash Abstraction + File I/O

**Specs mapped**: fdb-file (FlashIo trait, FileFlashIo, POSIX read/write/erase, fd cache, file path gen, flash dispatch, aligned write), fdb-utils (flash dispatch)

**Dependencies**: Batches 0-3

**Files to modify/create**:
- `src/utils.rs` — add FlashIo trait, flash dispatch functions
- `src/file.rs` — FileFlashIo struct, POSIX I/O impl

**Functions** (8):
1. `FlashIo` trait definition (read, write, erase methods)
2. `FileFlashIo` struct + `new(dir, sec_size)` constructor
3. `_fdb_flash_read(db, addr, buf, size)` — dispatch to file mode
4. `_fdb_flash_write(db, addr, buf, size, sync)` — dispatch to file mode
5. `_fdb_flash_erase(db, addr, size)` — dispatch to file mode
6. `_fdb_flash_write_align(db, addr, buf, size)` — aligned write with pad buffer
7. `_fdb_file_read(db, addr, buf, size)` — fd cache + lseek + read
8. `_fdb_file_write(db, addr, buf, size, sync)` — fd cache + lseek + write + fsync

**Build gate**:
```bash
cargo build --features file-mode-posix
```

---

## Batch 5: File I/O Continued + Fd Cache

**Specs mapped**: fdb-file (fd cache, erase, path generation, LIBC mode stubs)

**Dependencies**: Batch 4

**Files to modify/create**:
- `src/file.rs` — remaining file I/O

**Functions** (6):
1. `_fdb_file_erase(db, addr, size)` — truncate + fill 0xFF + fsync
2. `_fdb_file_fd_open(db, addr, clean)` — fd cache lookup + open
3. `_fdb_file_fd_close(db, fd)` — close fd + clear cache entry
4. `_fdb_file_path(db, addr)` — generate `<dir>/<name>.fdb.<idx>` path
5. Fd cache insert with LRU-shift eviction
6. `FlashIo` impl for `FileFlashIo`

**Build gate**:
```bash
cargo build --features file-mode-posix
```

---

## Batch 6: KVDB Engine — Sector Management + CRUD

**Specs mapped**: fdb-kvdb (init, sector format, recovery, CRUD, sector allocation, control)

**Dependencies**: Batches 0-5

**Files to modify/create**:
- `src/kvdb.rs` — KvDb struct, sector ops, CRUD

**Functions** (8):
1. `KvDb` struct definition with KV-specific fields
2. `kvdb_init(name, path, default_kvs, user_data)` — format + recovery
3. `_fdb_kv_sec_info_read(db, sector)` — read sector header + statuses
4. `_fdb_kv_sec_info_write(db, sector)` — write sector header
5. `_fdb_kv_set_ex(db, name, value)` — KV header write, CRC32, status transitions
6. `_fdb_kv_search(db, name)` — sector traversal + cache lookup
7. `KvDb::get(key) -> Option<String>` + `KvDb::get_blob(key, blob) -> usize`
8. `KvDb::del(key) -> Result<(), FdbError>` — PRE_DELETE → DELETED

**Build gate**:
```bash
cargo build --features file-mode-posix
```

---

## Batch 7: KVDB Engine — Cache, Iterator, GC

**Specs mapped**: fdb-kvdb (cache, iterator, GC, print, set_default, control)

**Dependencies**: Batch 6

**Files to modify/create**:
- `src/kvdb.rs` — remaining KVDB methods

**Functions** (8):
1. `_fdb_kv_cache_search(db, name)` — CRC16 hash + cache lookup
2. `_fdb_kv_cache_insert(db, addr, name)` — insert with LRU eviction
3. `_fdb_kv_iter_next(itr, db) -> bool` — advance iterator
4. `gc_collect(db)` + `gc_collect_by_free_size(db, free_size)` — GC entry points
5. `do_gc(db, sec_addr)` — move live KVs, erase, reformat
6. `KvDb::set(key, value)` + `KvDb::set_blob(key, blob)` — public API
7. `KvDb::control()` — set_sec_size, set_max_size, set_file_mode, set_not_formatable
8. `KvDb::deinit()` + `KvDb::set_default()` + `KvDb::print()`

**Build gate**:
```bash
cargo build --features file-mode-posix
```

---

## Batch 8: TSDB Engine — Init + Append + Rollover

**Specs mapped**: fdb-tsdb (init, sector management, append, sector rollover, crash resilience)

**Dependencies**: Batches 0-5 (file/DB/utils foundations)

**Files to modify/create**:
- `src/tsdb.rs` — TsDb struct, sector ops, append logic

**Functions** (7):
1. `TsDb` struct definition with TS-specific fields (cur_sec, rollover, get_time, last_time, max_len)
2. `tsdb_init(name, path, get_time_fn, max_len, user_data)` — format + recovery
3. `_fdb_tsl_sec_info_read(db, sector)` — read TSDB sector header + end_info
4. `_fdb_tsl_sec_info_write(db, sector)` — write TSDB sector header
5. `TsDb::append(blob)` — auto-timestamp, TSL index+data write, sector rollover
6. `TsDb::append_with_ts(blob, ts)` — explicit timestamp append
7. Sector rollover logic: finalize current sector (end_info[0],[1]), format/reuse next sector

**Build gate**:
```bash
cargo build --features file-mode-posix
```

---

## Batch 9: TSDB Engine — Iteration + Query + Clean

**Specs mapped**: fdb-tsdb (iteration, query_count, set_status, clean, control)

**Dependencies**: Batch 8

**Files to modify/create**:
- `src/tsdb.rs` — remaining TSDB methods

**Functions** (8):
1. `TsDb::iter(callback, arg)` — forward iteration across sectors
2. `TsDb::iter_reverse(callback, arg)` — reverse iteration
3. `TsDb::iter_by_time(from, to, callback, arg)` — time-range filtering with sector skip
4. `TsDb::query_count(from, to, status_filter) -> usize`
5. `TsDb::set_status(tsl, new_status)` — write-once status update
6. `TsDb::clean()` — mark all TSLs DELETED, reset to fresh sector
7. `TsDb::control()` — set_sec_size, set_rollover, get_last_time
8. `TsDb::deinit()` — cleanup

**Build gate**:
```bash
cargo build --features file-mode-posix
```

---

## Batch 10: KVDB Test Migration

**Specs mapped**: test-migration (13 KVDB test functions)

**Dependencies**: Batches 0-7 (full KVDB engine)

**Files to modify/create**:
- `tests/kvdb_tests.rs` — test helpers + 13 test functions

**Test functions** (13):
1. `kvdb_init` — basic init with sector count verification
2. `kvdb_deinit` — deinit cleanup verification
3. `kvdb_init_check` — re-init cycle survival
4. `kvdb_create_kv_blob` — blob create + read-back
5. `kvdb_change_kv_blob` — blob update + old status check
6. `kvdb_del_kv_blob` — blob delete + read-back returns None
7. `kvdb_create_kv` — string KV create + CRC32 verification
8. `kvdb_change_kv` — string KV update + deinit/reinit cycle
9. `kvdb_del_kv` — string KV deletion
10. `kvdb_gc` — full GC cycle verification
11. `kvdb_gc2` — GC with exact 3-KVs-per-sector layout
12. `kvdb_scale_up` — sector count increase between cycles
13. `kvdb_set_default` — default KV provisioning

**Build gate**:
```bash
cargo test --features file-mode-posix kvdb_
```

---

## Batch 11: TSDB Test Migration

**Specs mapped**: test-migration (11 TSDB test functions)

**Dependencies**: Batches 0-5, 8-9 (full TSDB engine)

**Files to modify/create**:
- `tests/tsdb_tests.rs` — test helpers + 12 test functions

**Test functions** (12):
1. `tsdb_init` — basic TSDB init with sector count
2. `tsdb_deinit` — deinit + re-init cycle
3. `tsdb_append` — append TSLs + timestamp verification
4. `tsdb_iter` — forward iteration count verification
5. `tsdb_iter_by_time` — time-range filtering with boundary tests
6. `tsdb_query_count` — query count with status filters
7. `tsdb_set_status` — status transition + filtered query
8. `tsdb_clean` (first) — clean all TSLs
9. `tsdb_clean_after_set_status` — clean after status manipulation
10. `tsdb_iter_by_time_1` — time-range across 5-sector boundaries
11. `tsdb_github_issue_249` — edge case regression test

**Build gate**:
```bash
cargo test --features file-mode-posix tsdb_
```

---

## Batch 12: Integration, Audit & Polish

**Specs mapped**: fdb-core (lib.rs re-exports, public API), test-migration (write-granularity param, unsafe audit)

**Dependencies**: All previous batches

**Files to modify/create**:
- `src/lib.rs` — final re-exports, version banner, public API surface

**Tasks** (8):
1. Finalize `src/lib.rs` public API re-exports
2. `cargo build` — verify all features compile
3. `cargo clippy --features file-mode-posix` — fix warnings
4. `cargo test --features file-mode-posix` — all 24 tests pass
5. Audit unsafe code: count lines, ensure <10%
6. Verify `#[repr(C)]` struct sizes against C `sizeof()` with const assertions
7. Verify CRC32 table byte-for-byte match with C source
8. Write-granularity parameterized tests for status table operations (WG=1,8,32,64,128,256)

**Final gate**:
```bash
cargo build --features file-mode-posix
cargo clippy --features file-mode-posix
cargo test --features file-mode-posix
```

---

## Batch Dependency Graph

```
Batch 0 (scaffolding)
  └─► Batch 1 (core types)
       └─► Batch 2 (db lifecycle)
            └─► Batch 3 (utils: CRC32, status, blob)
                 └─► Batch 4 (flash abstraction + file I/O part 1)
                      └─► Batch 5 (file I/O part 2: fd cache, erase)
                           ├─► Batch 6 (KVDB: sector mgmt + CRUD)
                           │    └─► Batch 7 (KVDB: cache + iterator + GC)
                           │         └─► Batch 10 (KVDB tests)
                           │
                           ├─► Batch 8 (TSDB: init + append + rollover)
                           │    └─► Batch 9 (TSDB: iteration + query + clean)
                           │         └─► Batch 11 (TSDB tests)
                           │
                           └─► Batch 12 (integration, audit, polish)
                                (depends on 10 + 11)
```

**Parallelism note**: After Batch 5, KVDB (Batchers 6-7) and TSDB (Batchers 8-9) can be developed in parallel. Test batches (10-11) follow their respective engine completions.

---

## Build/Test Commands per Batch

| Batch | Build Command | Test Command |
|-------|--------------|--------------|
| 0 | `cargo build` | — |
| 1 | `cargo build` | — |
| 2 | `cargo build` | — |
| 3 | `cargo build` | — |
| 4 | `cargo build --features file-mode-posix` | — |
| 5 | `cargo build --features file-mode-posix` | — |
| 6 | `cargo build --features file-mode-posix` | — |
| 7 | `cargo build --features file-mode-posix` | — |
| 8 | `cargo build --features file-mode-posix` | — |
| 9 | `cargo build --features file-mode-posix` | — |
| 10 | `cargo build --features file-mode-posix` | `cargo test --features file-mode-posix kvdb_` |
| 11 | `cargo build --features file-mode-posix` | `cargo test --features file-mode-posix tsdb_` |
| 12 | `cargo build --features file-mode-posix` | `cargo test --features file-mode-posix` |
