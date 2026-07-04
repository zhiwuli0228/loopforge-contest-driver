## ADDED Requirements

### Requirement: TSDB Initialization

`TsDb::init(name, path, get_time_fn, max_len, user_data)` SHALL initialize the time-series database, scanning existing sectors and determining the current write position.

#### Scenario: Fresh TSDB format on first init

- **WHEN** a TSDB is initialized on empty storage
- **THEN** the first sector SHALL be formatted with `SECTOR_MAGIC_WORD` (`T`, `S`, `L`, `0` = `0x304C5354`)
- **AND** the sector header SHALL include: `status (FDB_SECTOR_STORE_USING)`, `magic`, `start_time` (= `0xFFFFFFFF` for unused), two `end_info` slots (each with `time = 0xFFFFFFFF`, `index = 0xFFFFFFFF`, `status = FDB_TSL_UNUSED`)
- **AND** all remaining sectors SHALL be formatted as `FDB_SECTOR_STORE_EMPTY`
- **AND** `cur_sec` SHALL point to the formatted first sector

#### Scenario: TSDB recovery on re-init

- **WHEN** a TSDB is re-initialized on existing storage
- **THEN** the recovery SHALL scan all sector headers
- **AND** verify magic words; mark sectors as invalid if magic mismatch
- **AND** identify the "using" sector (the one with status `FDB_SECTOR_STORE_USING`)
- **AND** scan the using sector from start to end to find the last valid TSL (status `FDB_TSL_WRITE`)
- **AND** if a partially-written TSL is found (status `FDB_TSL_PRE_WRITE`), treat it as the end of valid data
- **AND** set `cur_sec.empty_idx` to the next write position
- **AND** set `cur_sec.empty_data` to the next data position (data is written from sector end backwards)
- **AND** `last_time` SHALL be set from the last valid TSL's timestamp

#### Scenario: TSDB sector store status transitions

- **WHEN** a new sector is allocated for writing
- **THEN** its store status SHALL transition: `FDB_SECTOR_STORE_UNUSED` → `FDB_SECTOR_STORE_EMPTY` → `FDB_SECTOR_STORE_USING`
- **WHEN** a sector is filled
- **THEN** its store status SHALL transition to `FDB_SECTOR_STORE_FULL`
- **AND** `end_info[0]` (primary) SHALL be written with the last TSL's time, index, and status
- **AND** `end_info[1]` (backup) SHALL be written as a copy for crash resilience

#### Scenario: TSDB deinitialization

- **WHEN** `TsDb::deinit()` is called
- **THEN** the database SHALL be deinitialized via `_fdb_deinit`
- **AND** `cur_sec` state SHALL be cleared

---

### Requirement: TSL Append

`TsDb::append(blob)` SHALL write a time-series log entry with auto-generated timestamp, and `TsDb::append_with_ts(blob, ts)` SHALL write with an explicit timestamp.

#### Scenario: Append with auto-generated timestamp

- **WHEN** `TsDb::append(blob)` is called
- **THEN** the `get_time` callback SHALL be invoked to obtain the current timestamp
- **AND** if the auto-generated timestamp < `last_time`, it SHALL be set to `last_time + 1`
- **AND** if the auto-generated timestamp is still < `last_time` (after correction), return `FdbError::InitFailed` (no valid time)

#### Scenario: TSL index and data layout within a sector

- **WHEN** a TSL is appended
- **THEN** the TSL index SHALL be written at `cur_sec.empty_idx` (growing upward from sector start + header)
- **AND** the TSL index SHALL contain: `status_table` (transitioning `FDB_TSL_PRE_WRITE` → `FDB_TSL_WRITE`), `time`, `log_len`, `log_addr`
- **AND** the TSL log data SHALL be written at `cur_sec.empty_data - log_len` (growing downward from sector end)
- **AND** `log_addr` SHALL point to the written data location

#### Scenario: Sector rollover when full

- **WHEN** a TSL append would exceed the remaining space in the current sector (index area would overlap with data area)
- **THEN** the current sector SHALL be finalized: status set to `FDB_SECTOR_STORE_FULL`, `end_info[0]` and `end_info[1]` written
- **AND** the next sector SHALL be allocated
- **AND** if all sectors are full and `rollover` is `true`, the oldest sector SHALL be reused (overwritten)
- **AND** the new sector SHALL be formatted as `FDB_SECTOR_STORE_USING` with `start_time` set to the TSL's timestamp
- **AND** the TSL SHALL be appended to the new sector

#### Scenario: Rollover behavior with oldest sector

- **WHEN** all sectors are full and a new TSL needs to be written
- **AND** `rollover` is `true`
- **THEN** the oldest sector (by `oldest_addr`) SHALL be identified
- **AND** it SHALL be erased (set all bytes to `0xFF`) and reformatted as `FDB_SECTOR_STORE_EMPTY`
- **AND** `oldest_addr` SHALL advance to the next sector
- **AND** the new sector SHALL be used for the TSL

#### Scenario: Append without rollover

- **WHEN** all sectors are full and a new TSL needs to be written
- **AND** `rollover` is `false`
- **THEN** the append SHALL return `FdbError::SavedFull`

---

### Requirement: TSL Iteration

TSL iteration SHALL support forward, reverse, and time-range-based traversal using callback functions.

#### Scenario: Forward iteration

- **WHEN** `TsDb::iter(callback, arg)` is called
- **THEN** the iterator SHALL traverse sectors from `oldest_addr` to `cur_sec`
- **AND** for each sector: iterate TSLs by index from sector start to `end_idx` (or `empty_idx` for current sector)
- **AND** for each TSL with status `FDB_TSL_WRITE`: invoke the callback with the TSL data and `arg`
- **AND** if the callback returns `false`, stop iteration

#### Scenario: Reverse iteration

- **WHEN** `TsDb::iter_reverse(callback, arg)` is called
- **THEN** the iterator SHALL traverse sectors from `cur_sec` backward to `oldest_addr`
- **AND** for each sector: iterate TSLs by index in reverse order
- **AND** invoke the callback for each valid TSL
- **AND** if the callback returns `false`, stop iteration

#### Scenario: Time-range iteration

- **WHEN** `TsDb::iter_by_time(from, to, callback, arg)` is called
- **THEN** the iterator SHALL use sector `end_time` metadata to skip sectors wholly outside the time range
- **AND** sectors whose `end_time < from` SHALL be skipped (data before range)
- **AND** sectors whose `start_time > to` SHALL be skipped (data after range)
- **AND** for sectors within range: iterate individual TSLs, filtering those with `time` within `[from, to]`
- **AND** invoke the callback only for matching TSLs

#### Scenario: Query count

- **WHEN** `TsDb::query_count(from, to, status_filter)` is called
- **THEN** the function SHALL count TSLs within the time range `[from, to]` that match the given status
- **AND** use sector-level time filtering for efficiency (skip sectors outside range)
- **AND** return the count as `usize`

#### Scenario: Set TSL status

- **WHEN** `TsDb::set_status(tsl, new_status)` is called
- **THEN** the TSL's status table SHALL be updated in flash to reflect the new status
- **AND** if the new status is a later status in the write-once chain, only the specific bits SHALL be cleared
- **AND** return `Result<(), FdbError>`

#### Scenario: Clean TSDB (delete all TSLs)

- **WHEN** `TsDb::clean()` is called
- **THEN** all sectors SHALL be iterated
- **AND** all TSLs SHALL have their status set to `FDB_TSL_DELETED`
- **AND** the `cur_sec` SHALL be reset to point to a newly formatted sector

---

### Requirement: Crash Resilience with Two End-Info Slots

TSDB sector headers SHALL maintain two `end_info` slots to protect against crash during sector finalization.

#### Scenario: Primary and backup end-info writing

- **WHEN** a sector is finalized (marked `FULL`)
- **THEN** `end_info[0]` SHALL be written first (time, index, status of last TSL)
- **AND** `end_info[1]` SHALL be written second as a copy
- **AND** during recovery: if `end_info[0]` is valid, use it; if corrupted, fall back to `end_info[1]`

#### Scenario: Recovery from partially-written end-info

- **WHEN** a crash occurs between writing `end_info[0]` and `end_info[1]`
- **THEN** recovery SHALL detect `end_info[0]` as valid and `end_info[1]` as `0xFFFFFFFF` (erased/unwritten)
- **AND** use `end_info[0]` values to determine the sector boundary

#### Scenario: Both end-info slots corrupted

- **WHEN** recovery finds both `end_info[0]` and `end_info[1]` invalid (or unwritten)
- **THEN** the sector SHALL be scanned linearly to find the last valid TSL (status `FDB_TSL_WRITE`)
- **AND** the sector boundary SHALL be set at the last valid TSL

---

### Requirement: TSL Status Management

The TSL status enum SHALL support write-once status transitions: `FDB_TSL_UNUSED` → `FDB_TSL_PRE_WRITE` → `FDB_TSL_WRITE` → `FDB_TSL_USER_STATUS1` → `FDB_TSL_DELETED` → `FDB_TSL_USER_STATUS2`.

#### Scenario: Status table encoding for TSL

- **WHEN** a TSL is written
- **THEN** the status SHALL be encoded in the TSL's `status_table` using `_fdb_set_status` / `_fdb_get_status` with `FDB_TSL_STATUS_NUM = 6`
- **AND** the write granularity (`FDB_WRITE_GRAN`) SHALL determine the byte/bit-level encoding of each status step

#### Scenario: User-defined status values

- **WHEN** `FDB_TSL_USER_STATUS1` is applied to a TSL
- **THEN** the TSL SHALL remain visible to iterators and queries (status >= `FDB_TSL_WRITE` and not deleted)
- **WHEN** `FDB_TSL_USER_STATUS2` is applied to a deleted TSL
- **THEN** the TSL SHALL be treated as deleted (not visible to default iterators)
