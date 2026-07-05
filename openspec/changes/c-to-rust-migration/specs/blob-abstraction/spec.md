# Spec: Blob Data Abstraction

## Capability Overview

This capability provides a thin wrapper bundling a buffer pointer, buffer size, and flash-saved metadata (address, length). It supports `fdb_blob_make` to create blob objects from application data and `fdb_blob_read` to read previously stored blob data from flash using saved address metadata. Blobs are the primary data container for KV values and TSL log entries.

## Key Functions

| C Function | C File:Line | Rust Equivalent | Behavior Summary |
|------------|-------------|-----------------|------------------|
| `fdb_blob_make` | `src/fdb_utils.c:221` | `fn fdb_blob_make(buf: Vec<u8>) -> FdbBlob` | Create a blob from a buffer, setting size and taking ownership of the data |
| `fdb_blob_read` | `src/fdb_utils.c:237` | `fn fdb_blob_read(blob: &mut FdbBlob, flash: &dyn FlashStorage) -> usize` | Read blob data from flash using `saved_addr`/`saved_len`, return bytes read |

## Data Structures

| C Struct | Fields | Rust Equivalent | Notes |
|----------|--------|----------------|-------|
| `fdb_blob` | `buf` (void*), `size`, `saved.meta_addr`, `saved.addr`, `saved.len` | `FdbBlob { buf: Vec<u8>, size: usize, saved_meta_addr: u32, saved_addr: u32, saved_len: usize }` | C `void*` buffer replaced by owned `Vec<u8>` for memory safety |

## Requirements

### REQ-blob-abstraction-001: fdb_blob_make SHALL create a blob that owns its buffer

C source reference: `src/fdb_utils.c:221`

Scenario (normal path):
  GIVEN a buffer `vec![0x01u8, 0x02, 0x03, 0x04, 0x05]` (5 bytes)
  WHEN `fdb_blob_make(buf)` is called
  THEN the returned `FdbBlob` SHALL have `size=5`, `buf==[0x01,0x02,0x03,0x04,0x05]`, and all `saved_*` fields SHALL be 0 (default)

Scenario (error path):
  N/A -- `fdb_blob_make` cannot fail; it only wraps a buffer. In C, a NULL buffer is undefined behavior; in Rust, `Vec<u8>` is always valid.

Scenario (boundary condition):
  GIVEN an empty buffer `vec![]` (size=0)
  WHEN `fdb_blob_make(buf)` is called
  THEN `blob.size` SHALL equal `0` and `blob.buf` SHALL be empty

### REQ-blob-abstraction-002: fdb_blob_read SHALL read at most min(blob.size, blob.saved_len) bytes from flash

C source reference: `src/fdb_utils.c:237`

Scenario (normal path):
  GIVEN a blob with `size=10`, `saved_len=8`, `saved_addr=0x1000`, and flash containing `[0xAA; 8]` at that address
  WHEN `fdb_blob_read(&mut blob, &flash)` is called
  THEN the function SHALL read 8 bytes from flash into `blob.buf[0..8]` and return `8`

Scenario (error path):
  GIVEN a flash read failure during `fdb_blob_read`
  WHEN `FlashStorage::read` returns an error
  THEN the function SHALL return `0` (no bytes read) and the blob buffer SHALL NOT be modified

Scenario (boundary condition):
  GIVEN `blob.size=0` or `blob.saved_len=0`
  WHEN `fdb_blob_read` is called
  THEN `read_len` SHALL be `0`, the flash read SHALL be skipped entirely, and the function SHALL return `0`

### REQ-blob-abstraction-003: Blob saved fields SHALL be populated by KV/TSL read operations before fdb_blob_read

C source reference: `src/fdb_utils.c:237`

Scenario (normal path):
  GIVEN a KV has been found on flash via `fdb_kv_get_obj`
  WHEN the KV's value address and length are stored in `blob.saved_addr` and `blob.saved_len`
  THEN `fdb_blob_read` SHALL read exactly `blob.saved_len` bytes from `blob.saved_addr`

Scenario (error path):
  GIVEN `blob.saved_addr` is uninitialized (0), pointing to flash address 0
  WHEN `fdb_blob_read` is called with `saved_len > 0`
  THEN the function SHALL attempt to read from address 0 (caller responsibility to ensure saved fields are valid)

Scenario (boundary condition):
  GIVEN `blob.size < blob.saved_len` (buffer smaller than stored data)
  WHEN `fdb_blob_read` is called
  THEN only `blob.size` bytes SHALL be read (truncation), preventing buffer overflow

## Invariants

- **INV-blob-abstraction-001**: `blob.buf.len()` SHALL always equal `blob.size` -- the buffer capacity is exactly the declared size.
- **INV-blob-abstraction-002**: `fdb_blob_read` SHALL NEVER read more than `min(blob.size, blob.saved_len)` bytes; this prevents buffer overflow.
- **INV-blob-abstraction-003**: On successful `fdb_blob_read`, the first `read_len` bytes of `blob.buf` SHALL contain the flash data; bytes beyond `read_len` SHALL be unchanged.

## Dependencies

- `foundational-types` -- Uses `FdbBlob` struct definition and `FdbError`.
- `flash-io-dispatch` -- `fdb_blob_read` depends on `_fdb_flash_read` (through `FlashStorage` trait) for flash I/O.
