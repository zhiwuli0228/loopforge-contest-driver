## ADDED Requirements

### Requirement: File Flash I/O Trait

The `FlashIo` trait SHALL abstract flash read/write/erase operations behind a trait interface, with `FileFlashIo` as the default implementation for FILE_MODE.

#### Scenario: FlashIo trait definition

- **WHEN** the `FlashIo` trait is defined
- **THEN** it SHALL include: `fn read(&self, addr: u32, buf: &mut [u8]) -> Result<(), FdbError>`
- **AND** `fn write(&self, addr: u32, buf: &[u8], sync: bool) -> Result<(), FdbError>`
- **AND** `fn erase(&self, addr: u32, size: usize) -> Result<(), FdbError>`

#### Scenario: FileFlashIo struct

- **WHEN** `FileFlashIo` is created
- **THEN** it SHALL store: `dir: String` (directory path), `sec_size: u32`, `file_cache` (file descriptor cache table of size `FDB_FILE_CACHE_TABLE_SIZE`), `cur_file_sec: [u32; FDB_FILE_CACHE_TABLE_SIZE]`, `cur_sec: u32`

---

### Requirement: File Path Generation

File-based sector files SHALL be named as `<db_name>.fdb.<index>` within the storage directory.

#### Scenario: File path for a sector address

- **WHEN** a sector file path is needed for address `addr` in database `db`
- **THEN** the sector address SHALL be aligned down to `sec_size`: `sec_addr = addr & !(sec_size - 1)`
- **AND** the sector index SHALL be computed as `sec_addr / sec_size`
- **AND** the file name SHALL be formatted as `<db_name_first_8_chars>.fdb.<index>`
- **AND** the full path SHALL be `<dir>/<db_name>.fdb.<index>`
- **AND** if the full path exceeds `DB_PATH_MAX` (256), an assertion SHALL fire

---

### Requirement: POSIX File I/O

When `FDB_USING_FILE_POSIX_MODE` is enabled, the file read/write/erase operations SHALL use POSIX file descriptors (`open`, `read`, `write`, `lseek`, `fsync`, `close`).

#### Scenario: POSIX file open

- **WHEN** `__fdb_file_read`, `_fdb_file_write`, or `_fdb_file_erase` needs a file descriptor for a given sector address
- **THEN** the file descriptor cache SHALL be searched for an entry matching `sec_addr`
- **AND** if found and not requesting clean, the cached fd SHALL be returned
- **AND** if not found: the file SHALL be opened with `open(path, O_RDWR, 0777)`
- **AND** for erase (clean=true): the file SHALL be opened with `open(path, O_RDWR | O_CREAT | O_TRUNC, 0777)` and immediately closed
- **AND** the fd SHALL be inserted into the cache table

#### Scenario: POSIX file read

- **WHEN** `_fdb_file_read(db, addr, buf, size)` is called
- **THEN** the file SHALL be opened/located via cache
- **AND** `addr` SHALL be adjusted to `addr % sec_size` (offset within sector file)
- **AND** `lseek(fd, offset, SEEK_SET)` SHALL seek to the offset
- **AND** `read(fd, buf, size)` SHALL read `size` bytes
- **AND** if any operation fails, return `FdbError::ReadErr`

#### Scenario: POSIX file write

- **WHEN** `_fdb_file_write(db, addr, buf, size, sync)` is called
- **THEN** the file SHALL be opened/located via cache
- **AND** `addr % sec_size` SHALL determine the write offset
- **AND** `lseek` + `write` SHALL write the data
- **AND** if `sync` is true, `fsync(fd)` SHALL be called after the write
- **AND** if any operation fails, return `FdbError::WriteErr`

#### Scenario: POSIX file erase

- **WHEN** `_fdb_file_erase(db, addr, size)` is called
- **THEN** the file SHALL be opened in clean mode (truncate)
- **AND** the file SHALL be filled with `0xFF` bytes (flash-erased state) up to `size` bytes
- **AND** data SHALL be written in `BUF_SIZE` (32-byte) chunks, with the remainder handled separately
- **AND** `fsync(fd)` SHALL be called after writing
- **AND** if any operation fails, return `FdbError::EraseErr`

---

### Requirement: LIBC File I/O (Alternative Mode)

When `FDB_USING_FILE_LIBC_MODE` is enabled (not POSIX), file I/O SHALL use C standard library `FILE*` handles (`fopen`, `fread`, `fwrite`, `fseek`, `fflush`, `fclose`).

#### Scenario: LIBC file open (NOT IN INITIAL SCOPE)

- **WHEN** `FDB_USING_FILE_LIBC_MODE` is active
- **THEN** the same cache pattern applies with `FILE*` instead of `int` fd
- **AND** files SHALL be opened with `fopen(path, "rb+")` for read/write
- **AND** erase opens with `fopen(path, "wb+")` to truncate
- **AND** the cache check SHALL verify `cur_file[i] != 0` (vs `-1` for POSIX)

---

### Requirement: File Descriptor Cache

The file cache SHALL maintain a small LRU-like table of open file descriptors to avoid repeated `open`/`close` calls for the same sector.

#### Scenario: Cache insertion

- **WHEN** a new file descriptor is inserted into the cache
- **THEN** if a free slot exists (`cur_file[i] == -1` for POSIX, `== 0` for LIBC), the fd and sec_addr SHALL be stored there
- **AND** if the cache is full, the oldest entry SHALL be evicted: close its fd, shift all entries right by one, insert the new fd at position 0

#### Scenario: Cache hit

- **WHEN** a file is requested for a sector that is already in the cache
- **THEN** the cached fd SHALL be returned without opening a new file
- **AND** `db->cur_sec` SHALL be updated to the requested `sec_addr`

#### Scenario: Cache eviction on clean/erase

- **WHEN** a clean (truncate) open is requested
- **THEN** if the sector has a cached fd, it SHALL be closed, the cache entry cleared, and the file reopened in truncate mode
- **AND** after truncation, the cache SHALL be updated with the new fd

---

### Requirement: Flash Abstraction Dispatch

`_fdb_flash_read`, `_fdb_flash_write`, and `_fdb_flash_erase` SHALL dispatch to the appropriate backend based on `db->file_mode`.

#### Scenario: File mode dispatch

- **WHEN** `db->file_mode == true`
- **THEN** `_fdb_flash_read` SHALL delegate to `_fdb_file_read`
- **AND** `_fdb_flash_write` SHALL delegate to `_fdb_file_write`
- **AND** `_fdb_flash_erase` SHALL delegate to `_fdb_file_erase`
- **AND** if `FDB_USING_FILE_MODE` is not compiled in, return the corresponding error

#### Scenario: FAL mode dispatch (NOT IN INITIAL SCOPE)

- **WHEN** `db->file_mode == false` and `FDB_USING_FAL_MODE` is compiled in
- **THEN** dispatches to `fal_partition_read/write/erase` (not in scope for initial migration)

#### Scenario: Aligned flash write

- **WHEN** `_fdb_flash_write_align(db, addr, buf, size)` is called
- **THEN** the write SHALL be split into two parts: the aligned portion (write directly) and the unaligned remainder (copy to a `[u8; FDB_WRITE_GRAN/8]` pad buffer filled with `0xFF` and write)
- **AND** this ensures writes on flash that only support write-granularity-aligned operations
