# Spec: TSL Iteration and Query

## Capability Overview

This capability provides comprehensive time-series data access: forward iteration (oldest to newest), reverse iteration (newest to oldest), and time-range query with binary search optimization. It supports status-based counting within time ranges, sector boundary crossings, and ring-buffer wrapping correctly in both directions. The binary search optimization leverages the fact that timestamps are sorted within each sector.

## Key Functions

| C Function | C File:Line | Rust Equivalent | Behavior Summary |
|------------|-------------|-----------------|------------------|
| `fdb_tsl_iter` | `src/fdb_tsdb.c:556` | `fn fdb_tsl_iter(tsdb: &FdbTsdb, cb: FdbTslCb, cb_arg: usize, flash: &dyn FlashStorage)` | Forward iteration over all TSLs from oldest to newest |
| `fdb_tsl_iter_reverse` | `src/fdb_tsdb.c:606` | `fn fdb_tsl_iter_reverse(tsdb: &FdbTsdb, cb: FdbTslCb, cb_arg: usize, flash: &dyn FlashStorage)` | Reverse iteration over all TSLs from newest to oldest |
| `fdb_tsl_iter_by_time` | `src/fdb_tsdb.c:691` | `fn fdb_tsl_iter_by_time(tsdb: &FdbTsdb, from: FdbTime, to: FdbTime, cb: FdbTslCb, cb_arg: usize, flash: &dyn FlashStorage)` | Iterate TSLs within a time range (forward or reverse depending on from/to order) |
| `fdb_tsl_query_count` | `src/fdb_tsdb.c:790` | `fn fdb_tsl_query_count(tsdb: &FdbTsdb, from: FdbTime, to: FdbTime, status: FdbTslStatus, flash: &dyn FlashStorage) -> usize` | Count TSLs matching a status within a time range |
| `search_start_tsl_addr` | `src/fdb_tsdb.c:654` | `fn search_start_tsl_addr(tsdb: &FdbTsdb, sec: &TsdbSecInfo, from: FdbTime, to: FdbTime, flash: &dyn FlashStorage) -> Option<u32>` | Binary search for the first TSL address matching the time range |
| `get_next_tsl_addr` | `src/fdb_tsdb.c:192` | `fn get_next_tsl_addr(tsdb: &FdbTsdb, cur_addr: u32, flash: &dyn FlashStorage) -> u32` | Get the next TSL index address in forward direction |
| `get_last_tsl_addr` | `src/fdb_tsdb.c:210` | `fn get_last_tsl_addr(tsdb: &FdbTsdb, cur_addr: u32, sec: &TsdbSecInfo, flash: &dyn FlashStorage) -> u32` | Get the previous TSL index address in reverse direction |

## Data Structures

| C Struct | Fields | Rust Equivalent | Notes |
|----------|--------|----------------|-------|
| `query_count_args` | (in-code struct) | `QueryCountArgs` | Internal struct bundling status filter and count accumulator |

## Requirements

### REQ-tsl-iteration-query-001: fdb_tsl_iter SHALL traverse all valid TSLs in forward order

C source reference: `src/fdb_tsdb.c:556`

Scenario (normal path):
  GIVEN a TSDB with 10 TSLs across 2 sectors, timestamps 1-10
  WHEN `fdb_tsl_iter` is called
  THEN the callback SHALL be invoked 10 times, with TSLs in timestamp order (1, 2, ..., 10)

Scenario (error path):
  GIVEN a sector read failure during iteration
  WHEN `read_sector_info` returns an error for one sector
  THEN that sector SHALL be skipped, and iteration SHALL continue to the next sector

Scenario (boundary condition):
  GIVEN an empty database (no valid TSLs)
  WHEN `fdb_tsl_iter` is called
  THEN no callback invocations SHALL occur

### REQ-tsl-iteration-query-002: fdb_tsl_iter_reverse SHALL traverse in reverse order

C source reference: `src/fdb_tsdb.c:606`

Scenario (normal path):
  GIVEN a TSDB with 5 TSLs across 2 sectors
  WHEN `fdb_tsl_iter_reverse` is called
  THEN the callback SHALL be invoked with TSLs in reverse order (newest to oldest)

Scenario (error path):
  GIVEN no current sector (`cur_sec.addr` is 0 or invalid)
  WHEN `fdb_tsl_iter_reverse` starts
  THEN the iteration SHALL return immediately without invoking the callback

Scenario (boundary condition):
  GIVEN the database wraps around (oldest sector is after current sector in address space)
  WHEN `fdb_tsl_iter_reverse` crosses from sector 0 backward
  THEN `get_last_sector_addr` SHALL correctly wrap to the last sector at `max_size - sec_size`

### REQ-tsl-iteration-query-003: fdb_tsl_iter_by_time SHALL support both forward and reverse time ranges

C source reference: `src/fdb_tsdb.c:691`

Scenario (normal path):
  GIVEN `from=100`, `to=500` (forward: from <= to)
  WHEN `fdb_tsl_iter_by_time` is called
  THEN only TSLs with timestamp in [100, 500] SHALL be passed to the callback, visited in forward order

Scenario (error path):
  GIVEN `from=500`, `to=100` (reverse: from > to)
  WHEN `fdb_tsl_iter_by_time` is called
  THEN only TSLs with timestamp in [100, 500] SHALL be passed to the callback, visited in reverse order

Scenario (boundary condition):
  GIVEN a time range that falls entirely within one sector (binary search can find start exactly)
  WHEN `search_start_tsl_addr` performs binary search
  THEN the first callback invocation SHALL be the TSL closest to `from` (not the sector start)

### REQ-tsl-iteration-query-004: fdb_tsl_query_count SHALL count only TSLs matching the specified status

C source reference: `src/fdb_tsdb.c:790`

Scenario (normal path):
  GIVEN 10 TSLs in range [100, 500], of which 3 have status `UserStatus1` and 7 have status `Write`
  WHEN `fdb_tsl_query_count(tsdb, 100, 500, FdbTslStatus::UserStatus1, &flash)` is called
  THEN the function SHALL return `3`

Scenario (error path):
  GIVEN a flash read error during counting
  WHEN `read_tsl` fails for a particular TSL
  THEN counting SHALL continue with remaining TSLs (best-effort count)

Scenario (boundary condition):
  GIVEN an empty time range (no TSLs between `from` and `to`)
  WHEN `fdb_tsl_query_count` is called
  THEN the function SHALL return `0`

### REQ-tsl-iteration-query-005: Binary search SHALL find the first TSL >= from time within a sector

C source reference: `src/fdb_tsdb.c:654`

Scenario (normal path):
  GIVEN a sector with TSLs at timestamps [100, 200, 300, 400, 500] and `from=250`
  WHEN `search_start_tsl_addr` binary-searches
  THEN the returned address SHALL point to the TSL with timestamp 300 (first >= 250)

Scenario (error path):
  GIVEN a sector where no TSL has timestamp >= from (all TSLs are older)
  WHEN `search_start_tsl_addr` searches
  THEN the function SHALL return `None` (sector has no matching TSLs)

Scenario (boundary condition):
  GIVEN a sector with exactly 1 TSL
  WHEN `search_start_tsl_addr` binary-searches
  THEN the search SHALL correctly handle the single-element case without infinite loop or panic

## Invariants

- **INV-tsl-iteration-query-001**: Forward iteration SHALL start at `db.oldest_addr` and proceed until all sectors are exhausted. Within each sector, TSLs SHALL be read in address order (forward from low to high index addresses).
- **INV-tsl-iteration-query-002**: Reverse iteration SHALL start at `db.cur_sec.addr` and proceed backward through sectors. Within each sector, TSLs SHALL be read in reverse address order (from `end_idx` backward).
- **INV-tsl-iteration-query-003**: Binary search SHALL assume timestamps are sorted within each sector. The search space SHALL be bounded by sector top and `end_idx`, and mid addresses SHALL be aligned to `LOG_IDX_DATA_SIZE`.
- **INV-tsl-iteration-query-004**: TSLs with `UNUSED` or `PRE_WRITE` status SHALL be skipped during iteration (not passed to callback).
- **INV-tsl-iteration-query-005**: `fdb_tsl_iter_by_time` with `from > to` SHALL perform reverse traversal; with `from <= to` SHALL perform forward traversal.

## Dependencies

- `foundational-types` -- Uses `FdbTsdb`, `FdbTsl`, `TsdbSecInfo`, `FdbTslStatus`, `FdbTime`, `FdbTslCb`.
- `flash-io-dispatch` -- Flash reads for sector headers and TSL index data.
- `tsdb-sector-layout` -- `read_sector_info`, `get_next_sector_addr`, `get_last_sector_addr`.
