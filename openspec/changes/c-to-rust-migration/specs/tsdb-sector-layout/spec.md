# Spec: TSDB Sector Layout and Initialization

## Capability Overview

This capability implements TSDB-specific sector management: sector header format with `start_time` and dual `end_info` slots (for crash resilience), magic word validation, and sector status tracking. It initializes the ring-buffer layout by scanning all sectors, detecting the oldest and current sectors, and restoring the last timestamp from previous sector data. Fresh (all-empty) database initialization is handled by formatting all sectors and setting up the initial current sector.

## Key Functions

| C Function | C File:Line | Rust Equivalent | Behavior Summary |
|------------|-------------|-----------------|------------------|
| `fdb_tsdb_init` | `src/fdb_tsdb.c:1004` | `fn fdb_tsdb_init(tsdb: &mut FdbTsdb, name: &str, path: &str, max_len: usize) -> Result<(), FdbError>` | Full TSDB initialization: lifecycle init, sector layout scan, current sector detection |
| `fdb_tsdb_deinit` | `src/fdb_tsdb.c:1091` | `fn fdb_tsdb_deinit(tsdb: &mut FdbTsdb)` | Clean shutdown with file handle cleanup |
| `read_sector_info` | `src/fdb_tsdb.c:229` | `fn tsdb_read_sector_info(tsdb: &FdbTsdb, sec: &mut TsdbSecInfo, flash: &dyn FlashStorage) -> Result<(), FdbError>` | Read TSDB sector header with start_time, end_time, end_info parsing |
| `format_sector` | `src/fdb_tsdb.c:320` | `fn tsdb_format_sector(tsdb: &FdbTsdb, addr: u32, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Erase sector and write TSDB sector header with magic and start_time |
| `check_sec_hdr_cb` | `src/fdb_tsdb.c:990` | `fn check_sec_hdr_cb(tsdb: &FdbTsdb, addr: u32, flash: &dyn FlashStorage) -> bool` | Callback: validate sector header during init scan |
| `sector_iterator` | `src/fdb_tsdb.c:950` | `fn tsdb_sector_iterator(tsdb: &FdbTsdb, cb: fn(u32) -> bool, flash: &dyn FlashStorage)` | Iterate over all sectors, calling callback for each |
| `get_next_sector_addr` | `src/fdb_tsdb.c:177` | `fn tsdb_get_next_sector_addr(tsdb: &FdbTsdb, cur_addr: u32) -> u32` | Calculate next sector address, wrapping at max_size boundary |
| `get_last_sector_addr` | `src/fdb_tsdb.c:227` | `fn tsdb_get_last_sector_addr(tsdb: &FdbTsdb, cur_addr: u32) -> u32` | Calculate previous sector address, wrapping backward at boundary |

## Data Structures

| C Struct | Fields | Rust Equivalent | Notes |
|----------|--------|----------------|-------|
| `tsdb_sec_info` | `check_ok`, `status`, `addr`, `magic`, `start_time`, `end_time`, `end_idx`, `end_info_stat[2]`, `remain`, `empty_idx`, `empty_data` | `TsdbSecInfo { check_ok: bool, status: FdbSectorStoreStatus, addr: u32, magic: u32, start_time: FdbTime, end_time: FdbTime, end_idx: u32, end_info_stat: [FdbTslStatus; 2], remain: usize, empty_idx: u32, empty_data: u32 }` | `#[repr(C)]`. Dual `end_info_stat[2]` provides crash resilience: if one end_info is corrupted, the other is used. |

## Requirements

### REQ-tsdb-sector-layout-001: fdb_tsdb_init SHALL scan all sectors to detect the current sector

C source reference: `src/fdb_tsdb.c:1004`

Scenario (normal path):
  GIVEN a fresh database directory with no existing sector files
  WHEN `fdb_tsdb_init(&mut tsdb, "ts", "/data/ts", 256)` is called
  THEN all sectors SHALL be formatted, `tsdb.cur_sec` SHALL be set to the first sector, `tsdb.parent.oldest_addr` SHALL be initialized, and `tsdb.last_time` SHALL be set to 0

Scenario (error path):
  GIVEN a database where sector files exist but have corrupted magic words
  WHEN `fdb_tsdb_init` scans the sectors
  THEN sectors with invalid headers SHALL be auto-formatted (if `not_formatable == false`), and the best valid sector SHALL become `cur_sec`

Scenario (boundary condition):
  GIVEN a database with exactly 2 sectors (minimum configuration)
  WHEN `fdb_tsdb_init` scans
  THEN both sectors SHALL be examined, and the ring-buffer logic SHALL handle wrap-around correctly (next after sector 1 wraps to sector 0)

### REQ-tsdb-sector-layout-002: TSDB sector header SHALL include start_time and dual end_info slots

C source reference: `src/fdb_tsdb.c:229`

Scenario (normal path):
  GIVEN a sector that has been used for TSL appends
  WHEN `tsdb_read_sector_info` reads the header
  THEN `sec.start_time`, `sec.end_time`, `sec.end_idx`, and `sec.end_info_stat[0]` / `[1]` SHALL be populated from the sector header data

Scenario (error path):
  GIVEN both end_info slots are uninitialized (0xFF, never written)
  WHEN `tsdb_read_sector_info` parses end_info
  THEN `end_info_stat` SHALL reflect the erased state (UNUSED), and the sector SHALL be treated as either EMPTY or improperly closed

Scenario (boundary condition):
  GIVEN one end_info slot is valid and the other is corrupt
  WHEN `tsdb_read_sector_info` evaluates end_info
  THEN the valid slot SHALL be used (crash resilience: dual-slot scheme protects against interrupted writes)

### REQ-tsdb-sector-layout-003: get_next_sector_addr SHALL wrap at max_size boundary

C source reference: `src/fdb_tsdb.c:177`

Scenario (normal path):
  GIVEN `sec_size=4096`, `max_size=16384` (4 sectors), and `cur_addr=0x2000` (sector 2)
  WHEN `tsdb_get_next_sector_addr(&tsdb, 0x2000)` is called
  THEN the function SHALL return `0x3000` (sector 3)

Scenario (error path):
  N/A -- Pure arithmetic function, no error states.

Scenario (boundary condition):
  GIVEN `cur_addr=0x3000` (last sector) with `max_size=16384`
  WHEN `tsdb_get_next_sector_addr` is called
  THEN the function SHALL return `0x0000` (wrap to sector 0)

## Invariants

- **INV-tsdb-sector-layout-001**: TSDB sector header magic word SHALL be `0x33424446` (distinct from KVDB's `0x30424446` and KV's `0x32424446`).
- **INV-tsdb-sector-layout-002**: `tsdb.cur_sec` SHALL always point to a sector that is either EMPTY or USING (the active write-target sector). It SHALL NEVER point to a FULL sector (unless the database has no empty sectors and `rollover == false`).
- **INV-tsdb-sector-layout-003**: The ring buffer wraps around: `get_next_sector_addr(last_sector)` returns `0` (the first sector).
- **INV-tsdb-sector-layout-004**: On init, `tsdb.last_time` SHALL be set to the end_time of the most recently written sector with valid data, or 0 if the database is completely empty.

## Dependencies

- `foundational-types` -- Uses `FdbTsdb`, `TsdbSecInfo`, `FdbSectorStoreStatus`, `FdbTime`, `FdbError`.
- `flash-io-dispatch` -- All sector I/O through `FlashStorage` trait.
- `flash-status-table` -- Sector status transitions use status tables.
- `database-lifecycle` -- `fdb_tsdb_init` calls `fdb_init_ex` and `fdb_init_finish`.
