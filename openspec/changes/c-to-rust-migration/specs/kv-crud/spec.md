# Spec: KV CRUD Operations

## Capability Overview

This capability implements the full create/read/update/delete lifecycle for key-value pairs stored on flash. It supports both string and blob (binary) values. Uses a 2-phase delete protocol (PRE_DELETE then DELETED) for crash safety. Maintains an LRU-based KV name cache for fast repeated lookups and CRC32 integrity checking on every read. This is the primary user-facing API for the Key-Value Database.

## Key Functions

| C Function | C File:Line | Rust Equivalent | Behavior Summary |
|------------|-------------|-----------------|------------------|
| `fdb_kv_set` | `src/fdb_kvdb.c:1369` | `fn fdb_kv_set(kvdb: &mut FdbKvdb, key: &str, value: &str, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Set string KV value (public API) |
| `fdb_kv_get` | `src/fdb_kvdb.c:732` | `fn fdb_kv_get(kvdb: &FdbKvdb, key: &str, flash: &dyn FlashStorage) -> Option<String>` | Get string KV value (returns `Option<String>` instead of static buffer) |
| `fdb_kv_set_blob` | `src/fdb_kvdb.c:1339` | `fn fdb_kv_set_blob(kvdb: &mut FdbKvdb, key: &str, blob: &FdbBlob, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Set blob KV value (public API) |
| `fdb_kv_get_blob` | `src/fdb_kvdb.c:701` | `fn fdb_kv_get_blob(kvdb: &FdbKvdb, key: &str, blob: &mut FdbBlob, flash: &dyn FlashStorage) -> usize` | Get blob KV value, returns bytes read |
| `fdb_kv_del` | `src/fdb_kvdb.c:1275` | `fn fdb_kv_del(kvdb: &mut FdbKvdb, key: &str, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Delete a KV entry by key name |
| `fdb_kv_get_obj` | `src/fdb_kvdb.c:655` | `fn fdb_kv_get_obj(kvdb: &FdbKvdb, key: &str, flash: &dyn FlashStorage) -> Option<FdbKv>` | Get KV object by key (returns full KV metadata) |
| `fdb_kv_to_blob` | `src/fdb_kvdb.c:683` | `fn fdb_kv_to_blob(kv: &FdbKv, blob: &mut FdbBlob)` | Convert KV object to blob for reading value |
| `fdb_kv_set_default` | `src/fdb_kvdb.c:1386` | `fn fdb_kv_set_default(kvdb: &mut FdbKvdb, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Reset all KVs to their default values |
| `set_kv` | `src/fdb_kvdb.c:1295` | `fn set_kv(kvdb: &mut FdbKvdb, key: &str, blob: &FdbBlob, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Internal: unified KV set with space check, old KV delete, GC trigger |
| `get_kv` | `src/fdb_kvdb.c:622` | `fn get_kv(kvdb: &FdbKvdb, kv_addr: u32, blob: &mut FdbBlob, flash: &dyn FlashStorage) -> Result<usize, FdbError>` | Internal: read KV value data from flash at given address |
| `create_kv_blob` | `src/fdb_kvdb.c:1184` | `fn create_kv_blob(kvdb: &mut FdbKvdb, kv: &FdbKv, blob: &FdbBlob, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Internal: write a new KV header and blob data to flash |
| `find_kv` | `src/fdb_kvdb.c:585` | `fn find_kv(kvdb: &FdbKvdb, key: &str, kv: &mut FdbKv, flash: &dyn FlashStorage) -> bool` | Find KV by key name, using cache first then full scan |
| `del_kv` | `src/fdb_kvdb.c:940` | `fn del_kv(kvdb: &mut FdbKvdb, key: &str, old_kv: Option<&FdbKv>, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Internal: delete KV with status transition (PRE_DELETE -> DELETED) |
| `write_kv_hdr` | `src/fdb_kvdb.c:1440` | `fn write_kv_hdr(kvdb: &FdbKvdb, addr: u32, kv: &FdbKv, flash: &mut dyn FlashStorage) -> Result<(), FdbError>` | Write KV header with CRC32 to flash |

## Data Structures

| C Struct | Fields | Rust Equivalent | Notes |
|----------|--------|----------------|-------|
| `fdb_kv` | `status, crc_is_ok, name_len, magic, len, value_len, name[FDB_KV_NAME_MAX], addr.start, addr.value` | `FdbKv { status: FdbKvStatus, crc_is_ok: bool, name_len: u8, magic: u32, len: u32, value_len: u32, name: [u8; FDB_KV_NAME_MAX], addr_start: u32, addr_value: u32 }` | `#[repr(C)]` for byte-buffer deserialization |

## Requirements

### REQ-kv-crud-001: fdb_kv_set SHALL create or update a KV with 2-phase delete

C source reference: `src/fdb_kvdb.c:1369, 1295`

Scenario (normal path):
  GIVEN an initialized KVDB and a key "sensor1" that does not exist
  WHEN `fdb_kv_set(&mut kvdb, "sensor1", "42.5", &mut flash)` is called
  THEN a new KV SHALL be created on flash with CRC32 covering the name and value, the KV cache SHALL be updated, and the function SHALL return `Ok(())`

Scenario (error path):
  GIVEN a key name longer than `FDB_KV_NAME_MAX` (64 chars)
  WHEN `fdb_kv_set` is called
  THEN the function SHALL return `Err(FdbError::KvNameErr)`

Scenario (boundary condition):
  GIVEN a key "sensor1" that already exists with value "42.5"
  WHEN `fdb_kv_set(&mut kvdb, "sensor1", "99.9", &mut flash)` is called
  THEN the old KV SHALL be marked PRE_DELETE, the new KV SHALL be written, then the old KV SHALL be marked DELETED (2-phase delete for crash safety)

### REQ-kv-crud-002: fdb_kv_get SHALL return Option<String> (no static buffer)

C source reference: `src/fdb_kvdb.c:732`

Scenario (normal path):
  GIVEN a KV "sensor1" with value "42.5" exists on flash
  WHEN `fdb_kv_get(&kvdb, "sensor1", &flash)` is called
  THEN the function SHALL find the KV, verify CRC32, read the value from flash, and return `Some("42.5".to_string())`

Scenario (error path):
  GIVEN a key "nonexistent" that does not exist
  WHEN `fdb_kv_get` is called
  THEN `find_kv` SHALL return false, and the function SHALL return `None`

Scenario (boundary condition):
  GIVEN a KV exists but its CRC32 is corrupt (flash bit-flip)
  WHEN `fdb_kv_get` reads and validates the KV
  THEN `crc_is_ok` SHALL be `false`, and the function SHALL return `None` (treated as not found)

### REQ-kv-crud-003: fdb_kv_del SHALL delete a KV using 2-phase status transition

C source reference: `src/fdb_kvdb.c:1275, 940`

Scenario (normal path):
  GIVEN a KV "sensor1" exists on flash
  WHEN `fdb_kv_del(&mut kvdb, "sensor1", &mut flash)` is called
  THEN the KV status SHALL transition from WRITE to PRE_DELETE (flash write), then to DELETED (another flash write), the KV SHALL be removed from the cache, and the function SHALL return `Ok(())`

Scenario (error path):
  GIVEN a key "nonexistent" that does not exist
  WHEN `fdb_kv_del` is called
  THEN `find_kv` SHALL return false, and the function SHALL return `Err(FdbError::KvNameErr)`

Scenario (boundary condition):
  GIVEN a crash occurs after PRE_DELETE but before DELETED
  WHEN the database is re-initialized
  THEN the recovery routine (`check_and_recovery_kv_cb`) SHALL move the partially-deleted KV to a new valid location

### REQ-kv-crud-004: fdb_kv_get_blob SHALL read at most blob.size bytes

C source reference: `src/fdb_kvdb.c:701`

Scenario (normal path):
  GIVEN a blob KV "config" with value `[0x00..0xFF]` (256 bytes) and a blob buffer of size 256
  WHEN `fdb_kv_get_blob(&kvdb, "config", &mut blob, &flash)` is called
  THEN the function SHALL read the full value from flash into `blob.buf`, update `blob.saved_len`, and return `256`

Scenario (error path):
  GIVEN a KV whose value is larger than the provided blob buffer
  WHEN `fdb_kv_get_blob` is called
  THEN the function SHALL read at most `blob.size` bytes (truncation, not overflow), updating `blob.saved_len` to the full stored size

Scenario (boundary condition):
  GIVEN `blob.size == 0` (zero-size buffer)
  WHEN `fdb_kv_get_blob` is called
  THEN the function SHALL return `0` without reading flash

### REQ-kv-crud-005: Every KV write SHALL include CRC32 over header name and value

C source reference: `src/fdb_kvdb.c:1440`

Scenario (normal path):
  GIVEN a KV with name "test" (4 bytes) and value "data" (4 bytes)
  WHEN `write_kv_hdr` writes the KV header to flash
  THEN the CRC32 SHALL cover `name_len + value_len + name + value` = 12 bytes, and the stored CRC SHALL match `fdb_calc_crc32(0, combined_data)`

Scenario (error path):
  GIVEN a flash write error during header write
  WHEN `write_kv_hdr` writes the CRC and header
  THEN the function SHALL return the error -- a partial header SHALL NOT be left on flash

Scenario (boundary condition):
  GIVEN a zero-length value (`value_len=0`)
  WHEN `write_kv_hdr` computes CRC32
  THEN the CRC SHALL cover only the name data (not an empty value), and the resulting CRC SHALL be correct

## Invariants

- **INV-kv-crud-001**: Every KV header written to flash SHALL include a valid CRC32 covering `name_len + value_len + name + value`. On read, CRC SHALL be verified against this data.
- **INV-kv-crud-002**: The 2-phase delete protocol SHALL be used for all KV deletions: PRE_DELETE status written first, new KV written (if update), then old KV status changed to DELETED.
- **INV-kv-crud-003**: `fdb_kv_set` with a NULL/empty value SHALL call `del_kv` (delete behavior), not create an empty-valued KV.
- **INV-kv-crud-004**: KV name SHALL be at most `FDB_KV_NAME_MAX` (64) bytes. KV total size (header + name + value) SHALL be at most `sec_size - SECTOR_HDR_DATA_SIZE`.
- **INV-kv-crud-005**: The KV cache SHALL be updated on every successful KV find, write, and delete to maintain consistency between cache and flash state.

## Dependencies

- `foundational-types` -- Uses `FdbKvdb`, `FdbKv`, `FdbBlob`, `FdbKvStatus`, `FdbError`, `FDB_KV_NAME_MAX`.
- `flash-io-dispatch` -- All flash reads and writes.
- `flash-status-table` -- KV status transitions use status tables.
- `crc32-computation` -- CRC32 integrity check on every KV read/write.
- `blob-abstraction` -- Blob operations for creating and reading KV values.
- `database-lifecycle` -- Requires `init_ok == true`.
- `kvdb-sector-management` -- KV allocation, sector formatting, space management.
