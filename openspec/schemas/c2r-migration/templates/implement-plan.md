# Implementation Plan

## Overview

[Total batches, overall strategy, dependency chain between batches. Reference the capability map's dependency graph if available, or the design's module mapping.]

**Output**: [OUTPUT_DIR path]
**Capability map**: `logs/trace/c-to-rust/01c-capability-map.json` (if available)
**Design**: `design.md`

---

## Batch Dependency Graph

[Draw the dependency graph as a text diagram or list. Each batch maps to one capability. Order follows the dependency graph: P0 first, then P1, then P2.]

```
Batch 1 (P0: [capability-id])
  ├─► Batch 2 (P1: [capability-id])
  └─► Batch 3 (P1: [capability-id])
       └─► Batch 4 (P2: [capability-id])
```

---

### Batch 1: [Capability Name]

**Capability**: [capability-id] (Priority: [P0/P1/P2])
**Spec reference**: specs/[capability-id]/spec.md
**C source files**: [explicit file paths, comma-separated]
**Rust target files**: [explicit file paths, comma-separated]
**Dependencies**: [batch-ids or "None (P0 foundation)"]

**Implementation functions**:
1. `fn [name]([signature]) -> [return_type]` — C equivalent: `[c_function_name]` in [file:line]
2. `fn [name]([signature]) -> [return_type]` — C equivalent: `[c_function_name]` in [file:line]
[Minimum 1 function per batch. If implementing only types/structs, replace with: "Type definitions only — no functions in this batch"]

**Data structures**:
| C Struct | Rust Equivalent | Field Mapping |
|----------|----------------|---------------|
| `struct [name] { [type] [field]; ... }` | `struct [Name] { [field]: [Type], ... }` | [C field] → [Rust field]: [ownership/type notes] |
[If no data structures in this batch, write: "N/A — this batch contains only functions"]

**Unit tests**:
1. `#[test] fn [name]()` — covers scenario: [scenario name from spec]
2. `#[test] fn [name]()` — covers scenario: [scenario name from spec]
[Minimum 1 test per function. If a function has no test, explain why: "fn [name] has no unit test — [reason]"]

**Build command**: `cargo build --features [feature_name]`
**Test command**: `cargo test [test_filter]`

**Completion criteria**:
- [ ] `cargo build` passes with 0 errors
- [ ] `cargo test [filter]` — all tests pass
- [ ] unsafe code: [expected count] lines (target: 0 for pure safe Rust capabilities)

---

### Batch 2: [Capability Name]
[... same structure as Batch 1 ...]

---

## OUTPUT_DIR Layout

```
OUTPUT_DIR/
├── Cargo.toml
├── src/
│   ├── lib.rs              (module declarations, re-exports)
│   ├── [capability1].rs    ([capability description])
│   └── [capability2].rs    ([capability description])
└── tests/
    ├── [capability1]_tests.rs  (unit tests for capability 1)
    └── [capability2]_tests.rs  (unit tests for capability 2)
```
