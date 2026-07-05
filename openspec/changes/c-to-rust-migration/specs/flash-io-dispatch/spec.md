# Spec: Flash I/O Dispatch Layer

## Capability Overview

This capability provides the runtime dispatch layer for flash read, write, and erase operations. It routes I/O requests to the file-mode backend via the `FlashStorage` trait. In the C codebase, it also supports FAL (Flash Abstraction Layer) mode via `#ifdef`; however, FAL mode is deferred in the Rust migration. Additionally, `_fdb_flash_write_align` provides write-granularity-aligned writes with 0xFF padding to ensure flash write constraints are met.

## Key Functions

| C Function | C File:Line | Rust Equivalent | Behavior Summary |
|------------|-------------|-----------------|------------------|
| `_fdb_flash_read` | `src/fdb_utils.c:257` | `fn fdb_flash_read(flash: &dyn FlashStorage, addr: u32, buf: &mut [u8], size: usize) -> Result<(), FdbError>` | Read `size` bytes from flash at `addr` through the storage backend |
| `_fdb_flash_erase` | `src/fdb_utils.c:278` | `fn fdb_flash_erase(flash: &mut dyn FlashStorage, addr: u32, size: usize) -> Result<(), FdbError>` | Erase `size` bytes of flash starting at `addr` (fill with 0xFF) |
| `_fdb_flash_write` | `src/fdb_utils.c:299` | `fn fdb_flash_write(flash: &mut dyn FlashStorage, addr: u32, buf: &[u8], size: usize) -> Result<(), FdbError>` | Write `size` bytes from `buf` to flash at `addr` |
| `_fdb_flash_write_align` | `src/fdb_utils.c:322` | `fn fdb_flash_write_align(flash: &mut dyn FlashStorage, addr: u32, buf: &[u8], size: usize) -> Result<(), FdbError>` | Write data aligned to `FDB_WRITE_GRAN` boundary, padding with 0xFF |

## Data Structures

N/A -- Pure dispatch functions operating on the `FlashStorage` trait object.

## Requirements

### REQ-flash-io-dispatch-001: fdb_flash_read SHALL delegate to FlashStorage::read

C source reference: `src/fdb_utils.c:257`

Scenario (normal path):
  GIVEN a `FlashStorage` implementation (e.g., `RamFlash`) and valid address/size parameters
  WHEN `fdb_flash_read(&flash, 0x100, &mut buf, 16)` is called
  THEN the function SHALL return `Ok(())` and `buf` SHALL contain the 16 bytes from flash address 0x100

Scenario (error path):
  GIVEN a flash storage backend that returns an error on read (e.g., address out of range)
  WHEN `fdb_flash_read` is called
  THEN the function SHALL propagate the error as `Err(FdbError::ReadErr)`

Scenario (boundary condition):
  GIVEN `size=0` (reading zero bytes)
  WHEN `fdb_flash_read(&flash, 0x100, &mut buf, 0)` is called
  THEN the function SHALL return `Ok(())` without any actual I/O (implementation-dependent: may be a no-op or a read of 0 bytes)

### REQ-flash-io-dispatch-002: fdb_flash_erase SHALL delegate to FlashStorage::erase

C source reference: `src/fdb_utils.c:278`

Scenario (normal path):
  GIVEN a `FlashStorage` implementation and a valid sector range
  WHEN `fdb_flash_erase(&mut flash, 0x0, 4096)` is called
  THEN the function SHALL erase the 4096-byte region (fill with 0xFF) and return `Ok(())`

Scenario (error path):
  GIVEN a flash storage backend that returns an error on erase
  WHEN `fdb_flash_erase` is called
  THEN the function SHALL propagate the error as `Err(FdbError::EraseErr)`

Scenario (boundary condition):
  GIVEN `size=0` (erasing zero bytes)
  WHEN `fdb_flash_erase(&mut flash, 0x100, 0)` is called
  THEN the function SHALL return `Ok(())` as a no-op (or propagate implementation-defined behavior)

### REQ-flash-io-dispatch-003: fdb_flash_write SHALL delegate to FlashStorage::write

C source reference: `src/fdb_utils.c:299`

Scenario (normal path):
  GIVEN data `[0xAA, 0xBB, 0xCC]` and a `FlashStorage` backend
  WHEN `fdb_flash_write(&mut flash, 0x200, &[0xAA, 0xBB, 0xCC], 3)` is called
  THEN the function SHALL write 3 bytes to flash at address 0x200 and return `Ok(())`

Scenario (error path):
  GIVEN a flash storage backend that returns an error on write (e.g., write to non-erased region)
  WHEN `fdb_flash_write` is called
  THEN the function SHALL propagate the error as `Err(FdbError::WriteErr)`

Scenario (boundary condition):
  GIVEN `size=0` (writing zero bytes)
  WHEN `fdb_flash_write(&mut flash, 0x100, &[], 0)` is called
  THEN the function SHALL return `Ok(())` without any actual I/O

### REQ-flash-io-dispatch-004: fdb_flash_write_align SHALL pad to FDB_WRITE_GRAN with 0xFF

C source reference: `src/fdb_utils.c:322`

Scenario (normal path):
  GIVEN data `[0xAA, 0xBB, 0xCC]` (3 bytes) and `FDB_WRITE_GRAN=32` (4-byte alignment)
  WHEN `fdb_flash_write_align(&mut flash, 0x100, &data, 3)` is called
  THEN `align_size` SHALL be `4`, the written buffer SHALL be `[0xAA, 0xBB, 0xCC, 0xFF]`, and the function SHALL return `Ok(())`

Scenario (error path):
  GIVEN a flash write failure during `fdb_flash_write_align`
  WHEN `FlashStorage::write` returns an error
  THEN the function SHALL propagate the error

Scenario (boundary condition):
  GIVEN data that is already `FDB_WRITE_GRAN`-aligned (size is a multiple of `FDB_WRITE_GRAN/8`)
  WHEN `fdb_flash_write_align` is called
  THEN `align_size == size` and no extra padding byte SHALL be appended

## Invariants

- **INV-flash-io-dispatch-001**: In the Rust migration, only file mode is supported. The `FlashStorage` trait provides the backend. FAL mode is deferred -- accessing FAL-specific paths SHALL be a compile error or panic.
- **INV-flash-io-dispatch-002**: `fdb_flash_write_align` SHALL always write exactly `fdb_wg_align(size)` bytes, with trailing bytes set to `FDB_BYTE_ERASED` (0xFF).
- **INV-flash-io-dispatch-003**: All flash I/O functions SHALL return `Result<_, FdbError>` -- no panics on I/O errors.

## Dependencies

- `foundational-types` -- Uses `FdbError`, `FDB_WRITE_GRAN`, `FDB_BYTE_ERASED`, `fdb_wg_align`.
- `file-storage-backend` -- In file mode, dispatch routes to file I/O functions (through `FlashStorage` trait).
