# c2r-02: Design

## Role

Create the technical design document for the C-to-Rust migration. Write phase — produces `design.md`.

## Context You Receive

- `OPENSPEC_CHANGE` — OpenSpec change name
- `SOURCE_ROOT` — path to C source tree
- `WORK_DIR` — path to work directory
- `PRIOR_OUTPUTS.inventory` — path to `01-source-inventory.json` from Phase 1
- `PRIOR_OUTPUTS.capability_map` — (OPTIONAL) path to `01c-capability-map.json` from Phase 1. If provided, use capability IDs, dependency graph, and priorities from the map. If NOT provided, derive module mapping from the proposal and source inventory.

## SuperPower Rules (this phase only)

- **Allowed tools**: none (pure agent reasoning + file writes)
- **Allowed filesystem**: read `**`, write `openspec/changes/*/design.md`
- **Forbidden**: modify source code, modify tools.py, modify profiles

## Steps

### 1. Get OpenSpec Template

Try to get the design template:

```
openspec instructions design --change "OPENSPEC_CHANGE" --json
```

If this succeeds, note the `template`, `instruction`, and `outputPath` fields. Use them to structure your output.

If openspec is unavailable, create the design document directly at:
```
openspec/changes/OPENSPEC_CHANGE/design.md
```

### 2. Read Source Inventory

Read the source inventory JSON from Phase 1. Understand:
- Module structure (which .c files exist, how they relate)
- Public API surface (which functions are public)
- Type system (structs, enums, typedefs)
- Call graph (who calls whom)
- Global state (what global variables exist)

If `01c-capability-map.json` is available, also read it to understand:
- Which capabilities were identified in the understand phase
- Their priorities (P0/P1/P2) and dependency graph
- Cross-module capabilities that span multiple source files
- Test coverage gaps identified during analysis

### 3. Read Key C Source Files

Read the main .h and .c files to understand:
- API contracts (function signatures, parameter semantics)
- Data structure layouts and relationships
- Error handling patterns (return codes, error states)
- Memory management patterns (allocation, ownership, cleanup)
- I/O and platform boundaries

### 4. Write design.md

The design document must cover:

**Context**: What the C codebase does, its size (N files, M functions), key modules.

**Goals**: What the migration must achieve — complete semantic equivalence, safe Rust preference, < 10% unsafe ratio.

**Non-Goals**: What is explicitly out of scope — performance parity, C ABI compatibility, platform-specific features that don't apply.

**Capability Mapping** (if capability map is available): A table mapping each capability from the understand phase to its implementation plan. Use this EXACT format:

| Capability ID | Name | Priority | C Source Files | Rust Target Module | Key Functions | Dependencies |
|--------------|------|----------|----------------|-------------------|---------------|--------------|
| [from capability map] | [name] | [P0/P1/P2] | [files] | [rust_module] | [function list] | [dependency ids] |

Every capability from `01c-capability-map.json` MUST appear in this table. Do not skip any.

**Module Mapping**: For each C source file/component, state the corresponding Rust module path (always required, regardless of whether capability map is available):
```
C: src/flashdb_core.c  →  Rust: src/core.rs
C: src/flashdb_kv.c    →  Rust: src/kv.rs
```

**Type Mapping**: For each key C type, state the Rust equivalent:
```
C: struct fdb_kv { ... }  →  Rust: struct Kv { ... }
C: typedef enum fdb_status { ... }  →  Rust: enum Status { ... }
```

**Error Strategy**: How C error patterns (return codes, errno) map to Rust (`Result<T, Error>`, custom error enum).

**Memory Strategy**: How C memory patterns (malloc/free, static buffers, arena) map to Rust (ownership, `Vec`, `Box`, arenas).

**Unsafe Strategy**: Which parts must use `unsafe` (FFI, raw pointer manipulation) and why. How to minimize and isolate unsafe blocks.

**Risk/Trade-offs**: Known risks — functions with complex pointer arithmetic, heavy macro use, undefined behavior in C source, conditional compilation challenges.

## Output

Write `design.md` to the OpenSpec change directory:
```
openspec/changes/OPENSPEC_CHANGE/design.md
```

## Gate

- `PHASE_PASS` — design.md written with all required sections (context, goals, module mapping, type mapping, error strategy, memory strategy, unsafe strategy, risks)
- `PHASE_BLOCKED` — inventory empty or unreadable, no C source to analyze
