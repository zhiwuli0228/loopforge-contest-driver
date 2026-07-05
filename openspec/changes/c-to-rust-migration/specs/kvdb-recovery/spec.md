# Spec: KVDB Crash Recovery and Integrity

## Capability Overview

This capability implements crash recovery executed automatically on KVDB initialization. It detects and repairs: interrupted writes (PRE_WRITE -> ERR_HDR), interrupted deletes (PRE_DELETE -> move KV to recovery location), and interrupted GC (DIRTY_GC -> resume GC). Also performs sector header validation with auto-format for corrupted sectors, and provides a public integrity check API (`fdb_kvdb_check`). The recovery module is the first thing that runs after the base `fdb_init_ex`.

## Key Functions

| C Function | C File:Line | Rust Equivalent | Behavior Summary |
|------------|-------------|-----------------|------------------|
| `_fdb_kv_load` | `src/fdb_kvdb.c:1616` | `fn fdb_kv_load(kvdb: &mut FdbKvdb, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Full KVDB init: sector scan, recovery, default KV setup |
| `fdb_kvdb_check` | `src/fdb_kvdb.c:1876` | `fn fdb_kvdb_check(kvdb: &FdbKvdb, flash: &dyn FlashStorage) -> Result<(), FdbError>` | Public integrity check: validate all sector headers and KV headers |
| `fdb_kvdb_init` | `src/fdb_kvdb.c:1753` | `fn fdb_kvdb_init(kvdb: &mut FdbKvdb, name: &str, path: &str) -> Result<(), FdbError>` | Full KVDB initialization: lifecycle + type-specific setup |
| `fdb_kvdb_deinit` | `src/fdb_kvdb.c:1825` | `fn fdb_kvdb_deinit(kvdb: &mut FdbKvdb)` | Clean shutdown |
| `fdb_kvdb_control` | `src/fdb_kvdb.c:1895` | `fn fdb_kvdb_control(kvdb: &mut FdbKvdb, cmd: u32, arg: usize)` | Runtime configuration (set sector size, lock/unlock, file mode) |
| `check_and_recovery_kv_cb` | `src/fdb_kvdb.c:1594` | `fn check_and_recovery_kv_cb(kvdb: &mut FdbKvdb, kv: &mut FdbKv, blob: &FdbBlob, flash: &mut dyn FlashStorage) -> bool` | Per-KV callback: repair PRE_WRITE/PRE_DELETE KVs during init |
| `check_and_recovery_gc_cb` | `src/fdb_kvdb.c:1604` | `fn check_and_recovery_gc_cb(kvdb: &mut FdbKvdb, sec_addr: u32, flash: &mut dyn FlashStorage) -> bool` | Per-sector callback: detect DIRTY_GC and resume GC |
| `check_sec_hdr_cb` | `src/fdb_kvdb.c:1563` | `fn check_sec_hdr_cb(kvdb: &mut FdbKvdb, sec_addr: u32, flash: &mut dyn FlashStorage) -> bool` | Validate sector headers, auto-format bad sectors, track oldest sector |
| `kv_auto_update` | `src/fdb_kvdb.c:1858` | N/A -- deferred | Auto-update KVs (deferred: `FDB_KV_AUTO_UPDATE` feature) |

## Data Structures

N/A -- Uses existing `FdbKv`, `KvdbSecInfo`, `FdbKvdb`.

## Requirements

### REQ-kvdb-recovery-001: fdb_kvdb_init SHALL run recovery before marking init_ok

C source reference: `src/fdb_kvdb.c:1753`

Scenario (normal path):
  GIVEN a fresh database directory
  WHEN `fdb_kvdb_init(&mut kvdb, "kv", "/data/kv")` is called
  THEN the function SHALL call `fdb_init_ex`, then `fdb_kv_load`, then `fdb_init_finish`, and return `Ok(())`

Scenario (error path):
  GIVEN `fdb_init_ex` fails (e.g., bad sector size)
  WHEN `fdb_kvdb_init` is called
  THEN `fdb_init_finish` SHALL be called with the error status, `init_ok` SHALL remain `false`, and the error SHALL be propagated

Scenario (boundary condition):
  GIVEN `init_ok` is already `true` (re-init)
  WHEN `fdb_kvdb_init` is called
  THEN `fdb_init_ex` SHALL return `Ok(())` immediately (idempotent), and recovery SHALL NOT re-run

### REQ-kvdb-recovery-002: check_and_recovery_kv_cb SHALL repair PRE_WRITE KVs

C source reference: `src/fdb_kvdb.c:1594`

Scenario (normal path):
  GIVEN a WRITE-status KV -- valid, no repair needed
  WHEN `check_and_recovery_kv_cb` inspects it
  THEN the callback SHALL return `true` (continue iterating) without modifying the KV

Scenario (error path):
  GIVEN a PRE_WRITE-status KV (interrupted write -- header written but data may be incomplete)
  WHEN `check_and_recovery_kv_cb` detects PRE_WRITE
  THEN the KV SHALL be transitioned to ERR_HDR status (mark as corrupt), and the callback SHALL continue

Scenario (boundary condition):
  GIVEN a PRE_DELETE-status KV (interrupted delete)
  WHEN `check_and_recovery_kv_cb` detects PRE_DELETE
  THEN if space allows, the KV SHALL be moved to a new valid location (preserving the data that the interrupted delete was about to remove)

### REQ-kvdb-recovery-003: check_sec_hdr_cb SHALL auto-format sectors with bad headers

C source reference: `src/fdb_kvdb.c:1563`

Scenario (normal path):
  GIVEN a sector with valid magic word and valid combined/status values
  WHEN `check_sec_hdr_cb` inspects the header
  THEN the sector SHALL pass validation, be added to the sector cache, and tracked for oldest sector detection

Scenario (error path):
  GIVEN a sector with invalid magic word (corrupted or never formatted)
  WHEN `check_sec_hdr_cb` inspects it and `not_formatable == false`
  THEN the sector SHALL be auto-formatted (erased + new header), and the callback SHALL continue

Scenario (boundary condition):
  GIVEN `not_formatable == true` (database is locked from formatting)
  WHEN `check_sec_hdr_cb` encounters a bad sector
  THEN the sector SHALL NOT be formatted -- it SHALL be skipped, and `in_recovery_check` SHALL track the error

### REQ-kvdb-recovery-004: fdb_kvdb_check SHALL validate all sector headers and KV CRCs

C source reference: `src/fdb_kvdb.c:1876`

Scenario (normal path):
  GIVEN a database where all sectors have valid headers and all KVs have valid CRC32
  WHEN `fdb_kvdb_check(&kvdb, &flash)` is called
  THEN the function SHALL return `Ok(())`

Scenario (error path):
  GIVEN one sector has a bad magic word
  WHEN `fdb_kvdb_check` scans
  THEN the function SHALL return `Err(FdbError::ReadErr)` (or the first encountered error)

Scenario (boundary condition):
  GIVEN an empty database (all sectors formatted but no KVs)
  WHEN `fdb_kvdb_check` is called
  THEN the function SHALL return `Ok(())` -- no KVs to validate means no errors

### REQ-kvdb-recovery-005: check_and_recovery_gc_cb SHALL resume interrupted GC

C source reference: `src/fdb_kvdb.c:1604`

Scenario (normal path):
  GIVEN a sector with `DIRTY_FALSE` or `DIRTY_TRUE` status
  WHEN `check_and_recovery_gc_cb` inspects it
  THEN the callback SHALL return `true` (continue scanning) without GC action

Scenario (error path):
  GIVEN a sector with `DIRTY_GC` status (GC was interrupted)
  WHEN `check_and_recovery_gc_cb` detects `DIRTY_GC`
  THEN `do_gc` SHALL be called on the sector to resume GC

Scenario (boundary condition):
  GIVEN a `DIRTY_GC` sector where all KVs have already been moved (GC was 99% complete)
  WHEN recovery calls `do_gc`
  THEN the sector SHALL be formatted (no valid KVs to move), completing the interrupted GC

## Invariants

- **INV-kvdb-recovery-001**: Recovery SHALL run automatically as part of `_fdb_kv_load`, before `init_ok` is set. It SHALL NOT require an explicit user call.
- **INV-kvdb-recovery-002**: On PRE_WRITE detection, the KV SHALL be marked ERR_HDR. This is a one-way transition -- the corrupted data fragment is abandoned.
- **INV-kvdb-recovery-003**: On PRE_DELETE detection, the KV SHALL be moved to a new sector if possible, preserving the data. If space is unavailable, the KV may be lost.
- **INV-kvdb-recovery-004**: Recovery SHALL be idempotent: running recovery on an already-recovered database SHALL produce the same result (no double-repair).
- **INV-kvdb-recovery-005**: After recovery, all sectors SHALL have valid magic words (formatted during recovery if needed), and all KVs SHALL be in a stable state (WRITE or DELETED, not PRE_WRITE or PRE_DELETE).

## Dependencies

- `kvdb-sector-management` -- Sector formatting, info reading, status updates, iteration.
- `kv-crud` -- KV read, write, delete operations used during recovery.
- `kvdb-garbage-collection` -- `do_gc` for resuming interrupted GC.
- `kvdb-iteration` -- `kv_iterator` for scanning KVs in each sector.
- `database-lifecycle` -- Init/deinit lifecycle coordination.
