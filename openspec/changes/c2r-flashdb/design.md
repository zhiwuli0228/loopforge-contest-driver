## Context

FlashDB is an ultra-lightweight embedded key-value and time-series database for MCUs, written in C (Apache-2.0). It operates on raw flash/partition storage (FAL mode) or plain files (FILE mode), using sector-based storage with garbage collection, wear-leveling, and CRC32 integrity checks. The codebase consists of 5 C source files (~3,900 lines), 4 headers (~550 lines), and 2 test suites (24 test functions) built on the RT-Thread Utest framework.

**Source inventory summary:**

| File | Lines | Purpose |
|------|-------|---------|
| `inc/flashdb.h` | 79 | Public API (30 declarations) |
| `inc/fdb_def.h` | 351 | Structs, enums, error codes, control commands |
| `inc/fdb_low_lvl.h` | 71 | Internal macros (alignment, status tables) |
| `inc/fdb_cfg_template.h` | 56 | Build-time feature flags |
| `src/fdb.c` | 157 | Init/deinit lifecycle, path resolution |
| `src/fdb_kvdb.c` | 1944 | KVDB engine: sectors, read/write, GC, cache, iterator |
| `src/fdb_tsdb.c` | 1096 | TSDB engine: TSL append/iter/query, time-range |
| `src/fdb_file.c` | 317 | File mode I/O (POSIX + LIBC) |
| `src/fdb_utils.c` | 349 | CRC32, status-table ops, flash abstraction, blob |
| `tests/fdb_kvdb_tc.c` | 979 | 13 KVDB test functions |
| `tests/fdb_tsdb_tc.c` | 518 | 11 TSDB test functions |

**Key architectural patterns in the C codebase:**

1. **Status tables**: Write-once state machines encoded as bit/byte sequences in flash, where `0xFF` (erased) represents unused and `0x00` (written) marks state transitions. The encoding depends on `FDB_WRITE_GRAN` (1, 8, 32, 64, 128, or 256 bits).

2. **Sector management**: Storage is divided into fixed-size sectors. Each sector has a header with store status (unused/empty/using/full), dirty status (unused/false/true/GC), magic word, and combined-number. KV sectors additionally track the next empty address and remaining space; TSDB sectors track start/end timestamps and two end-info slots for crash resilience.

3. **Garbage collection**: Multi-pass algorithm. When free sectors fall below threshold, dirty sectors are scanned; live KVs are moved to a new sector, then the old sector is erased and reformatted. The `gc_request` flag drives deferred collection after a KV write fills a sector.

4. **CRC32 integrity**: Each KV header includes a CRC32 covering name_len + value_len + name (padded to write granularity) + value (padded). Corruption is detected on read and logged.

5. **KV cache**: LRU-like cache with name CRC16 hashing and activity counters, supporting fast KV lookups without sector traversal.

6. **File mode abstraction**: `_fdb_flash_read/write/erase` dispatch to either FAL partition calls or file-based I/O (POSIX open/read/write/lseek/fsync or LIBC fopen/fread/fwrite/fflush) depending on compile-time flags.

7. **Iterator patterns**: Both KVDB and TSDB expose iterator-based traversal (forward, reverse, and time-range for TSDB) using callback functions and sector-by-sector traversal.

8. **Endianness**: Magic word matching uses conditional compilation (`FDB_BIG_ENDIAN`) to handle different byte orders.

## Goals / Non-Goals

**Goals:**

1. Produce a Rust crate `flashdb_rust` in `work/output/flashdb_rust/` that:
   - Preserves all 30 public API functions from `flashdb.h`
   - Is a single `lib` crate with modules `kvdb`, `tsdb`, `file`, `utils`
   - Uses FILE_MODE (POSIX file API) for tests, not FAL partition layer
   - Passes `cargo build` (with `--features file-mode-posix`)
   - Passes `cargo test` (migrated tests must execute and pass)
   - Keeps `unsafe` code below 10% of total lines

2. Semantically preserve all core algorithms:
   - Status-table state machines (all 6 write-granularity variants)
   - Sector header formats and state transitions
   - KV read/write with CRC32 verification
   - Multi-pass GC algorithm (dirty scan → move → erase → reformat)
   - KV cache with LRU-like eviction
   - TSL append with sector rollover and two-end-info crash resilience
   - Time-range iteration and query-count
   - Iterator patterns (KV and TSL, forward/reverse/by-time)

3. Migrate all 24 test functions plus helper utilities:
   - 13 KVDB tests: init, init_check, create/blob/change/del KV, gc, gc2, scale-up, set_default, deinit
   - 11 TSDB tests: init, clean, append, iter, iter_by_time, query_count, set_status, iter_by_time_1, github_issue_249, deinit

4. Provide a trait-based flash I/O abstraction that enables FILE_MODE in tests and pluggable backends for embedded use.

**Non-Goals:**

- Porting demo applications (esp32, esp8266, stm32, linux demos)
- Porting STM32 BSP/HAL drivers or CMSIS headers
- Porting the FAL (Flash Abstraction Layer) partition layer
- Supporting FDB_USING_FAL_MODE in the initial implementation
- Reproducing RT-Thread Utest framework — tests will use Rust's native `#[test]` and `assert!` macros
- Optimizing for embedded memory constraints (heap-allocated structs are acceptable)
- Replicating `FDB_KV_AUTO_UPDATE` (version-based auto-update) feature
- Supporting `FDB_TSDB_FIXED_BLOB_SIZE` in the initial implementation (variable-size only)

## Decisions

### 1. Crate layout: single `lib` crate with modules

```
flashdb_rust/
├── Cargo.toml
├── src/
│   ├── lib.rs          # Re-exports, FdbError, FdbTime, version constants
│   ├── db.rs           # FdbDb base struct, init/deinit, path (from fdb.c)
│   ├── kvdb.rs         # KVDB engine (from fdb_kvdb.c)
│   ├── tsdb.rs         # TSDB engine (from fdb_tsdb.c)
│   ├── file.rs         # File mode I/O (from fdb_file.c)
│   ├── utils.rs        # CRC32, status-table, blob, flash abstraction
│   └── config.rs       # Constants, write-granularity types
└── tests/
    ├── kvdb_tests.rs   # Migrated from fdb_kvdb_tc.c
    └── tsdb_tests.rs   # Migrated from fdb_tsdb_tc.c
```

**Rationale**: Single crate avoids circular dependency issues between core types and I/O. The C codebase already interleaves DB, KVDB, TSDB, and utility functions; a monolithic crate mirrors this naturally. Modules provide logical separation without physical boundaries that would complicate shared types.

**Alternatives considered:**
- Multi-crate workspace (`flashdb-core`, `flashdb-file`, etc.): Adds unnecessary complexity for a ~4000-line migration. Shared types would require a separate `flashdb-types` crate or `pub use` chains.
- Flat module structure (all in lib.rs): Too large for a single file; violates Rust modularity conventions.

### 2. Error strategy: `Result<T, FdbError>`

All fallible operations return `Result<T, FdbError>` where:

```rust
pub enum FdbError {
    NoErr,
    EraseErr,
    ReadErr,
    WriteErr,
    PartNotFound,
    KvNameErr,
    KvNameExist,
    SavedFull,
    InitFailed,
}
```

C functions returning `fdb_err_t` are mapped to `Result<(), FdbError>`. Functions returning pointers (e.g. `fdb_kv_get`) return `Option<&str>`.

**Rationale**: Idiomatic Rust. The C error enum maps 1:1. No hidden error states (unlike C where callers must check return codes).

### 3. Flash I/O abstraction: trait-based interface

```rust
pub trait FlashIo {
    fn read(&self, addr: u32, buf: &mut [u8]) -> Result<(), FdbError>;
    fn write(&self, addr: u32, buf: &[u8], sync: bool) -> Result<(), FdbError>;
    fn erase(&self, addr: u32, size: usize) -> Result<(), FdbError>;
}

pub struct FileFlashIo {
    // File descriptor cache, sector→fd mapping
    dir: String,
    sec_size: u32,
    file_cache: ...,
}
```

File mode is the default implementation. The trait enables swap-in of real flash drivers for embedded targets.

**Rationale**: Decouples storage from business logic. Enables testability (in-memory backing store for unit tests if desired). The C code already has this abstraction implicitly through `_fdb_flash_read/write/erase` dispatching to `_fdb_file_*` or FAL.

**Alternatives considered:**
- `embedded-storage` / `embedded-io` traits: These are the embedded Rust standard, but require additional dependencies and have async variants that would complicate the synchronous design. We can add `embedded-storage` impls as a follow-up.
- Direct `std::fs` calls: Couples the library to OS filesystems; defeats embedded use case.

### 4. Sector management: direct algorithm translation

The C sector management uses:
- Sector header structs with packed fields at flash offsets
- Status tables (byte arrays) where offsets encode state via write-once bit patterns
- Magic words for sector type identification
- Combined-sector numbers for KVDB sector merging

These will be translated directly to Rust structs with `#[repr(C)]` for byte-level layout compatibility with the on-flash format. Status table operations (`_fdb_set_status`, `_fdb_get_status`, `_fdb_write_status`) will be pure Rust functions operating on `&[u8]`.

**Rationale**: The on-flash format is fixed; any structural change breaks compatibility with existing databases. The algorithms are well-tested and complex (6 write-granularity variants × status-table encodings); direct translation minimizes the risk of introducing bugs.

### 5. Garbage collection: preserve the multi-pass algorithm

The GC algorithm has three layers:
1. `gc_collect()` — entry point, requests full free-space collection
2. `gc_collect_by_free_size(db, free_size)` — checks empty sector count, iterates dirty sectors via `do_gc`
3. `do_gc()` — marks sector as GC-in-progress, moves live KVs to new sector, erases old sector, updates `oldest_addr`

This will be preserved exactly. The deferred GC pattern (`gc_request` flag → triggered after sector-fill) will also be preserved.

**Rationale**: GC correctness is the highest-risk area. The algorithm handles edge cases: crash recovery (partially written KVs), incomplete deletes, cache invalidation, sector combining. Any deviation risks data loss. This is a direct translation, not a redesign.

**Risk mitigtation**: `test_fdb_gc` and `test_fdb_gc2` in the C test suite exercise complex GC scenarios with sector-by-sector layout verification. These tests will be migrated first and run as regression tests for the Rust GC implementation.

### 6. Testing: migrate all 24 test functions + helpers

Each C test function becomes a Rust `#[test]` function. Setup/teardown (`utest_tc_init`/`utest_tc_cleanup`) become per-test setup or `#[cfg(test)]` module-level helpers. RT-Thread specific APIs are replaced:
- `rt_tick_get()` → `std::time::Instant`
- `rt_thread_mdelay()` → `std::thread::sleep`
- `rt_malloc`/`rt_free` → `Box`/`Vec`
- `rt_strncpy`/`rt_snprintf` → Rust string operations
- `uassert_*` → Rust's `assert!`, `assert_eq!`, `assert_ne!`
- Filesystem operations (`access`, `mkdir`, `opendir`, `unlink`) → `std::fs`

KVDB tests use FILE_MODE with dedicated test directories. Each DB instance writes to a temporary directory created in the test function.

**Rationale**: Test preservation ensures behavioral equivalence. The C test suite is comprehensive, covering init, CRUD, GC (two variants), scale-up, time-range queries, status transitions, and edge cases (GitHub issue #249).

### 7. Public API mapping

All 30 public API functions from `flashdb.h` are preserved with Rust-idiomatic signatures:

| C function | Rust signature |
|------------|---------------|
| `fdb_kvdb_init(...)` → `fdb_err_t` | `KvDb::init(name, path, ...) -> Result<(), FdbError>` |
| `fdb_kvdb_deinit(...)` → `fdb_err_t` | `KvDb::deinit() -> Result<(), FdbError>` |
| `fdb_kvdb_control(...)` → `void` | `KvDb::control(cmd, arg)` |
| `fdb_kv_set(...)` → `fdb_err_t` | `KvDb::set(key, value) -> Result<(), FdbError>` |
| `fdb_kv_get(...)` → `char*` | `KvDb::get(key) -> Option<String>` |
| `fdb_kv_set_blob(...)` → `fdb_err_t` | `KvDb::set_blob(key, blob) -> Result<(), FdbError>` |
| `fdb_kv_get_blob(...)` → `size_t` | `KvDb::get_blob(key, blob) -> usize` |
| `fdb_kv_del(...)` → `fdb_err_t` | `KvDb::del(key) -> Result<(), FdbError>` |
| `fdb_kv_set_default(...)` → `fdb_err_t` | `KvDb::set_default() -> Result<(), FdbError>` |
| `fdb_blob_make(...)` → `fdb_blob_t` | `Blob::new(buf, len) -> Blob` |
| `fdb_blob_read(...)` → `size_t` | `Blob::read(db) -> usize` |
| `fdb_tsl_append(...)` → `fdb_err_t` | `TsDb::append(blob) -> Result<(), FdbError>` |
| `fdb_tsl_iter(...)` → `void` | `TsDb::iter(cb)` |
| `fdb_tsl_iter_by_time(...)` → `void` | `TsDb::iter_by_time(from, to, cb)` |
| `fdb_calc_crc32(...)` → `uint32_t` | `calc_crc32(crc, buf) -> u32` |

C structs with interior pointers (`fdb_kv_t`, `fdb_blob_t`) become owned Rust structs with `&[u8]` slices where possible, or heap-allocated `Vec<u8>` for name/value storage. The C pattern of passing pre-allocated structs by pointer and mutating them is replaced by methods that return owned values or `&mut self` methods.

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| GC algorithm correctness | Data loss/corruption | Direct translation; exhaustive GC tests migrated first; manual verification against sector diagrams in test comments |
| Status-table encoding (6 write-granularity variants) | Incorrect state transitions | Parametrized tests over `FDB_WRITE_GRAN` values; table-driven status encoding tests |
| Alignment-sensitive flash operations | `FDB_WG_ALIGN` and struct padding must match C exactly | `#[repr(C)]` structs; alignment tests; verify struct sizes match C `sizeof()` |
| Timestamp handling (32-bit vs 64-bit `fdb_time_t`) | Overflow or truncation in time-range queries | `FdbTime` type alias with feature flag; tests at boundary values |
| Pointer arithmetic translation (offsetof, FAILED_ADDR sentinel) | Incorrect address computation | Constant verification tests; adapter functions for address arithmetic |
| File mode caching (fd caching, lseek offsets) | Concurrent access issues, stale file handles | Preserve C caching logic; single-threaded design (lock callbacks optional) |
| Rust ownership vs C pointer sharing (`fdb_kv_t`, `fdb_blob_t`) | Borrow-checker friction, double-free risks | `Blob` and `KvData` as owned types; no raw pointer sharing between modules |
| RT-Thread API replacement in tests | Test flakiness due to timing differences | `std::time::Instant` for ticks; remove real-time delays where possible; `sleep` only when necessary for ordering |
| `unsafe` threshold (<10%) | Design constraint | Isolate `unsafe` to flash I/O (file trait impl) and byte-level operations; status-table and CRC32 are pure safe Rust |

## Open Questions

1. **Crate naming**: The design contract specifies `flashDB_rust` but Cargo convention is lowercase with underscores. Recommend `flashdb_rust` for the crate name (Cargo.toml `name` field) while keeping the output directory as `flashDB_rust` per the design contract.

2. **`fdb_kv_get` reentrancy**: The C function uses a `static char value[...]` buffer, making it non-reentrant. The Rust version should return `Option<String>` (heap-allocated) instead. This changes the API semantics but improves safety.

3. **Lock callbacks**: The C code supports optional `lock`/`unlock` function pointers. For the initial Rust implementation, these can be `Option<Box<dyn Fn()>>` or omitted entirely since Rust's ownership model already prevents data races in single-threaded contexts. For embedded multi-threading, `Mutex<()>` wraps can be added later.

4. **`FDB_KV_AUTO_UPDATE`**: Marked as non-goal for the initial implementation. Should be added as a follow-up feature behind a Cargo feature flag.

5. **`FDB_TSDB_FIXED_BLOB_SIZE`**: Marked as non-goal. The feature changes the on-flash format (index size, data layout). Variable-size implementation is the more general case and should be implemented first.

6. **Timestamp feature flag**: Use Cargo feature `timestamp-64bit` (off by default) that changes `FdbTime` from `i32` to `i64`, mirroring `FDB_USING_TIMESTAMP_64BIT`.

## Migration Approach

The migration follows a module-by-module approach with batch execution:

### Phase 1: Foundation (db, config, utils)
- `config.rs`: Constants, `FdbError`, `FdbTime`, write-granularity types
- `utils.rs`: CRC32 table, status-table get/set/write, flash abstraction trait, `Blob` struct
- `db.rs`: `FdbDb` base struct, `_fdb_init_ex`, `_fdb_init_finish`, `_fdb_deinit`
- **Build gate**: `cargo build` succeeds with foundation modules

### Phase 2: File I/O
- `file.rs`: `FileFlashIo` implementing `FlashIo` trait (POSIX mode)
- File descriptor caching, sector→file mapping
- **Test gate**: File read/write/erase tests pass

### Phase 3: KVDB engine
- `kvdb.rs`: Sector header structs, `KvDb` struct, read/write sector info
- KV search (with cache), KV create/read/update/delete
- Sector formatting, status transitions
- Iterator implementation
- **Test gate**: KVDB unit tests (init, CRUD) pass

### Phase 4: KVDB GC
- GC algorithm (gc_collect, gc_collect_by_free_size, do_gc, move_kv)
- GC integration with sector allocation
- **Test gate**: `test_fdb_gc` and `test_fdb_gc2` pass

### Phase 5: TSDB engine
- `tsdb.rs`: Sector header structs, `TsDb` struct, read/write sector info
- TSL append with sector rollover
- Iterator (forward, reverse, by_time)
- Query count, set status, clean
- **Test gate**: All TSDB tests pass

### Phase 6: Integration and verification
- `lib.rs`: Re-exports, public API surface
- Full test suite execution
- Unsafe ratio audit
- Semantic equivalence verification
- **Final gate**: `cargo build && cargo test` both succeed; unsafe < 10%

Each phase is independently buildable and testable. Subagents may work on phases 2-5 in parallel after phase 1 completes.
