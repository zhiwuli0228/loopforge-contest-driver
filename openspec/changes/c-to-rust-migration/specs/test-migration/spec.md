# Spec: Test Migration

## Overview

This spec provides the binding contract between C test functions in the FlashDB test suite and their Rust equivalents. Every C test function from the source inventory and test checklist MUST appear in the mapping table below. Phase 6 (Test) will use this spec to verify complete coverage.

## C Test Inventory

The C test suite consists of two files:
- `tests/fdb_kvdb_tc.c` -- 21 test/infrastructure functions (13 test functions + 3 helpers + 2 infrastructure)
- `tests/fdb_tsdb_tc.c` -- 14 test/infrastructure functions (11 test functions + 1 helper + 2 infrastructure)

Tests use the RT-Thread utest framework with scenario-based assertions. The Rust test suite uses Rust's native `#[test]` framework.

## C-to-Rust Mapping Table

### KVDB Tests (tests/fdb_kvdb_tc.c)

| C Test Function | C Source File | Rust Test Function | Rust Test File | Status |
|-----------------|---------------|--------------------|----------------|--------|
| `test_fdb_kvdb_init` | `tests/fdb_kvdb_tc.c:206` | `test_kvdb_init` | `tests/kvdb_tests.rs` | mapped |
| `test_fdb_kvdb_init_by_8_sectors` | `tests/fdb_kvdb_tc.c:211` | `test_kvdb_init_by_8_sectors` | `tests/kvdb_tests.rs` | mapped |
| `test_fdb_kvdb_init_by_sector_num` | `tests/fdb_kvdb_tc.c:189` | `test_kvdb_init_by_sector_num` | `tests/kvdb_tests.rs` | mapped |
| `test_fdb_kvdb_init_check` | `tests/fdb_kvdb_tc.c:216` | `test_kvdb_init_check` | `tests/kvdb_tests.rs` | mapped |
| `test_fdb_kvdb_deinit` | `tests/fdb_kvdb_tc.c:222` | `test_kvdb_deinit` | `tests/kvdb_tests.rs` | mapped |
| `test_fdb_create_kv_blob` | `tests/fdb_kvdb_tc.c:227` | `test_kvdb_create_kv_blob` | `tests/kvdb_tests.rs` | mapped |
| `test_fdb_change_kv_blob` | `tests/fdb_kvdb_tc.c:252` | `test_kvdb_change_kv_blob` | `tests/kvdb_tests.rs` | mapped |
| `test_fdb_del_kv_blob` | `tests/fdb_kvdb_tc.c:275` | `test_kvdb_del_kv_blob` | `tests/kvdb_tests.rs` | mapped |
| `test_fdb_create_kv` | `tests/fdb_kvdb_tc.c:297` | `test_kvdb_create_kv` | `tests/kvdb_tests.rs` | mapped |
| `test_fdb_change_kv` | `tests/fdb_kvdb_tc.c:313` | `test_kvdb_change_kv` | `tests/kvdb_tests.rs` | mapped |
| `test_fdb_del_kv` | `tests/fdb_kvdb_tc.c:343` | `test_kvdb_del_kv` | `tests/kvdb_tests.rs` | mapped |
| `test_fdb_gc` | `tests/fdb_kvdb_tc.c:447` | `test_kvdb_gc` | `tests/kvdb_tests.rs` | mapped |
| `test_fdb_gc2` | `tests/fdb_kvdb_tc.c:705` | `test_kvdb_gc2` | `tests/kvdb_tests.rs` | mapped |
| `test_fdb_kvdb_set_default` | `tests/fdb_kvdb_tc.c:938` | `test_kvdb_set_default` | `tests/kvdb_tests.rs` | mapped |
| `test_fdb_scale_up` | `tests/fdb_kvdb_tc.c:899` | `test_kvdb_scale_up` | `tests/kvdb_tests.rs` | mapped |
| `test_save_fdb_by_kvs` | `tests/fdb_kvdb_tc.c:398` | `test_kvdb_save_by_kvs` | `tests/kvdb_tests.rs` | mapped (test helper) |
| `test_check_fdb_by_kvs` | `tests/fdb_kvdb_tc.c:412` | `test_kvdb_check_by_kvs` | `tests/kvdb_tests.rs` | mapped (test helper) |
| `test_fdb_by_kvs` | `tests/fdb_kvdb_tc.c:441` | `test_kvdb_by_kvs` | `tests/kvdb_tests.rs` | mapped (test helper) |
| `utest_tc_init` | `tests/fdb_kvdb_tc.c:944` | — | — | N/A: RT-Thread test infrastructure; replaced by Rust `#[test]` setup/teardown via `setup_kvdb()` helper |
| `utest_tc_cleanup` | `tests/fdb_kvdb_tc.c:950` | — | — | N/A: RT-Thread test infrastructure; Rust `Drop` and `#[test]` teardown handles cleanup |

### TSDB Tests (tests/fdb_tsdb_tc.c)

| C Test Function | C Source File | Rust Test Function | Rust Test File | Status |
|-----------------|---------------|--------------------|----------------|--------|
| `test_fdb_tsdb_init_ex` | `tests/fdb_tsdb_tc.c:86` | `test_tsdb_init_ex` | `tests/tsdb_tests.rs` | mapped |
| `test_fdb_tsdb_deinit` | `tests/fdb_tsdb_tc.c:104` | `test_tsdb_deinit` | `tests/tsdb_tests.rs` | mapped |
| `test_fdb_tsl_append` | `tests/fdb_tsdb_tc.c:116` | `test_tsl_append` | `tests/tsdb_tests.rs` | mapped |
| `test_fdb_tsl_iter` | `tests/fdb_tsdb_tc.c:148` | `test_tsl_iter` | `tests/tsdb_tests.rs` | mapped |
| `test_fdb_tsl_iter_by_time` | `tests/fdb_tsdb_tc.c:154` | `test_tsl_iter_by_time` | `tests/tsdb_tests.rs` | mapped |
| `test_fdb_tsl_iter_by_time_1` | `tests/fdb_tsdb_tc.c:372` | `test_tsl_iter_by_time_1` | `tests/tsdb_tests.rs` | mapped |
| `test_fdb_tsl_query_count` | `tests/fdb_tsdb_tc.c:165` | `test_tsl_query_count` | `tests/tsdb_tests.rs` | mapped |
| `test_fdb_tsl_set_status` | `tests/fdb_tsdb_tc.c:191` | `test_tsl_set_status` | `tests/tsdb_tests.rs` | mapped |
| `test_fdb_tsl_clean` | `tests/fdb_tsdb_tc.c:211` | `test_tsl_clean` | `tests/tsdb_tests.rs` | mapped |
| `test_fdb_tsl_sector_bound_test` | `tests/fdb_tsdb_tc.c:349` | `test_tsl_sector_bound` | `tests/tsdb_tests.rs` | mapped |
| `test_fdb_github_issue_249` | `tests/fdb_tsdb_tc.c:452` | `test_tsl_github_issue_249` | `tests/tsdb_tests.rs` | mapped |
| `test_tsdb_data_by_time` | `tests/fdb_tsdb_tc.c:281` | `test_tsdb_data_by_time` | `tests/tsdb_tests.rs` | mapped (test helper) |
| `utest_tc_init` | `tests/fdb_tsdb_tc.c:228` | — | — | N/A: RT-Thread test infrastructure; replaced by Rust `#[test]` setup via `setup_tsdb()` helper |
| `utest_tc_cleanup` | `tests/fdb_tsdb_tc.c:236` | — | — | N/A: RT-Thread test infrastructure; Rust `Drop` and test teardown handles cleanup |

## Mapping Summary

| Category | C Test Functions | Mapped to Rust | N/A (infrastructure) |
|----------|-----------------|----------------|----------------------|
| KVDB test functions | 15 | 15 | 0 |
| KVDB helpers | 3 | 3 | 0 |
| KVDB infrastructure | 2 | 0 | 2 |
| TSDB test functions | 11 | 11 | 0 |
| TSDB helpers | 1 | 1 | 0 |
| TSDB infrastructure | 2 | 0 | 2 |
| **Total** | **34** | **30** | **4** |

## Additional Test Requirements

These are scenarios not covered by C tests but required for semantic equivalence assurance. They are flagged to be implemented as additional Rust tests in Phase 6.

### REQ-TEST-001: CRC32 known-answer test SHALL verify standard CRC32 output

WHEN `fdb_calc_crc32(0, b"123456789")` is called THEN the result SHALL equal `0xCBF43926` (standard zlib/ethernet CRC32 check value).

Status: Already implemented in existing `test_crc32_known_values` in `tests/source_migration.rs`.

### REQ-TEST-002: CRC32 empty buffer SHALL return 0x00000000

WHEN `fdb_calc_crc32(0, b"")` is called THEN the result SHALL equal `0x00000000`.

Status: Already implemented in existing `test_crc32_empty` in `tests/source_migration.rs`.

### REQ-TEST-003: Status table encoding SHALL be tested for each write granularity

WHEN `FDB_WRITE_GRAN` is set to each value in `{1, 8, 32, 64, 128, 256}` THEN `fdb_set_status` and `fdb_get_status` SHALL round-trip correctly for all valid status indices 0..N-1.

Status: New -- no C equivalent exists. C tests cover status tables only indirectly.

### REQ-TEST-004: fdb_continue_ff_addr SHALL find correct boundary for all-erased and partially-written flash

WHEN the entire range is 0xFF THEN the function SHALL return the aligned start address. WHEN the range has no 0xFF bytes THEN the function SHALL return `end`.

Status: New -- no direct C test for this utility function.

### REQ-TEST-005: File cache LRU eviction SHALL close the oldest file when full

WHEN the file cache is full (2 slots) and a third sector is accessed THEN the LRU entry SHALL be closed and evicted, and the new file SHALL occupy the cache.

Status: New -- no dedicated C test for file cache eviction.

### REQ-TEST-006: KVDB init SHALL reject non-power-of-2 sector size

WHEN `fdb_kvdb_init` is called with `sec_size=5000` THEN the function SHALL return `Err(FdbError::InitFailed)`.

Status: Already implemented in existing `test_db_init_rejects_non_power_of_two_sec_size` in `tests/source_migration.rs`.

### REQ-TEST-007: KVDB init SHALL reject single-sector configuration

WHEN `fdb_kvdb_init` is called with `max_size == sec_size` (only 1 sector) THEN the function SHALL return `Err(FdbError::InitFailed)`.

Status: Already implemented in existing `test_db_init_rejects_single_sector` in `tests/source_migration.rs`.

### REQ-TEST-008: Crash recovery SHALL handle interrupted writes (PRE_WRITE -> ERR_HDR)

WHEN a KV is in PRE_WRITE status on init THEN recovery SHALL mark it ERR_HDR and the database SHALL still be usable.

Status: New -- C tests do not simulate mid-write power failure. This is a high-severity coverage gap noted in the capability map.

### REQ-TEST-009: Crash recovery SHALL handle interrupted deletes (PRE_DELETE -> move KV)

WHEN a KV is in PRE_DELETE status on init THEN recovery SHALL move it to a new valid location (preserving the data that was about to be deleted).

Status: New -- high-severity coverage gap. Synthetic test required.

### REQ-TEST-010: Crash recovery SHALL resume interrupted GC (DIRTY_GC detection)

WHEN a sector is marked DIRTY_GC on init THEN recovery SHALL call `do_gc` to complete the interrupted GC.

Status: New -- high-severity coverage gap. Synthetic test required.

### REQ-TEST-011: TSL reverse iteration SHALL handle sector boundary crossings

WHEN `fdb_tsl_iter_reverse` traverses from the last TSL in sector N backward into sector N-1 THEN sector boundary SHALL be correctly crossed and iteration SHALL continue with the last TSL of sector N-1.

Status: New -- C has no dedicated reverse iteration test. Medium-severity gap.

### REQ-TEST-012: TSL binary search SHALL handle single-TSL sector edge case

WHEN a sector contains exactly 1 TSL THEN `search_start_tsl_addr` SHALL correctly find it (no infinite loop, no panic).

Status: New -- medium-severity gap. Binary search edge cases not exhaustively tested in C.

### REQ-TEST-013: KVDB re-init (init_ok already true) SHALL be idempotent

WHEN `fdb_kvdb_init` is called on an already-initialized KVDB THEN the function SHALL return `Ok(())` immediately without re-running recovery.

Status: New -- no C test for double-init scenario, but it is a documented behavior.

## Notes

1. **RT-Thread utest replacement**: C tests use `utest_tc_init`/`utest_tc_cleanup` for per-test setup/teardown. In Rust, equivalent logic is handled by `#[test]` functions that create fresh `FdbKvdb`/`FdbTsdb` instances and use temporary directories for file-mode storage. Rust's `Drop` trait ensures cleanup.

2. **FAL partition simulation**: C tests use FAL partition simulation (`blk_dev`). In Rust, the `RamFlash` struct (implementing `FlashStorage` trait) provides equivalent in-memory flash simulation for tests. For file-mode tests, temporary directories with unique names per test are created.

3. **Scenario assertions**: C tests use `uassert_true`, `uassert_int_equal`, `uassert_str_equal`, etc. In Rust, these map to `assert!`, `assert_eq!`, and custom assertion macros.

4. **Test helpers**: C helper functions (`test_save_fdb_by_kvs`, `test_check_fdb_by_kvs`, `test_fdb_by_kvs`) are utility functions used by multiple test cases. In Rust, they become shared helper functions in the test module, used via `#[test]` functions.

5. **Known gaps**: Crash recovery tests (REQ-TEST-008 through REQ-TEST-010) are high-severity gaps in both C and Rust. The C test suite does not simulate power failure, interrupted writes, or data corruption. These tests should be added in Phase 6 as synthetic recovery tests, but their absence does not block migration -- the C baseline also lacks them.
