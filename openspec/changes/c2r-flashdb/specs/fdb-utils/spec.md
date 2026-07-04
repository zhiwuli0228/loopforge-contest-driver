## ADDED Requirements

### Requirement: CRC32 Computation

`calc_crc32(crc, buf, size)` SHALL compute the 32-bit CRC checksum using the standard CRC32 table algorithm, returning `u32`.

#### Scenario: CRC32 with initial state

- **WHEN** `calc_crc32(0, buf, len)` is called with initial CRC `0`
- **THEN** the function SHALL initialize `crc = 0 ^ !0u32` (i.e. `crc = 0xFFFFFFFF`)
- **AND** iterate over each byte in `buf`
- **AND** for each byte: `crc = crc32_table[(crc ^ byte) & 0xFF] ^ (crc >> 8)`
- **AND** return `crc ^ !0u32` (XOR with `0xFFFFFFFF`)

#### Scenario: CRC32 with accumulated state

- **WHEN** `calc_crc32(existing_crc, buf, len)` is called with a non-zero initial CRC
- **THEN** the function SHALL continue the CRC computation from the given `existing_crc` value
- **AND** XOR `existing_crc` with `0xFFFFFFFF`, process bytes, XOR result with `0xFFFFFFFF`

#### Scenario: CRC32 table is constant

- **WHEN** the CRC32 table is defined in Rust
- **THEN** it SHALL be a `static [u32; 256]` constant containing exactly the 256 values from `fdb_utils.c`
- **AND** the table SHALL be verified against the C source's table for exact match

#### Scenario: Empty buffer CRC32

- **WHEN** `calc_crc32(0, &[], 0)` is called with an empty buffer
- **THEN** the function SHALL return `0` (since `0xFFFFFFFF XOR 0xFFFFFFFF = 0`)

---

### Requirement: Status Table Set

`_fdb_set_status` SHALL encode a status index into a status table byte array using write-once semantics (only writing `0` bits on flash, never `1` bits), supporting all 6 write-granularity variants.

#### Scenario: Status set for FDB_WRITE_GRAN == 1 (bit-level)

- **WHEN** `FDB_WRITE_GRAN` is `1` and `_fdb_set_status(status_table, status_num, status_index)` is called
- **THEN** the status table SHALL first be filled with `0xFF` (all bits erased)
- **AND** if `status_index > 0`: compute `byte_index = (status_index - 1) / 8`
- **AND** if `FDB_BYTE_ERASED == 0xFF`: `status_table[byte_index] &= (0x00FF >> (status_index % 8))` (clear bits from MSB side)
- **AND** if `FDB_BYTE_ERASED == 0x00`: `status_table[byte_index] |= (0x00FF >> (status_index % 8))` (set bits)
- **AND** return the `byte_index` that was modified

#### Scenario: Status set for FDB_WRITE_GRAN == 8/32/64/128/256 (byte-level)

- **WHEN** `FDB_WRITE_GRAN` is >= 8 and set_status is called
- **THEN** the status table SHALL be filled with `FDB_BYTE_ERASED` bytes
- **AND** if `status_index > 0`: `byte_index = (status_index - 1) * (FDB_WRITE_GRAN / 8)`
- **AND** `status_table[byte_index] = FDB_BYTE_WRITTEN` (write the first byte of each write-granularity block)
- **AND** return the `byte_index`

#### Scenario: Status set for index 0 (no write needed)

- **WHEN** `status_index` is `0`
- **THEN** `memset` fills the table with `FDB_BYTE_ERASED`
- **AND** no byte is modified (since `status_index > 0` is false)
- **AND** return `SIZE_MAX` (indicating no flash write is needed)

---

### Requirement: Status Table Get

`_fdb_get_status` SHALL read the current status index from a status table byte array by finding the first zero bit/byte from the end.

#### Scenario: Status get for FDB_WRITE_GRAN == 1 (bit-level)

- **WHEN** `FDB_WRITE_GRAN` is `1` and `_fdb_get_status(status_table, status_num)` is called
- **THEN** the function SHALL iterate status indices from `status_num - 2` down to `0`
- **AND** for each index: check if bit `(0x80 >> (index % 8))` in byte `status_table[index / 8]` is `0`
- **AND** if bit is `0`, the index + 1 SHALL be returned (the first transition point)
- **AND** if no `0` bit is found, return `status_num - 1` (all bits are `1` = unused)

#### Scenario: Status get for FDB_WRITE_GRAN >= 8 (byte-level)

- **WHEN** `FDB_WRITE_GRAN` is >= 8 and `_fdb_get_status(status_table, status_num)` is called
- **THEN** the function SHALL iterate from `status_num - 2` down to `0`
- **AND** for each index: check if byte `status_table[index * FDB_WRITE_GRAN / 8]` equals `FDB_BYTE_WRITTEN`
- **AND** if byte is `FDB_BYTE_WRITTEN`, return `index + 1`
- **AND** if no written byte is found, return `status_num - 1`

#### Scenario: Status get for initial state

- **WHEN** a status table is all `FDB_BYTE_ERASED` (no status written)
- **THEN** `_fdb_get_status` SHALL return `status_num - 1` (which maps to the last status, i.e. UNUSED for the first status)

---

### Requirement: Write Status to Flash

`_fdb_write_status` SHALL atomically set a status index and write the changed byte(s) to flash.

#### Scenario: Write status combines set and flash write

- **WHEN** `_fdb_write_status(db, addr, status_table, status_num, index, sync)` is called
- **THEN** the function SHALL first call `_fdb_set_status(status_table, status_num, index)` to get `byte_index`
- **AND** if `byte_index == SIZE_MAX` (no change needed), return `FDB_NO_ERR` without flash write
- **AND** for `FDB_WRITE_GRAN == 1`: write the single byte `status_table[byte_index]` to `addr + byte_index` via `_fdb_flash_write`
- **AND** for `FDB_WRITE_GRAN >= 8`: write `FDB_WRITE_GRAN / 8` bytes starting at `status_table[byte_index]` to `addr + byte_index`
- **AND** the `sync` parameter SHALL be passed through to `_fdb_flash_write`
- **AND** return the result of the flash write

#### Scenario: Write status for index 0

- **WHEN** `_fdb_write_status` is called with `index = 0`
- **THEN** the flash write SHALL be skipped (since `byte_index == SIZE_MAX`)
- **AND** `FDB_NO_ERR` SHALL be returned

---

### Requirement: Read Status from Flash

`_fdb_read_status` SHALL read a status table from flash and return the current status index.

#### Scenario: Read status from flash

- **WHEN** `_fdb_read_status(db, addr, status_table, total_num)` is called
- **THEN** the function SHALL call `_fdb_flash_read(db, addr, status_table, FDB_STATUS_TABLE_SIZE(total_num))` to fill the status table from flash
- **AND** then call `_fdb_get_status(status_table, total_num)` to decode the status index
- **AND** return the status index

---

### Requirement: Continue 0xFF Address Finder

`_fdb_continue_ff_addr` SHALL find the first continuous `0xFF` region in flash, starting from a given address toward an end address.

#### Scenario: Finding first continuous erased region

- **WHEN** `_fdb_continue_ff_addr(db, start, end)` is called
- **THEN** the function SHALL read flash in 32-byte chunks from `start` toward `end`
- **AND** track `last_data` (initially `FDB_BYTE_WRITTEN`)
- **AND** when transitioning from non-erased to erased (`last_data != 0xFF && buf[i] == 0xFF`): record `addr = start + i`
- **AND** after the scan: if `last_data == 0xFF` (entire region is erased), return `FDB_WG_ALIGN(addr)`
- **AND** if no erased region is found, return `end`

#### Scenario: Entire region is already erased

- **WHEN** the entire region `[start, end)` is `0xFF` (already erased)
- **THEN** the function SHALL return `FDB_WG_ALIGN(start)` (the aligned start of the region)

---

### Requirement: Blob Creation and Reading

`fdb_blob_make` and `fdb_blob_read` SHALL create blob objects and read blob data from flash.

#### Scenario: Blob creation

- **WHEN** `Blob::new(buf, len)` is called
- **THEN** the blob SHALL store the pointer/reference to the buffer and set `size = len`
- **AND** return the blob object

#### Scenario: Blob read from flash

- **WHEN** `Blob::read(db)` is called with `saved` metadata set (addr, len, meta_addr)
- **THEN** the function SHALL cap `read_len` to `min(blob.size, blob.saved.len)`
- **AND** call `_fdb_flash_read(db, blob.saved.addr, blob.buf, read_len)`
- **AND** if the flash read succeeds, return `read_len`
- **AND** if the flash read fails, return `0`

---

### Requirement: Flash Abstraction Dispatch

`_fdb_flash_read`, `_fdb_flash_write`, and `_fdb_flash_erase` SHALL dispatch based on `db->file_mode`.

#### Scenario: File mode dispatch for read

- **WHEN** `db->file_mode` is `true`
- **THEN** `_fdb_flash_read` SHALL call `_fdb_file_read(db, addr, buf, size)`
- **WHEN** `db->file_mode` is `false` (FAL mode, not in initial scope)
- **THEN** the function SHALL dispatch to `fal_partition_read`

#### Scenario: File mode dispatch for write

- **WHEN** `db->file_mode` is `true`
- **THEN** `_fdb_flash_write` SHALL call `_fdb_file_write(db, addr, buf, size, sync)`

#### Scenario: File mode dispatch for erase

- **WHEN** `db->file_mode` is `true`
- **THEN** `_fdb_flash_erase` SHALL call `_fdb_file_erase(db, addr, size)`

#### Scenario: Aligned write for non-aligned boundaries

- **WHEN** `_fdb_flash_write_align(db, addr, buf, size)` is called
- **THEN** the aligned portion (`FDB_WG_ALIGN_DOWN(size)`) SHALL be written directly
- **AND** the unaligned remainder SHALL be copied to a temporary buffer filled with `0xFF`, then written as a full write-granularity block
