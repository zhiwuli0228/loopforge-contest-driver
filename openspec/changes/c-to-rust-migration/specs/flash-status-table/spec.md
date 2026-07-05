# Spec: Flash Status Table Management

## Capability Overview

This capability implements the multi-state encoding mechanism that enables flash wear-leveling without requiring erase-before-write for state changes. A status table is a byte array where each state transition writes exactly one additional byte to flash, progressively consuming the erased (0xFF) region. The encoding adapts to variable write granularities from 1 bit to 256 bits. This mechanism is used by KVDB and TSDB for all node state transitions (KV create/delete, sector status changes, TSL lifecycle).

## Key Functions

| C Function | C File:Line | Rust Equivalent | Behavior Summary |
|------------|-------------|-----------------|------------------|
| `_fdb_set_status` | `src/fdb_utils.c:91` | `fn fdb_set_status(status_table: &mut [u8], status_num: usize, status_index: usize) -> usize` | Encode a status index into a status table buffer, return byte index written |
| `_fdb_get_status` | `src/fdb_utils.c:126` | `fn fdb_get_status(status_table: &[u8], status_num: usize) -> usize` | Decode the current status index from a status table buffer by scanning for the first written byte |
| `_fdb_write_status` | `src/fdb_utils.c:147` | `fn fdb_write_status(flash: &mut dyn FlashStorage, addr: u32, status_table: &mut [u8], status_num: usize, status_index: usize) -> Result<(), FdbError>` | Set status and persist the updated byte(s) to flash |
| `_fdb_read_status` | `src/fdb_utils.c:173` | `fn fdb_read_status(flash: &dyn FlashStorage, addr: u32, status_table: &mut [u8], total_num: usize) -> Result<usize, FdbError>` | Read a status table from flash and return the current status index |
| `_fdb_continue_ff_addr` | `src/fdb_utils.c:185` | `fn fdb_continue_ff_addr(flash: &dyn FlashStorage, start: u32, end: u32) -> Result<u32, FdbError>` | Scan flash for the last contiguous 0xFF (erased) region to find the true empty address |

## Data Structures

N/A -- Operates on raw `&[u8]`/`&mut [u8]` buffers.

## Requirements

### REQ-flash-status-table-001: fdb_set_status SHALL encode status_index correctly for all write granularities

C source reference: `src/fdb_utils.c:91`

Scenario (normal path):
  GIVEN a 4-byte status table, `status_num=6`, and `status_index=2`, with `FDB_WRITE_GRAN=32`
  WHEN `fdb_set_status(&mut table, 6, 2)` is called
  THEN the first byte at offset `(2-1)*(32/8) = 4` SHALL be set to `FDB_BYTE_WRITTEN`, and the function SHALL return `4`

Scenario (error path):
  GIVEN `status_index=0`
  WHEN `fdb_set_status` is called
  THEN the function SHALL return `usize::MAX` and SHALL NOT modify the status table (status 0 = erased; no write needed)

Scenario (boundary condition):
  GIVEN `FDB_WRITE_GRAN=1` (bit-level encoding) and `status_index=3`
  WHEN `fdb_set_status` is called
  THEN bit `3 % 8` of byte at offset `(3-1)/8 = 0` SHALL be cleared to 0, and the function SHALL return the byte index

### REQ-flash-status-table-002: fdb_get_status SHALL decode the highest reached status index

C source reference: `src/fdb_utils.c:126`

Scenario (normal path):
  GIVEN a status table where status indices 0-2 have been written (first 2 bytes are non-0xFF)
  WHEN `fdb_get_status(&table, 6)` is called
  THEN the function SHALL return `3` (meaning status 3 is the next unused state, i.e., status 2 is current)

Scenario (error path):
  GIVEN a status table that is all 0xFF (erased, never written)
  WHEN `fdb_get_status(&table, 6)` is called
  THEN the function SHALL return `0` (status 0 = UNUSED)

Scenario (boundary condition):
  GIVEN a status table where ALL bytes are written (maximum status reached = `status_num - 1`)
  WHEN `fdb_get_status(&table, 6)` is called
  THEN the function SHALL return `5` (the last valid status)

### REQ-flash-status-table-003: fdb_write_status SHALL persist only the newly written byte to flash

C source reference: `src/fdb_utils.c:147`

Scenario (normal path):
  GIVEN a status table at flash address 0x1000, `status_num=6`, `status_index=2`, `FDB_WRITE_GRAN=32`
  WHEN `fdb_write_status(&mut flash, 0x1000, &mut table, 6, 2)` is called
  THEN exactly 4 bytes (32/8) SHALL be written to flash at address `0x1000 + byte_index`, and the function SHALL return `Ok(())`

Scenario (error path):
  GIVEN a flash write failure occurs during `fdb_write_status`
  WHEN the `FlashStorage::write` call returns an error
  THEN `fdb_write_status` SHALL propagate the error as `Err(FdbError::WriteErr)`

Scenario (boundary condition):
  GIVEN `status_index=0` (meaning no transition needed)
  WHEN `fdb_write_status` is called
  THEN `byte_index == usize::MAX`, the function SHALL return `Ok(())` without any flash write

### REQ-flash-status-table-004: fdb_continue_ff_addr SHALL find the last contiguous erased region

C source reference: `src/fdb_utils.c:185`

Scenario (normal path):
  GIVEN flash data from `0x1000` to `0x1200` where bytes `0x1040-0x1050` are 0xFF and preceding bytes are non-0xFF
  WHEN `fdb_continue_ff_addr(&flash, 0x1000, 0x1200)` is called
  THEN the function SHALL return a write-granularity-aligned address pointing to the start of the 0xFF region

Scenario (error path):
  GIVEN a flash read failure during scanning
  WHEN `FlashStorage::read` returns an error
  THEN the function SHALL propagate the error as `Err(FdbError::ReadErr)`

Scenario (boundary condition):
  GIVEN the entire range `start..end` is all non-0xFF (fully written)
  WHEN `fdb_continue_ff_addr` scans the range
  THEN `last_data` SHALL NOT equal `FDB_BYTE_ERASED` at the final check, and the function SHALL return `end`

## Invariants

- **INV-flash-status-table-001**: Status transitions are monotonic -- `_fdb_set_status` only moves from lower index to higher index; it NEVER decreases the status index.
- **INV-flash-status-table-002**: `fdb_set_status` and `fdb_get_status` SHALL agree on the encoding scheme for every valid `FDB_WRITE_GRAN` value (1, 8, 32, 64, 128, 256).
- **INV-flash-status-table-003**: On any flash I/O failure in `fdb_write_status` or `fdb_read_status`, the status table buffer state SHALL NOT be modified (no partial updates).
- **INV-flash-status-table-004**: A status table of `status_num` states SHALL require exactly `fdb_status_table_size(status_num)` bytes of storage.

## Dependencies

- `foundational-types` -- Uses `FdbError`, `FDB_WRITE_GRAN`, `FDB_BYTE_ERASED`, `FDB_BYTE_WRITTEN` constants and `fdb_status_table_size`, `fdb_wg_align` utility functions.
