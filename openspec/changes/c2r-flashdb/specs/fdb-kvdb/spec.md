## ADDED Requirements

### Requirement: KVDB Initialization

`KvDb::init(name, path, default_kvs, user_data)` SHALL initialize the key-value database, including sector scanning, format detection, and default key-value provisioning.

#### Scenario: Fresh KVDB format on first init

- **WHEN** a KVDB is initialized on empty storage (all sectors are `FDB_SECTOR_STORE_UNUSED`)
- **THEN** the first sector SHALL be formatted with `SECTOR_MAGIC_WORD`, status set to `FDB_SECTOR_STORE_USING`
- **AND** all remaining sectors SHALL be formatted as `FDB_SECTOR_STORE_EMPTY` with `SECTOR_NOT_COMBINED`
- **AND** the database SHALL be marked as `init_ok = true`

#### Scenario: KVDB recovery check on re-init

- **WHEN** a KVDB is re-initialized on storage that already has formatted sectors
- **THEN** the recovery check SHALL scan all sector headers
- **AND** for each sector: read store status, dirty status, magic word, combined number
- **AND** verify the magic word matches `SECTOR_MAGIC_WORD`; if mismatch, mark the sector as `check_ok = false` and skip
- **AND** build the sector cache table with valid sectors
- **AND** scan all KVs in valid sectors for CRC32 integrity; mark corrupted KVs with `FDB_KV_ERR_HDR`
- **AND** if a sector has status `FDB_SECTOR_STORE_UNUSED`, reformat it

#### Scenario: Default KVs are set on empty database

- **WHEN** `default_kvs` is provided during initialization and no existing user KVs are found
- **THEN** each default KV SHALL be written to the database via `_fdb_kv_set_ex`
- **AND** after writing, the KV SHALL be verified by reading it back
- **AND** the `set_default` flag SHALL prevent formatting if `not_formatable` is set

#### Scenario: KVDB deinitialization

- **WHEN** `KvDb::deinit()` is called
- **THEN** the database SHALL be deinitialized via `_fdb_deinit`
- **AND** the KV cache table SHALL be cleared (all entries set to default/zero)
- **AND** the sector cache table SHALL be cleared

---

### Requirement: KV Storage (Create, Read, Update, Delete)

KV create/read/update/delete operations SHALL preserve the on-flash format (KV header with status table, magic, length, CRC32, name_len, value_len, followed by name and value data).

#### Scenario: Create a new KV

- **WHEN** `KvDb::set(key, value)` is called with a key that does not exist
- **THEN** the function SHALL allocate space for a new KV node (header + name + value, all aligned to `FDB_WRITE_GRAN`)
- **AND** the KV header SHALL be written with status transitioning through `FDB_KV_PRE_WRITE` → `FDB_KV_WRITE`
- **AND** the name SHALL be CRC32-checked and stored in the write buffer
- **AND** the value SHALL be CRC32-checked and stored in the write buffer
- **AND** the CRC32 SHALL cover `name_len + value_len + name + value` (excluding the CRC32 field itself)
- **AND** return `Result<(), FdbError>`

#### Scenario: Read a KV by name

- **WHEN** `KvDb::get(key)` is called with an existing key
- **THEN** the function SHALL search all sectors (starting from oldest) for a KV matching the key name
- **AND** if the KV cache is enabled, SHALL check the cache first (by name CRC16 hash)
- **AND** for each candidate KV: read the header, verify CRC32, verify KV status is `FDB_KV_WRITE`
- **AND** if `FDB_KV_PRE_DELETE` or `FDB_KV_DELETED`, skip to next sector
- **AND** return `Option<String>` with the value (for string mode), or `Option<Vec<u8>>` (for blob mode)

#### Scenario: Update an existing KV

- **WHEN** `KvDb::set(key, new_value)` is called with an existing key
- **THEN** the function SHALL first mark the existing KV as `FDB_KV_PRE_DELETE` via status table write
- **AND** then mark the existing KV as `FDB_KV_DELETED`
- **AND** then create a new KV node with the updated value at the current sector's empty address
- **AND** the cache entry SHALL be updated to point to the new address
- **AND** return `Result<(), FdbError>`

#### Scenario: Delete a KV

- **WHEN** `KvDb::del(key)` is called with an existing key
- **THEN** the function SHALL search for the KV by name across all sectors
- **AND** mark the KV's status as `FDB_KV_PRE_DELETE` via status table write
- **AND** then `FDB_KV_DELETED`
- **AND** the cache entry SHALL be removed or invalidated
- **AND** return `Result<(), FdbError>`

#### Scenario: Delete a non-existent KV

- **WHEN** `KvDb::del(key)` is called with a key that does not exist
- **THEN** the function SHALL return `FdbError::KvNameErr` (or `FdbError::NoErr` — preserves C behavior where a non-existent key is not an error for deletion)

#### Scenario: KV storage using blob data

- **WHEN** `KvDb::set_blob(key, blob)` or `KvDb::get_blob(key, blob)` is called
- **THEN** the blob's `saved` metadata SHALL track the KV address (`meta_addr`), data address (`addr`), and length (`len`)
- **AND** `get_blob` SHALL read the blob data from flash at `blob.saved.addr` into `blob.buf`
- **AND** return the number of bytes read

#### Scenario: Storage full condition

- **WHEN** a KV write operation finds insufficient space in the current sector
- **THEN** the current sector SHALL be marked as `FDB_SECTOR_STORE_FULL`
- **AND** the next sector SHALL be allocated as `FDB_SECTOR_STORE_USING`
- **AND** if no empty sector is available and GC threshold is reached, GC SHALL be triggered
- **AND** if no empty sector is available after GC, return `FdbError::SavedFull`

---

### Requirement: KV Header CRC32 Integrity

Every KV header SHALL include a CRC32 checksum computed over `name_len + value_len + name + value`, and every KV read SHALL verify the CRC32.

#### Scenario: CRC32 computation for a KV node

- **WHEN** a KV node is written to flash
- **THEN** the CRC32 SHALL be computed starting with `crc = 0`
- **AND** the CRC32 SHALL be fed `name_len` (as a 4-byte uint32 aligned write), `value_len` (as a 4-byte uint32 aligned write), then the name bytes, then the value bytes
- **AND** the CRC32 SHALL be stored in the KV header's `crc32` field

#### Scenario: CRC32 verification on KV read

- **WHEN** a KV node is read from flash
- **THEN** the CRC32 SHALL be recomputed over the same data and compared to the stored CRC32
- **AND** if the CRC32 does not match, the KV status SHALL be set to `FDB_KV_ERR_HDR` and the KV SHALL be treated as invalid
- **AND** if the CRC32 matches, `crc_is_ok` SHALL be set to `true`

---

### Requirement: KV Cache

When `FDB_KV_USING_CACHE` is enabled, the LRU-like KV cache SHALL accelerate KV lookups.

#### Scenario: Cache lookup on KV read

- **WHEN** a KV is being read by name
- **THEN** the name's CRC16 (low 16 bits of CRC32 for the name) SHALL be computed
- **AND** the cache table SHALL be searched for an entry matching the CRC16 and KV name
- **AND** if found, the cache entry's `addr` SHALL be used to directly read the KV without sector traversal
- **AND** the cache entry's `active` counter SHALL be incremented

#### Scenario: Cache insertion on KV write/find

- **WHEN** a KV is written or found through sector traversal
- **THEN** a new cache entry SHALL be inserted with the name's CRC16, the KV's flash address, and initial `active` count
- **AND** if the cache table is full, the least-active entry (lowest `active` value) SHALL be evicted

#### Scenario: Cache invalidation on KV delete

- **WHEN** a KV is deleted
- **THEN** any cache entry matching the KV's address SHALL be invalidated (CRC16 set to `0xFFFF` as unused)

#### Scenario: Sector cache for empty address tracking

- **WHEN** sector info is read or updated
- **THEN** the sector cache table SHALL track `addr`, `empty_kv`, `remain`, and `status` for currently-using sectors
- **AND** when a KV is written, the sector cache's `empty_kv` and `remain` SHALL be updated accordingly

---

### Requirement: Sector Management and Status Tables

KVDB sector management SHALL use write-once status tables to track sector store and dirty states.

#### Scenario: Sector store status transitions

- **WHEN** a sector is formatted
- **THEN** its store status SHALL transition: `FDB_SECTOR_STORE_UNUSED` → `FDB_SECTOR_STORE_EMPTY` (or direct to `USING` for the first sector)
- **WHEN** a sector becomes the active write target
- **THEN** its store status SHALL transition to `FDB_SECTOR_STORE_USING`
- **WHEN** a sector is filled beyond `FDB_SEC_REMAIN_THRESHOLD`
- **THEN** its store status SHALL transition to `FDB_SECTOR_STORE_FULL`

#### Scenario: Sector dirty status transitions

- **WHEN** a KV is deleted within a sector
- **THEN** the sector's dirty status SHALL transition to `FDB_SECTOR_DIRTY_TRUE`
- **WHEN** GC begins on a dirty sector
- **THEN** its dirty status SHALL transition to `FDB_SECTOR_DIRTY_GC`
- **WHEN** GC completes (sector erased and reformatted)
- **THEN** the dirty status SHALL reset to `FDB_SECTOR_DIRTY_UNUSED`

#### Scenario: Sector combined number for merged sectors

- **WHEN** a KV node exceeds `sec_size - sector_header_size` (large value)
- **THEN** multiple sectors SHALL be combined, with each sector's `combined` field pointing to the next sector in the chain, and the last sector having `SECTOR_NOT_COMBINED`

---

### Requirement: Garbage Collection

The GC algorithm SHALL collect dirty sectors when free sector count drops below threshold, moving live KVs to a new sector and erasing/reformatting the old sector.

#### Scenario: GC trigger on sector full

- **WHEN** a KV write fills the current sector and marks it `FDB_SECTOR_STORE_FULL`
- **THEN** `gc_request` flag SHALL be set to `true`
- **AND** the `gc_collect_by_free_size` function SHALL be called with `free_size = kv_size`

#### Scenario: GC sector selection

- **WHEN** GC is requested with a target `free_size`
- **THEN** the database SHALL count empty sectors (status `FDB_SECTOR_STORE_EMPTY`)
- **AND** if empty sectors < `FDB_GC_EMPTY_SEC_THRESHOLD`, SHALL iterate dirty sectors from oldest, selecting sectors where dirty status is `FDB_SECTOR_DIRTY_TRUE`
- **AND** for each dirty sector, call `do_gc`

#### Scenario: do_gc moving live KVs

- **WHEN** `do_gc` processes a dirty sector
- **THEN** it SHALL mark the sector's dirty status as `FDB_SECTOR_DIRTY_GC`
- **AND** iterate all KVs in the sector
- **AND** for each KV with status `FDB_KV_WRITE` (live): move it to the new empty sector by writing the KV header + name + value at the new sector's empty address
- **AND** after moving all live KVs: if moved bytes exceed `free_size`, stop GC
- **AND** erase the old sector (flash erase, set all bytes to `0xFF`)
- **AND** reformat the old sector as `FDB_SECTOR_STORE_EMPTY`
- **AND** update `oldest_addr` to the next sector if the GC'd sector was the oldest

#### Scenario: GC on combined sectors

- **WHEN** a KV spans multiple combined sectors
- **THEN** GC SHALL iterate through all sectors in the combined chain
- **AND** move the large KV as a single unit to a new combined sector chain

#### Scenario: Post-GC cache update

- **WHEN** a KV is moved during GC
- **THEN** the KV cache SHALL be updated to point to the new address
- **AND** the new sector's cache entry SHALL be updated with the new empty address

---

### Requirement: KV Iterator

The KV iterator SHALL traverse all live KVs in sector order, supporting forward iteration only (as per C implementation).

#### Scenario: Iterator initialization

- **WHEN** `KvDb::iterator_init(itr)` is called
- **THEN** the iterator SHALL be reset: `iterated_cnt = 0`, `iterated_obj_bytes = 0`, `iterated_value_bytes = 0`, `traversed_len = 0`
- **AND** `sector_addr` SHALL be set to `oldest_addr`

#### Scenario: Iterator advance

- **WHEN** `KvDb::iterator_next(itr)` is called
- **THEN** the iterator SHALL scan the current sector for the next live KV (status `FDB_KV_WRITE`, CRC32 valid)
- **AND** if the current sector is exhausted, SHALL advance to the next sector (by `sector_addr += sec_size` with wrap-around)
- **AND** populate `curr_kv` with the found KV's data
- **AND** increment `iterated_cnt`
- **AND** return `true` if a KV was found, `false` if no more KVs exist

#### Scenario: Iterator termination

- **WHEN** all sectors have been traversed without finding a new KV
- **THEN** the iterator SHALL return `false`
- **AND** the iterator SHALL track total `iterated_obj_bytes` and `iterated_value_bytes`

---

### Requirement: String Value Buffer Limit

String get operations (`fdb_kv_get` in C) SHALL handle the `FDB_STR_KV_VALUE_MAX_SIZE` buffer limit.

#### Scenario: String value within buffer limit

- **WHEN** `KvDb::get(key)` returns a value that fits within `FDB_STR_KV_VALUE_MAX_SIZE` (default 128 bytes)
- **THEN** the value SHALL be returned as a `String` (equivalent to the C static buffer)

#### Scenario: String value exceeds buffer limit

- **WHEN** `KvDb::get(key)` encounters a value larger than `FDB_STR_KV_VALUE_MAX_SIZE`
- **THEN** the value SHALL be truncated or an error SHALL be returned (preserve C behavior)
- **AND** blob-mode get SHOULD be used instead for large values

---

### Requirement: Print KV Contents

`KvDb::print()` SHALL produce a human-readable dump of all KVs in the database.

#### Scenario: Print empty database

- **WHEN** `KvDb::print()` is called on an empty database
- **THEN** it SHALL print nothing (or a header with zero KVs)

#### Scenario: Print database with KVs

- **WHEN** `KvDb::print()` is called on a database with KVs
- **THEN** it SHALL iterate all sectors and print each KV's sector number, status, name, and value length (for blobs)
