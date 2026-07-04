## ADDED Requirements

### Requirement: Core Database Lifecycle

The Rust crate MUST preserve the init/deinit lifecycle of FlashDB databases. All databases (KVDB and TSDB) SHALL be initialized through `_fdb_init_ex` followed by a type-specific init finisher, and SHALL be deinitialized through `_fdb_deinit`.

#### Scenario: Database initialization creates a valid database handle

- **WHEN** `_fdb_init_ex` is called with a valid name, path, type (`FDB_DB_TYPE_KV` or `FDB_DB_TYPE_TS`), and user data
- **THEN** the function SHALL validate all assertions (non-null db, name, path)
- **AND** if already initialized (`init_ok == true`), return `FdbError::NoErr` immediately
- **AND** store name, type, and user_data on the database handle
- **AND** in file mode: MUST validate that `sec_size` and `max_size` are non-zero; MUST initialize file cache tables with `FAILED_ADDR` and `-1`/`0` (POSIX/LIBC) sentinel values; MUST validate path length
- **AND** in FAL mode (not in scope for initial migration): MUST validate partition existence
- **AND** validate that `sec_size` is a power of 2
- **AND** validate that `max_size` is a multiple of `sec_size`
- **AND** validate that the number of sectors (`max_size / sec_size`) is >= 2

#### Scenario: Database init finisher marks database as ready

- **WHEN** `_fdb_init_finish` is called with `FdbError::NoErr`
- **THEN** the database SHALL set `init_ok = true`
- **AND** on the first successful init, print the FlashDB version banner exactly once (using a static/once guard)

#### Scenario: Database init finisher on failure

- **WHEN** `_fdb_init_finish` is called with a non-zero error
- **AND** `not_formatable` is `false`
- **THEN** an error message SHALL be logged with database type, name, path, and error code
- **AND** `init_ok` SHALL remain `false`

#### Scenario: Database deinitialization closes all resources

- **WHEN** `_fdb_deinit` is called on an initialized database
- **THEN** the function SHALL validate the db pointer is non-null
- **AND** in file mode: iterate over all file cache table entries; close any open file descriptors (>0 for POSIX, !=0 for LIBC)
- **AND** set `init_ok = false`

#### Scenario: Deinitialization of already-deinitialized database is safe

- **WHEN** `_fdb_deinit` is called on a database where `init_ok` is already `false`
- **THEN** the function SHALL return without error and without attempting to close files

---

### Requirement: Database Path Resolution

`_fdb_db_path` SHALL return the storage path string for both file mode and FAL mode databases.

#### Scenario: File mode path resolution

- **WHEN** called on a file-mode database (`file_mode == true`)
- **THEN** return the directory path string from `storage.dir`

#### Scenario: FAL mode path resolution

- **WHEN** called on a FAL-mode database (`file_mode == false`)
- **THEN** return the partition name from `storage.part->name` (not in scope for initial migration)

#### Scenario: Path resolution when mode is not compiled in

- **WHEN** called on a database where the current mode is not compiled in (file mode without `FDB_USING_FILE_MODE`, or FAL mode without `FDB_USING_FAL_MODE`)
- **THEN** return a sentinel (empty string or NULL) indicating the mode is unavailable

---

### Requirement: Core Data Types

The `FdbDb` (base struct), `FdbKvDb`, `FdbTsDb`, `FdbKvIterator`, `FdbTsl`, and `FdbBlob` structs SHALL be translated from their C equivalents in `fdb_def.h` with equivalent field layout and semantics.

#### Scenario: FdbDb base struct

- **WHEN** the `FdbDb` struct is defined in Rust
- **THEN** it SHALL contain: `name: String`, `db_type: FdbDbType`, `sec_size: u32`, `max_size: u32`, `oldest_addr: u32`, `init_ok: bool`, `file_mode: bool`, `not_formatable: bool`, `user_data: Option<Box<dyn Any>>`
- **AND** in file mode: `cur_file_sec: [u32; FDB_FILE_CACHE_TABLE_SIZE]`, file cache entries, `cur_sec: u32`
- **AND** optional lock/unlock callback slots (`Option<Box<dyn Fn(&FdbDb)>>`)

#### Scenario: FdbBlob as an owned type

- **WHEN** the `FdbBlob` struct is defined in Rust
- **THEN** it SHALL contain: `buf: Vec<u8>` (owned buffer), `size: usize`
- **AND** `saved` metadata: `meta_addr: u32`, `addr: u32`, `len: usize`
- **WHEN** `fdb_blob_make` is called with a buffer and length
- **THEN** the blob SHALL reference or copy the buffer and set `size` to the provided length

#### Scenario: FdbKv with owned name

- **WHEN** the `FdbKv` struct is defined in Rust
- **THEN** it SHALL contain: `status: FdbKvStatus`, `crc_is_ok: bool`, `name_len: u8`, `magic: u32`, `len: u32`, `value_len: u32`, `name: String` (owned, max `FDB_KV_NAME_MAX`), `addr_start: u32`, `addr_value: u32`

#### Scenario: FdbTsl for time-series log entries

- **WHEN** the `FdbTsl` struct is defined in Rust
- **THEN** it SHALL contain: `status: FdbTslStatus`, `time: FdbTime`, `log_len: u32`, `addr_index: u32`, `addr_log: u32`

#### Scenario: FdbKvIterator for traversal

- **WHEN** the `FdbKvIterator` struct is defined in Rust
- **THEN** it SHALL contain: `curr_kv: FdbKv`, `iterated_cnt: u32`, `iterated_obj_bytes: usize`, `iterated_value_bytes: usize`, `sector_addr: u32`, `traversed_len: u32`

---

### Requirement: Error Handling

All public APIs SHALL use `Result<T, FdbError>` for fallible operations. The error enum SHALL map 1:1 to the C `fdb_err_t`.

#### Scenario: FdbError enum variants

- **WHEN** the `FdbError` enum is defined
- **THEN** it SHALL contain exactly these variants: `NoErr`, `EraseErr`, `ReadErr`, `WriteErr`, `PartNotFound`, `KvNameErr`, `KvNameExist`, `SavedFull`, `InitFailed`
- **AND** the enum SHALL implement `Debug`, `Clone`, `Copy`, `PartialEq`, `Eq`

#### Scenario: Functions returning error codes in C return Result in Rust

- **WHEN** a C function returns `fdb_err_t` (e.g. `fdb_kv_set`, `fdb_kvdb_init`)
- **THEN** the Rust equivalent SHALL return `Result<(), FdbError>`
- **WHEN** a C function returns a pointer (e.g. `fdb_kv_get` returning `char*`)
- **THEN** the Rust equivalent SHALL return `Option<String>`

---

### Requirement: Control Commands

KVDB and TSDB control functions (`fdb_kvdb_control`, `fdb_tsdb_control`) SHALL be implemented as setter methods on the database structs.

#### Scenario: KVDB control commands

- **WHEN** `KvDb::set_sec_size(size)` is called before initialization
- **THEN** it SHALL set the `sec_size` field (equivalent to `FDB_KVDB_CTRL_SET_SEC_SIZE`)
- **WHEN** `KvDb::set_file_mode(true)` is called
- **THEN** it SHALL set `file_mode = true` (equivalent to `FDB_KVDB_CTRL_SET_FILE_MODE`)
- **WHEN** `KvDb::set_max_size(size)` is called
- **THEN** it SHALL set `max_size` (equivalent to `FDB_KVDB_CTRL_SET_MAX_SIZE`)
- **WHEN** `KvDb::set_not_formatable(true)` is called
- **THEN** it SHALL set `not_formatable = true` (equivalent to `FDB_KVDB_CTRL_SET_NOT_FORMAT`)

#### Scenario: TSDB control commands

- **WHEN** `TsDb::set_sec_size(size)` is called before initialization
- **THEN** it SHALL set `sec_size` (equivalent to `FDB_TSDB_CTRL_SET_SEC_SIZE`)
- **WHEN** `TsDb::set_rollover(true)` is called after initialization
- **THEN** it SHALL set `rollover = true` (equivalent to `FDB_TSDB_CTRL_SET_ROLLOVER`)
- **WHEN** `TsDb::get_last_time()` is called
- **THEN** it SHALL return `last_time` (equivalent to `FDB_TSDB_CTRL_GET_LAST_TIME`)

---

### Requirement: Database Type Enum

The `FdbDbType` enum SHALL distinguish between KV and TS database types.

#### Scenario: Database type discrimination

- **WHEN** `FdbDbType::Kv` is used
- **THEN** it SHALL correspond to C's `FDB_DB_TYPE_KV`
- **WHEN** `FdbDbType::Ts` is used
- **THEN** it SHALL correspond to C's `FDB_DB_TYPE_TS`
