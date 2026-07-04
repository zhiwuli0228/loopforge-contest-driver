## Implementation Tasks

### 1. Project Scaffolding

- [ ] 1.1 Create `Cargo.toml` with crate name `flashdb_rust`, edition 2021, dependencies, `file-mode-posix` feature flag
- [ ] 1.2 Create `src/lib.rs` with module declarations (`db`, `kvdb`, `tsdb`, `file`, `utils`) and re-exports
- [ ] 1.3 Create `src/config.rs` with constants (`FDB_WRITE_GRAN`, `FDB_KV_NAME_MAX`, `FDB_STR_KV_VALUE_MAX_SIZE`, `SECTOR_MAGIC_WORD`, `SECTOR_NOT_COMBINED`, `FDB_FILE_CACHE_TABLE_SIZE`, `FDB_SECTOR_SIZE`, `BUF_SIZE`, etc.)
- [ ] 1.4 Create `tests/` directory structure with mod files for integration tests

### 2. Core Types

- [ ] 2.1 Define `FdbError` enum (NoErr, EraseErr, ReadErr, WriteErr, PartNotFound, KvNameErr, KvNameExist, SavedFull, InitFailed) with Debug, Clone, Copy, PartialEq, Eq
- [ ] 2.2 Define `FdbDbType` enum (Kv, Ts)
- [ ] 2.3 Define `FdbDb` base struct with fields: name, db_type, sec_size, max_size, oldest_addr, init_ok, file_mode, not_formatable, user_data, storage fields
- [ ] 2.4 Define `FdbBlob` struct with owned buffer (`Vec<u8>`), size, saved metadata (meta_addr, addr, len)
- [ ] 2.5 Define `FdbKv` struct with status, crc_is_ok, name_len, magic, len, value_len, owned name (String), addr_start, addr_value
- [ ] 2.6 Define `FdbTsl` struct with status, time, log_len, addr_index, addr_log
- [ ] 2.7 Define `FdbKvIterator` struct with curr_kv, iterated_cnt, iterated_obj_bytes, iterated_value_bytes, sector_addr, traversed_len
- [ ] 2.8 Define sector header structs for KVDB (`SectorHdrKv`) and TSDB (`SectorHdrTs`) with `#[repr(C)]`
- [ ] 2.9 Define TSL end-info struct with time, index, status fields
- [ ] 2.10 Define `FdbTime` type alias (i32 default, i64 under `timestamp-64bit` feature)
- [ ] 2.11 Define status constants enums: `FdbKvStatus`, `FdbTslStatus`, `FdbSectorStoreStatus`, `FdbSectorDirtyStatus`

### 3. Core Lifecycle (db.rs)

- [ ] 3.1 Implement `_fdb_init_ex(db, name, path, db_type, user_data)` — validate assertions, store metadata, alloc storage fields
- [ ] 3.2 Implement `_fdb_init_finish(db, result)` — set init_ok, print version banner once (static guard)
- [ ] 3.3 Implement `_fdb_deinit(db)` — close file descriptors, reset init_ok, clear storage
- [ ] 3.4 Implement `_fdb_db_path(db)` — return path string for file/FAL mode
- [ ] 3.5 Implement `FdbDb` init/validation helpers: sector size power-of-2 check, max_size/sec_size validation

### 4. Utils (utils.rs)

- [ ] 4.1 Define CRC32 lookup table as `static [u32; 256]` matching C source exactly
- [ ] 4.2 Implement `calc_crc32(crc: u32, buf: &[u8]) -> u32` with standard table algorithm
- [ ] 4.3 Implement `_fdb_set_status(status_table, status_num, status_index)` for all 6 write-granularity variants
- [ ] 4.4 Implement `_fdb_get_status(status_table, status_num)` for all 6 write-granularity variants
- [ ] 4.5 Implement `_fdb_write_status(db, addr, status_table, status_num, index, sync)` — set + flash write
- [ ] 4.6 Implement `_fdb_read_status(db, addr, status_table, total_num)` — flash read + get status
- [ ] 4.7 Implement `_fdb_continue_ff_addr(db, start, end)` — find first continuous 0xFF region
- [ ] 4.8 Implement `Blob::new(buf, len)` — create blob
- [ ] 4.9 Implement `Blob::read(db)` — read blob data from flash using saved metadata
- [ ] 4.10 Define `FlashIo` trait (`read`, `write`, `erase` methods)
- [ ] 4.11 Implement `_fdb_flash_read/write/erase` dispatch functions (file_mode vs FAL mode)
- [ ] 4.12 Implement `_fdb_flash_write_align(db, addr, buf, size)` — aligned write with pad buffer

### 5. File I/O (file.rs)

- [ ] 5.1 Define `FileFlashIo` struct with dir, sec_size, file_cache, cur_file_sec, cur_sec
- [ ] 5.2 Implement file path generation: `sector_to_file_path(db, addr)` producing `<dir>/<name>.fdb.<idx>`
- [ ] 5.3 Implement POSIX file open with descriptor cache (open/lseek pattern)
- [ ] 5.4 Implement POSIX file read (`_fdb_file_read`) with fd cache lookup, lseek+read
- [ ] 5.5 Implement POSIX file write (`_fdb_file_write`) with fd cache lookup, lseek+write+fsync
- [ ] 5.6 Implement POSIX file erase (`_fdb_file_erase`) — truncate open, fill 0xFF in 32-byte chunks, fsync
- [ ] 5.7 Implement file descriptor cache: insert, lookup, eviction (LRU-shift pattern)
- [ ] 5.8 Implement `FlashIo` trait for `FileFlashIo`
- [ ] 5.9 Create `FileFlashIo` constructor/new with directory path and sector size

### 6. KVDB Engine (kvdb.rs)

- [ ] 6.1 Define `KvDb` struct extending `FdbDb` with KV-specific fields (kv_cache, sec_cache, gc_request, etc.)
- [ ] 6.2 Implement sector header read/write for KVDB (store/dirty status, magic, combined)
- [ ] 6.3 Implement `kvdb_init(name, path, default_kvs, user_data)` — format sectors, recovery check, default KV provisioning
- [ ] 6.4 Implement sector formatting: `_fdb_sector_format` for UNUSED → EMPTY → USING transitions
- [ ] 6.5 Implement recovery check: scan sectors, verify magic, build cache table, CRC32 check
- [ ] 6.6 Implement `kvdb_deinit()` — clear cache tables, call `_fdb_deinit`
- [ ] 6.7 Implement KV header write: `_fdb_kv_set_ex` with status PRE_WRITE → WRITE transitions, CRC32 computation
- [ ] 6.8 Implement KV search: `_fdb_kv_search` — sector-by-sector traversal, cache integration
- [ ] 6.9 Implement `KvDb::get(key)` — search + read value, return `Option<String>`
- [ ] 6.10 Implement `KvDb::get_blob(key, blob)` — read blob-mode KV data
- [ ] 6.11 Implement `KvDb::set_blob(key, blob)` — write blob-mode KV with CRC32
- [ ] 6.12 Implement `KvDb::del(key)` — PRE_DELETE → DELETED status transitions, cache invalidation
- [ ] 6.13 Implement `KvDb::set_default(default_kvs)` — write default KVs on empty DB
- [ ] 6.14 Implement sector allocation: find empty sector, mark USING, handle combined sectors for large values
- [ ] 6.15 Implement sector fullness detection and `FDB_SECTOR_STORE_FULL` transition
- [ ] 6.16 Implement control methods: `set_sec_size`, `set_max_size`, `set_file_mode`, `set_not_formatable`

### 7. KV Cache

- [ ] 7.1 Implement `_fdb_kv_cache_init` — initialize cache table with sentinel values
- [ ] 7.2 Implement `_fdb_kv_cache_search(name, kv)` — CRC16 hash lookup, active counter increment
- [ ] 7.3 Implement `_fdb_kv_cache_insert(addr, name)` — insert new entry, evict least-active if full
- [ ] 7.4 Implement `_fdb_kv_cache_delete(addr)` — invalidate entry by address (set CRC16 to 0xFFFF)
- [ ] 7.5 Implement `_fdb_kv_cache_clear` — reset all entries

### 8. KV Iterator

- [ ] 8.1 Implement `_fdb_kv_iter_init(itr)` — reset counters, set sector_addr to oldest_addr
- [ ] 8.2 Implement `_fdb_kv_iter_next(itr, db)` — scan sectors for next live KV, advance, return bool
- [ ] 8.3 Implement `KvDb::print()` — iterate and print all KVs with sector/status/value info

### 9. Garbage Collection

- [ ] 9.1 Implement `gc_collect(db)` — entry point, request full free-space collection
- [ ] 9.2 Implement `gc_collect_by_free_size(db, free_size)` — count empty sectors, iterate dirty sectors
- [ ] 9.3 Implement `do_gc(db, sec_addr)` — mark GC-in-progress, move live KVs, erase, reformat
- [ ] 9.4 Implement `_fdb_gc_move_kv(db, from_addr, to_addr)` — copy KV header + name + value to new sector
- [ ] 9.5 Implement `gc_check_sec` — verify dirty status and GC eligibility
- [ ] 9.6 Integrate GC trigger: set gc_request after sector fill, call gc_collect_by_free_size before sector allocation
- [ ] 9.7 Implement post-GC cache update: update cache entries for moved KVs

### 10. TSDB Engine (tsdb.rs)

- [ ] 10.1 Define `TsDb` struct extending `FdbDb` with TS-specific fields (cur_sec info, rollover, get_time, last_time, max_len)
- [ ] 10.2 Implement TSDB sector header read/write (store status, magic, start_time, end_info[2])
- [ ] 10.3 Implement `tsdb_init(name, path, get_time_fn, max_len, user_data)` — format sectors, recovery
- [ ] 10.4 Implement TSDB recovery: scan sector headers, identify using sector, scan TSLs for last valid position, handle partial writes
- [ ] 10.5 Implement `tsdb_deinit()` — clear cur_sec state, call `_fdb_deinit`
- [ ] 10.6 Implement `TsDb::append(blob)` — auto-generate timestamp, write TSL index + data, handle rollover
- [ ] 10.7 Implement `TsDb::append_with_ts(blob, ts)` — explicit timestamp append
- [ ] 10.8 Implement sector rollover: finalize current sector (write end_info[0],[1]), format next sector, handle oldest-sector reuse
- [ ] 10.9 Implement TSL index/data write with sector layout (index grows up, data grows down)
- [ ] 10.10 Implement `TsDb::iter(callback, arg)` — forward iteration across sectors
- [ ] 10.11 Implement `TsDb::iter_reverse(callback, arg)` — reverse iteration
- [ ] 10.12 Implement `TsDb::iter_by_time(from, to, callback, arg)` — time-range filtered iteration with sector-level skipping
- [ ] 10.13 Implement `TsDb::query_count(from, to, status_filter)` — count TSLs in time range
- [ ] 10.14 Implement `TsDb::set_status(tsl, new_status)` — write-once status update in flash
- [ ] 10.15 Implement `TsDb::clean()` — iterate all sectors, mark all TSLs DELETED, reset to fresh sector
- [ ] 10.16 Implement control methods: `set_sec_size`, `set_rollover`, `get_last_time`

### 11. KVDB Test Migration (tests/kvdb_tests.rs)

- [ ] 11.1 Create test infrastructure helpers: `create_temp_dir()`, `setup_kvdb()`, `teardown_kvdb()`, `make_test_kvs()`
- [ ] 11.2 Migrate `test_fdb_kvdb_init` → `#[test] fn kvdb_init()`
- [ ] 11.3 Migrate `test_fdb_kvdb_deinit` → `#[test] fn kvdb_deinit()`
- [ ] 11.4 Migrate `test_fdb_kvdb_init_check` → `#[test] fn kvdb_init_check()`
- [ ] 11.5 Migrate `test_fdb_create_kv_blob` → `#[test] fn kvdb_create_kv_blob()`
- [ ] 11.6 Migrate `test_fdb_change_kv_blob` → `#[test] fn kvdb_change_kv_blob()`
- [ ] 11.7 Migrate `test_fdb_del_kv_blob` → `#[test] fn kvdb_del_kv_blob()`
- [ ] 11.8 Migrate `test_fdb_create_kv` → `#[test] fn kvdb_create_kv()`
- [ ] 11.9 Migrate `test_fdb_change_kv` → `#[test] fn kvdb_change_kv()`
- [ ] 11.10 Migrate `test_fdb_del_kv` → `#[test] fn kvdb_del_kv()`
- [ ] 11.11 Migrate `test_fdb_gc` → `#[test] fn kvdb_gc()`
- [ ] 11.12 Migrate `test_fdb_gc2` → `#[test] fn kvdb_gc2()`
- [ ] 11.13 Migrate `test_fdb_scale_up` → `#[test] fn kvdb_scale_up()`
- [ ] 11.14 Migrate `test_fdb_kvdb_set_default` → `#[test] fn kvdb_set_default()`

### 12. TSDB Test Migration (tests/tsdb_tests.rs)

- [ ] 12.1 Create test infrastructure helpers: `setup_tsdb()`, `teardown_tsdb()`, `mock_get_time()`, `make_test_blob()`
- [ ] 12.2 Migrate `test_fdb_tsdb_init_ex` → `#[test] fn tsdb_init()`
- [ ] 12.3 Migrate `test_fdb_tsdb_deinit` → `#[test] fn tsdb_deinit()`
- [ ] 12.4 Migrate `test_fdb_tsl_append` → `#[test] fn tsdb_append()`
- [ ] 12.5 Migrate `test_fdb_tsl_iter` → `#[test] fn tsdb_iter()`
- [ ] 12.6 Migrate `test_fdb_tsl_iter_by_time` → `#[test] fn tsdb_iter_by_time()`
- [ ] 12.7 Migrate `test_fdb_tsl_query_count` → `#[test] fn tsdb_query_count()`
- [ ] 12.8 Migrate `test_fdb_tsl_set_status` → `#[test] fn tsdb_set_status()`
- [ ] 12.9 Migrate `test_fdb_tsl_clean` (first) → `#[test] fn tsdb_clean()`
- [ ] 12.10 Migrate `test_fdb_tsl_clean` (second) → `#[test] fn tsdb_clean_after_set_status()`
- [ ] 12.11 Migrate `test_fdb_tsl_iter_by_time_1` → `#[test] fn tsdb_iter_by_time_1()`
- [ ] 12.12 Migrate `test_fdb_github_issue_249` → `#[test] fn tsdb_github_issue_249()`

### 13. Integration & Polish

- [ ] 13.1 Verify `cargo build` passes with default features
- [ ] 13.2 Verify `cargo build --features file-mode-posix` passes
- [ ] 13.3 Verify `cargo test` passes all 24 migrated tests
- [ ] 13.4 Run `cargo clippy` and fix lint warnings
- [ ] 13.5 Audit unsafe code: count unsafe lines, ensure <10% of total
- [ ] 13.6 Verify `#[repr(C)]` struct sizes match C `sizeof()` using const assertions
- [ ] 13.7 Verify CRC32 table matches C source byte-for-byte
- [ ] 13.8 Run tests under Miri if available (unsafe audit)
- [ ] 13.9 Write write-granularity parameterized tests for status table operations (all 6 variants)
- [ ] 13.10 Add `timestamp-64bit` feature flag test coverage
