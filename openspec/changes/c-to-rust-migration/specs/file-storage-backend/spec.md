# Spec: File-based Storage Backend

## Capability Overview

This capability implements the file-mode storage backend for FlashDB. Each flash sector is stored as a separate file named `<db_name>.fdb.<sector_index>` in a directory specified during init. It supports POSIX-style file I/O and manages an LRU file descriptor cache to reduce open/close overhead. File "erase" is simulated by filling with 0xFF bytes.

## Key Functions

| C Function | C File:Line | Rust Equivalent | Behavior Summary |
|------------|-------------|-----------------|------------------|
| `get_db_file_path` | `src/fdb_file.c:19` | `fn get_db_file_path(dir: &str, name: &str, sec_addr: u32, sec_size: u32) -> String` | Construct the file path `dir/name.fdb.N` for a given flash address |
| `get_file_from_cache` | `src/fdb_file.c:45` | `fn get_file_from_cache(db: &FdbDb, sec_addr: u32) -> Option<usize>` | Look up a cached file handle by sector address |
| `update_file_cache` | `src/fdb_file.c:55` | `fn update_file_cache(db: &mut FdbDb, sec_addr: u32, file: std::fs::File)` | Update the file cache, evicting LRU entry on overflow |
| `open_db_file` | `src/fdb_file.c:86` | `fn open_db_file(db: &mut FdbDb, sec_addr: u32, clean: bool) -> Result<std::fs::File, FdbError>` | Open (or clean + reopen) the database file for a sector |
| `_fdb_file_read` | `src/fdb_file.c:122` | `fn fdb_file_read(db: &mut FdbDb, addr: u32, buf: &mut [u8], size: usize) -> Result<(), FdbError>` | Read data from a file at the given logical flash address |
| `_fdb_file_write` | `src/fdb_file.c:138` | `fn fdb_file_write(db: &mut FdbDb, addr: u32, buf: &[u8], size: usize) -> Result<(), FdbError>` | Write data to a file at the given logical flash address |
| `_fdb_file_erase` | `src/fdb_file.c:157` | `fn fdb_file_erase(db: &mut FdbDb, addr: u32, size: usize) -> Result<(), FdbError>` | "Erase" a file region by filling with 0xFF bytes |

## Data Structures

N/A -- Uses `std::fs::File` from Rust's standard library.

## Requirements

### REQ-file-storage-backend-001: get_db_file_path SHALL construct paths as "dir/name.fdb.N"

C source reference: `src/fdb_file.c:19`

Scenario (normal path):
  GIVEN `dir="/data/testdb"`, `name="mydb"`, `sec_addr=0x2000`, `sec_size=0x1000`
  WHEN `get_db_file_path(dir, name, sec_addr, sec_size)` is called
  THEN the result SHALL be `"/data/testdb/mydb.fdb.2"` (sector index 2 = 0x2000 / 0x1000)

Scenario (error path):
  N/A -- Rust's `String` is heap-allocated; path construction cannot fail due to buffer overflow (unlike C's fixed-size buffer). If `DB_PATH_MAX` (256) is exceeded, the program SHALL panic or the path SHALL be silently truncated.

Scenario (boundary condition):
  GIVEN `sec_addr=0` and `sec_size=4096`
  WHEN path is constructed
  THEN the sector index SHALL be `0` and the filename SHALL be `name.fdb.0`

### REQ-file-storage-backend-002: open_db_file SHALL cache open file handles with LRU eviction

C source reference: `src/fdb_file.c:86`

Scenario (normal path):
  GIVEN a database with `FDB_FILE_CACHE_TABLE_SIZE=2` and no open files
  WHEN `open_db_file(&mut db, 0x1000, false)` is called for sector 1
  THEN the file SHALL be opened (created if not exists), cached in slot 0, and the handle returned

Scenario (error path):
  GIVEN a filesystem error (e.g., permission denied) during `File::open` or `File::create`
  WHEN `open_db_file` is called
  THEN the function SHALL return `Err(FdbError::ReadErr)` or `Err(FdbError::WriteErr)` depending on the operation

Scenario (boundary condition):
  GIVEN a full cache (2/2 slots used) and a request for a new sector
  WHEN `open_db_file` is called
  THEN the LRU entry (oldest by `cur_file_sec` ordering) SHALL be closed, shifted out, and the new file SHALL occupy slot 0

### REQ-file-storage-backend-003: fdb_file_erase SHALL fill the file region with 0xFF bytes

C source reference: `src/fdb_file.c:157`

Scenario (normal path):
  GIVEN a sector file for address 0x1000, sector size 4096
  WHEN `fdb_file_erase(&mut db, 0x1000, 4096)` is called
  THEN the file SHALL be opened, all 4096 bytes SHALL be overwritten with `0xFF`, and the function SHALL return `Ok(())`

Scenario (error path):
  GIVEN a filesystem write error during erase (e.g., disk full)
  WHEN `fdb_file_erase` writes 0xFF bytes
  THEN the function SHALL return `Err(FdbError::EraseErr)`

Scenario (boundary condition):
  GIVEN `size=0` (erasing zero bytes)
  WHEN `fdb_file_erase` is called
  THEN the function SHALL return `Ok(())` without modifying the file

### REQ-file-storage-backend-004: File I/O SHALL use relative addressing within each sector file

C source reference: `src/fdb_file.c:122, 138`

Scenario (normal path):
  GIVEN a flash address `0x2500` with sector size `0x1000` (4096)
  WHEN reading/writing at this address
  THEN the file path SHALL resolve to sector 2 (`0x2500 / 0x1000`), and the file offset SHALL be `0x2500 % 0x1000 = 0x500`

Scenario (error path):
  GIVEN a seek failure within the file
  WHEN `seek(SeekFrom::Start(offset))` returns an error
  THEN the read/write function SHALL return the appropriate error (`FdbError::ReadErr` or `FdbError::WriteErr`)

Scenario (boundary condition):
  GIVEN a read that spans across the sector boundary (`offset + size > sec_size`)
  WHEN `fdb_file_read` is called
  THEN the function SHALL still attempt to read `size` bytes (the underlying file may be larger, or the read may return fewer bytes)

## Invariants

- **INV-file-storage-backend-001**: File operations use relative addressing: `addr % sec_size` is the offset within each sector file.
- **INV-file-storage-backend-002**: The file cache SHALL never exceed `FDB_FILE_CACHE_TABLE_SIZE` (default 2) open file handles simultaneously.
- **INV-file-storage-backend-003**: File paths SHALL follow the pattern `<dir>/<name>.fdb.<sector_index>` with sector_index = `addr / sec_size`.
- **INV-file-storage-backend-004**: On `open_db_file` with `clean=true`, the file SHALL be truncated to `sec_size` bytes and filled with 0xFF before being returned.

## Dependencies

- `foundational-types` -- Uses `FdbDb`, `FdbError`, `FDB_FILE_CACHE_TABLE_SIZE`.
