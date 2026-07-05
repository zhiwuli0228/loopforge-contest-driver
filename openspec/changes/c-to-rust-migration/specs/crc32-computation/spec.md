# Spec: CRC32 Checksum Computation

## Capability Overview

This capability implements standard CRC32 checksum computation using a 256-entry lookup table. It is used by KVDB for data integrity verification on every KV read and write. The CRC32 covers the KV header, name, and value data to detect flash corruption. This is a pure, stateless function with zero external dependencies.

## Key Functions

| C Function | C File:Line | Rust Equivalent | Behavior Summary |
|------------|-------------|-----------------|------------------|
| `fdb_calc_crc32` | `src/fdb_utils.c:77` | `fn fdb_calc_crc32(init_crc: u32, buf: &[u8]) -> u32` | Compute standard zlib/ethernet CRC32 of a buffer with optional accumulated CRC value |

## Data Structures

N/A -- This capability uses only primitives and a static lookup table.

## Requirements

### REQ-crc32-computation-001: fdb_calc_crc32 SHALL produce standard CRC32 output matching the C implementation

C source reference: `src/fdb_utils.c:77`

Scenario (normal path):
  GIVEN a buffer `[0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39]` ("123456789")
  WHEN `fdb_calc_crc32(0, &buf)` is called
  THEN the result SHALL equal `0xCBF43926` (the standard CRC32 checksum for this input)

Scenario (error path):
  N/A -- This is a pure function with no error paths. A NULL buffer in C is undefined behavior; in Rust, an empty `&[u8]` slice is always valid.

Scenario (boundary condition):
  GIVEN an empty buffer `b""` (size=0)
  WHEN `fdb_calc_crc32(0, &buf)` is called
  THEN the loop SHALL be skipped (zero iterations) and the result SHALL equal `0x00000000`

### REQ-crc32-computation-002: CRC32 lookup table SHALL be a compile-time constant with 256 entries

C source reference: `src/fdb_utils.c:21-76`

Scenario (normal path):
  GIVEN the CRC32 table is accessed at any valid index 0-255
  WHEN computing `CRC32_TABLE[(byte ^ crc) & 0xFF]`
  THEN the table lookup SHALL return the correct pre-computed polynomial value

Scenario (error path):
  N/A -- Rust bounds-checks all array accesses. An out-of-bounds index SHALL panic.

Scenario (boundary condition):
  GIVEN index 0 of the CRC32 table
  WHEN checked against the CRC32 polynomial reference
  THEN it SHALL equal `0x00000000`

### REQ-crc32-computation-003: CRC32 SHALL support incremental computation via init_crc parameter

C source reference: `src/fdb_utils.c:77`

Scenario (normal path):
  GIVEN two buffers `b"hello"` and `b" world"`
  WHEN CRC32 is computed incrementally: `c1 = fdb_calc_crc32(0, b"hello")`, then `c2 = fdb_calc_crc32(c1, b" world")`
  THEN `c2` SHALL equal `fdb_calc_crc32(0, b"hello world")`

Scenario (error path):
  N/A -- No error state.

Scenario (boundary condition):
  GIVEN `init_crc` is `0xFFFFFFFF`
  WHEN `fdb_calc_crc32(init_crc, b"test")` is called
  THEN the result SHALL be the same as if the init_crc had been produced by the C implementation from the same prior data

## Invariants

- **INV-crc32-computation-001**: The CRC32 lookup table (`CRC32_TABLE`) SHALL be identical to the C `crc32_table[]` -- a deterministic mapping of 256 u32 values computed from the standard CRC32 polynomial `0xEDB88320`.
- **INV-crc32-computation-002**: `fdb_calc_crc32(x, data)` SHALL be a pure function: same inputs always produce same output; no side effects; no global state access.
- **INV-crc32-computation-003**: The return value is always `accumulated_crc ^ 0xFFFFFFFF` at function exit, matching the C implementation's final XOR.

## Dependencies

None -- This is a standalone P0 capability with no internal code dependencies. It is consumed by `kv-crud` for KV integrity verification.
