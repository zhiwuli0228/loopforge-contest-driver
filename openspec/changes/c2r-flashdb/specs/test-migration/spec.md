## ADDED Requirements

### Requirement: Test Migration Checklist

All 24 C test functions (13 KVDB + 11 TSDB) SHALL be migrated to Rust `#[test]` functions. Each test SHALL preserve the original C test's purpose, assertions, and edge-case coverage.

---

### KVDB Tests (13 functions from `tests/fdb_kvdb_tc.c`)

#### 1. `test_fdb_kvdb_init`

- **C source**: `fdb_kvdb_tc.c:206` — `UTEST_UNIT_RUN(test_fdb_kvdb_init)`
- **Purpose**: Basic KVDB initialization with default sector count
- **Rust test requirement**: Call `KvDb::init(name, dir, default_kvs, None)` on a temp directory; verify `init_ok == true`; verify sector count matches expected
- **Rust test name**: `kvdb_init`

#### 2. `test_fdb_kvdb_init_check`

- **C source**: `fdb_kvdb_tc.c:216` — `UTEST_UNIT_RUN(test_fdb_kvdb_init_check)`
- **Purpose**: Verify KVDB can be re-initialized (recovery) and survive a re-init cycle
- **Rust test requirement**: Init KVDB, deinit, init again; verify no errors on re-init; verify existing KVs are still readable
- **Rust test name**: `kvdb_init_check`

#### 3. `test_fdb_create_kv_blob`

- **C source**: `fdb_kvdb_tc.c:227` — `UTEST_UNIT_RUN(test_fdb_create_kv_blob)`
- **Purpose**: Create a blob-mode KV, verify it can be read back
- **Rust test requirement**: Init KVDB, call `KvDb::set_blob(key, blob)`, read back with `KvDb::get_blob(key, &blob)`, verify value matches; verify status is `FDB_KV_WRITE`
- **Rust test name**: `kvdb_create_kv_blob`

#### 4. `test_fdb_change_kv_blob`

- **C source**: `fdb_kvdb_tc.c:252` — `UTEST_UNIT_RUN(test_fdb_change_kv_blob)`
- **Purpose**: Update an existing blob-mode KV
- **Rust test requirement**: Create a blob KV, update with a new blob value, verify the updated value is read back; verify old KV status is `FDB_KV_DELETED`
- **Rust test name**: `kvdb_change_kv_blob`

#### 5. `test_fdb_del_kv_blob`

- **C source**: `fdb_kvdb_tc.c:275` — `UTEST_UNIT_RUN(test_fdb_del_kv_blob)`
- **Purpose**: Delete a blob-mode KV
- **Rust test requirement**: Create a blob KV, delete it, verify `KvDb::get_blob` returns 0 or `KvDb::get` returns `None`; verify KV status is `FDB_KV_DELETED`
- **Rust test name**: `kvdb_del_kv_blob`

#### 6. `test_fdb_create_kv`

- **C source**: `fdb_kvdb_tc.c:297` — `UTEST_UNIT_RUN(test_fdb_create_kv)`
- **Purpose**: Create a string-mode KV, verify it can be read back
- **Rust test requirement**: Init KVDB, call `KvDb::set(key, value)`, read back with `KvDb::get(key)`, verify value matches; verify CRC32 is valid
- **Rust test name**: `kvdb_create_kv`

#### 7. `test_fdb_change_kv`

- **C source**: `fdb_kvdb_tc.c:313` — `UTEST_UNIT_RUN(test_fdb_change_kv)`
- **Purpose**: Update an existing string-mode KV
- **Rust test requirement**: Create a string KV, update with a new value using `KvDb::set(key, new_value)`, verify the updated value is read back; verify old KV address becomes `FDB_KV_DELETED`; requires deinit/reinit cycle
- **Rust test name**: `kvdb_change_kv`

#### 8. `test_fdb_del_kv`

- **C source**: `fdb_kvdb_tc.c:343` — `UTEST_UNIT_RUN(test_fdb_del_kv)`
- **Purpose**: Delete a string-mode KV
- **Rust test requirement**: Create a string KV, delete it, verify `KvDb::get(key)` returns `None`; verify KV status is `FDB_KV_DELETED`
- **Rust test name**: `kvdb_del_kv`

#### 9. `test_fdb_gc`

- **C source**: `fdb_kvdb_tc.c:447` — `UTEST_UNIT_RUN(test_fdb_gc)`
- **Purpose**: Verify garbage collection moves live KVs and reclaims dirty sectors
- **Rust test requirement**: Fill sectors with KVs (including creates, updates, and deletes to produce dirty KVs); trigger GC by exhausting sectors; verify GC correctly moves live KVs; verify old sectors are erased and reformatted as `FDB_SECTOR_STORE_EMPTY`; verify sector layout matches expected state after each GC cycle
- **Rust test name**: `kvdb_gc`

#### 10. `test_fdb_gc2`

- **C source**: `fdb_kvdb_tc.c:705` — `UTEST_UNIT_RUN(test_fdb_gc2)`
- **Purpose**: Verify GC with exact sector layout constraints (3 KVs per sector, large value sizes)
- **Rust test requirement**: Same as GC but with specific dynamically-computed value length so exactly 3 KVs fit per sector; verify GC stops correctly after moving enough KVs to satisfy `free_size`; verify the do_gc early-stop condition (`remain > free_size`) works correctly
- **Rust test name**: `kvdb_gc2`

#### 11. `test_fdb_scale_up`

- **C source**: `fdb_kvdb_tc.c:899` — `UTEST_UNIT_RUN(test_fdb_scale_up)`
- **Purpose**: Verify KVDB handles sector count changes between deinit/reinit cycles
- **Rust test requirement**: Init with small sector count, write KVs, deinit; re-init with larger sector count, verify existing KVs are still readable and new KVs can be written in the expanded space
- **Rust test name**: `kvdb_scale_up`

#### 12. `test_fdb_kvdb_set_default`

- **C source**: `fdb_kvdb_tc.c:938` — `UTEST_UNIT_RUN(test_fdb_kvdb_set_default)`
- **Purpose**: Verify default KVs are written on fresh database init
- **Rust test requirement**: Init KVDB with a default KV list; verify all default KVs exist with correct values; verify no extra KVs were created
- **Rust test name**: `kvdb_set_default`

#### 13. `test_fdb_kvdb_deinit`

- **C source**: `fdb_kvdb_tc.c:222` — `UTEST_UNIT_RUN(test_fdb_kvdb_deinit)`
- **Purpose**: Verify KVDB deinitialization cleans up resources
- **Rust test requirement**: Init KVDB, call `KvDb::deinit()`, verify `init_ok == false`; verify files are closed (can re-open temp dir); verify deinit of already-deinitialized DB is safe
- **Rust test name**: `kvdb_deinit`

---

### TSDB Tests (11 registrations from `tests/fdb_tsdb_tc.c`)

#### 14. `test_fdb_tsdb_init_ex`

- **C source**: `fdb_tsdb_tc.c:86` — `UTEST_UNIT_RUN(test_fdb_tsdb_init_ex)`
- **Purpose**: Basic TSDB initialization with file mode, sector size, and max size configured via control commands
- **Rust test requirement**: Create a temp directory, set sector size and max size via control methods, call `TsDb::init(name, path, get_time_fn, max_len, None)`; verify `init_ok == true`; verify sector count; create test directory if it doesn't exist
- **Rust test name**: `tsdb_init`

#### 15. `test_fdb_tsl_clean`

- **C source**: `fdb_tsdb_tc.c:211` — `UTEST_UNIT_RUN(test_fdb_tsl_clean)` (appears twice in testcase: line 504 and 510)
- **Purpose**: Verify TSDB clean operation marks all TSLs as deleted
- **Rust test requirement**: Append TSLs, call `TsDb::clean()`, iterate and verify all TSLs have status `FDB_TSL_DELETED`; verify database can be used again after clean
- **Rust test name**: `tsdb_clean`

#### 16. `test_fdb_tsl_append`

- **C source**: `fdb_tsdb_tc.c:116` — `UTEST_UNIT_RUN(test_fdb_tsl_append)`
- **Purpose**: Verify TSL append creates valid entries with auto-generated timestamps
- **Rust test requirement**: Append `TEST_TS_COUNT` TSLs; verify each TSL has correct timestamp (increasing by `TEST_TIME_STEP`); verify TSL status is `FDB_TSL_WRITE`; verify sector rollover occurs when sectors fill
- **Rust test name**: `tsdb_append`

#### 17. `test_fdb_tsl_iter`

- **C source**: `fdb_tsdb_tc.c:148` — `UTEST_UNIT_RUN(test_fdb_tsl_iter)`
- **Purpose**: Verify forward iteration visits all TSLs in order
- **Rust test requirement**: Append TSLs, call `TsDb::iter(callback, arg)`; verify callback is invoked for each TSL; verify iteration count matches append count; verify TSLs are visited in chronological order
- **Rust test name**: `tsdb_iter`

#### 18. `test_fdb_tsl_iter_by_time`

- **C source**: `fdb_tsdb_tc.c:154` — `UTEST_UNIT_RUN(test_fdb_tsl_iter_by_time)`
- **Purpose**: Verify time-range iteration filters TSLs correctly
- **Rust test requirement**: Append TSLs with known timestamps, call `TsDb::iter_by_time(from, to, callback, arg)`; verify only TSLs within `[from, to]` are visited; test boundary conditions (from==to, from > to, from/to before/after data range)
- **Rust test name**: `tsdb_iter_by_time`

#### 19. `test_fdb_tsl_query_count`

- **C source**: `fdb_tsdb_tc.c:165` — `UTEST_UNIT_RUN(test_fdb_tsl_query_count)`
- **Purpose**: Verify query count returns correct number of TSLs in time range
- **Rust test requirement**: Append TSLs, call `TsDb::query_count(from, to, status)`; verify count matches expected; test with different status filters (ALL, USER_STATUS1, DELETED)
- **Rust test name**: `tsdb_query_count`

#### 20. `test_fdb_tsl_set_status`

- **C source**: `fdb_tsdb_tc.c:191` — `UTEST_UNIT_RUN(test_fdb_tsl_set_status)`
- **Purpose**: Verify TSL status can be changed to user-defined and deleted states
- **Rust test requirement**: Append TSLs, set half to `FDB_TSL_USER_STATUS1`, the other half to `FDB_TSL_DELETED`; verify `query_count` with status filter returns correct counts; verify deleted TSLs are excluded from default iteration
- **Rust test name**: `tsdb_set_status`

#### 21. `test_fdb_tsl_clean` (second appearance)

- **C source**: `fdb_tsdb_tc.c:211` — `UTEST_UNIT_RUN(test_fdb_tsl_clean)` at line 510 (second registration)
- **Purpose**: Second clean test after status manipulation to verify clean resets state
- **Rust test requirement**: Same as test 15 but run after `test_fdb_tsl_set_status`; verify clean correctly handles deleted and user-marked TSLs
- **Rust test name**: `tsdb_clean_after_set_status`

#### 22. `test_fdb_tsl_iter_by_time_1`

- **C source**: `fdb_tsdb_tc.c:372` — `UTEST_UNIT_RUN(test_fdb_tsl_iter_by_time_1)`
- **Purpose**: Verify time-range iteration across sector boundaries with specific sector-filling pattern (exactly 5 sectors of data)
- **Rust test requirement**: Append exactly `TEST_ITER1_COUNT` TSLs (computed to span exactly 5 sectors for any write-granularity); test iteration from different sector boundaries; verify correct TSLs are returned for each time range; test `sector_bound_test` variants covering start/end sector index permutations
- **Rust test name**: `tsdb_iter_by_time_1`

#### 23. `test_fdb_tsdb_deinit`

- **C source**: `fdb_tsdb_tc.c:104` — `UTEST_UNIT_RUN(test_fdb_tsdb_deinit)`
- **Purpose**: Verify TSDB deinitialization works correctly
- **Rust test requirement**: Init TSDB, call `TsDb::deinit()`, verify `init_ok == false`; verify `_fdb_deinit` closes all files; verify re-init after deinit works correctly
- **Rust test name**: `tsdb_deinit`

#### 24. `test_fdb_github_issue_249`

- **C source**: `fdb_tsdb_tc.c:452` — `UTEST_UNIT_RUN(test_fdb_github_issue_249)`
- **Purpose**: Edge case regression test for GitHub issue #249 (specific corruption or race condition)
- **Rust test requirement**: Reproduce the exact scenario from the issue: specific sequence of append/read/status-change operations that triggered the bug; verify the fix prevents the issue; verify no data corruption or incorrect status transitions
- **Rust test name**: `tsdb_github_issue_249`

---

### Requirement: Test Infrastructure Requirements

All migrated tests SHALL use Rust's native test framework (`#[test]`), standard library APIs, and per-test temporary directories.

#### Scenario: Test setup and teardown

- **WHEN** each `#[test]` function runs
- **THEN** it SHALL create a unique temporary directory (using `tempdir` or `std::env::temp_dir()`)
- **AND** the database SHALL be initialized with `file_mode = true` and the temp dir as `path`
- **AND** the temp directory SHALL be cleaned up after the test (using `Drop` or `std::fs::remove_dir_all`)
- **AND** the test SHALL NOT depend on any other test's state

#### Scenario: RT-Thread API replacements

- **WHEN** the C test uses RT-Thread APIs
- **THEN** the following replacements SHALL be used:
  - `rt_tick_get()` → `std::time::Instant::now().elapsed()`
  - `rt_thread_mdelay(ms)` → `std::thread::sleep(Duration::from_millis(ms))`
  - `rt_malloc(size)` / `rt_free(ptr)` → Rust's `Vec::with_capacity(size)` / `Box`
  - `rt_strncpy(dst, src, n)` → `std::str::copy_from_slice` or `String::from_utf8_lossy`
  - `rt_snprintf(buf, size, fmt, ...)` → Rust's `format!` or `write!`
  - `uassert_*` macros → Rust's `assert!`, `assert_eq!`, `assert_ne!`
  - Filesystem operations (`access`, `mkdir`, `opendir`, `unlink`) → `std::fs` equivalents

#### Scenario: FDB_PRINT / FDB_INFO / FDB_DEBUG in tests

- **WHEN** the C test uses `FDB_PRINT` or `FDB_INFO` for debug output
- **THEN** the Rust test SHALL use `eprintln!` or `log::debug!` for equivalent output
- **AND** the output SHALL NOT affect test pass/fail status

#### Scenario: Write-granularity parameterization

- **WHEN** tests exercise status-table operations
- **THEN** the test SHALL be parameterized over all 6 valid `FDB_WRITE_GRAN` values (1, 8, 32, 64, 128, 256)
- **AND** use Rust's `#[cfg(feature = "write-gran-X")]` or compile-time constants to switch behavior

---

### Requirement: Test Preservation and Equivalence

Each migrated Rust test SHALL preserve the behavioral intent and assertion coverage of the corresponding C test.

#### Scenario: Assertion equivalence

- **WHEN** a C test calls `uassert_int_equal(expected, actual)`
- **THEN** the Rust test SHALL use `assert_eq!(expected, actual)`
- **WHEN** a C test calls `uassert_true(condition)`
- **THEN** the Rust test SHALL use `assert!(condition)`
- **WHEN** a C test calls `uassert_null(ptr)`
- **THEN** the Rust test SHALL use `assert!(result.is_none())`

#### Scenario: Sector layout verification

- **WHEN** a C test verifies sector magic words, statuses, or KVs at specific addresses
- **THEN** the Rust test SHALL use equivalent flash read operations to verify the same byte patterns
- **AND** sector header fields SHALL be verified with `assert_eq!` against expected values (magic words, combined numbers, store/dirty status, address calculations)

#### Scenario: Test is N/A

- **WHEN** a C test feature is explicitly excluded from the initial migration scope (e.g. FAL mode tests)
- **THEN** the test SHALL be marked as N/A with a comment explaining the exclusion reason
- **AND** the test SHALL NOT cause `cargo test` failures
