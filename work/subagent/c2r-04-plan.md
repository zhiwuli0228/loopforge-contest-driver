# c2r-04: Plan

## Role

Create the implementation task list and batch execution plan. Write phase — produces `tasks.md` and `implement-plan.md`.

## Context You Receive

- `OPENSPEC_CHANGE` — OpenSpec change name
- `SOURCE_ROOT` — path to C source tree
- `WORK_DIR` — path to work directory
- `OUTPUT_DIR` — path to Rust output project
- `PRIOR_OUTPUTS.design` — path to `design.md`
- `PRIOR_OUTPUTS.specs_dir` — path to `specs/` directory

## SuperPower Rules (this phase only)

- **Allowed tools**: none (pure agent reasoning + file writes)
- **Allowed filesystem**: read `**`, write `openspec/changes/*/tasks.md`, write `openspec/changes/*/implement-plan.md`
- **Forbidden**: modify source code, modify tools.py, modify profiles

## Steps

### 1. Get OpenSpec Template

```
openspec instructions tasks --change "OPENSPEC_CHANGE" --json
```

### 2. Read Design and Specs

Read `design.md` for module mapping and migration approach.
Read every `specs/<module>/spec.md` for requirements per module.
Read `specs/test-migration/spec.md` for test requirements.

### 3. Create tasks.md

Organize tasks by dependency order. Use checkbox format:

```
# Implementation Tasks

## Phase 5: Implementation
### Batch 1: Core Types and Utilities
- [ ] 5.1.1 Define core types (Status enum, Result type) in src/types.rs
- [ ] 5.1.2 Implement FlashDB struct and new() in src/lib.rs
- [ ] 5.1.3 ...

### Batch 2: KV Store
- [ ] 5.2.1 Implement KvItem struct in src/kv.rs
- [ ] 5.2.2 Implement set() and get() in src/kv.rs
- [ ] 5.2.3 ...

## Phase 6: Tests
### Batch 1: Core Tests
- [ ] 6.1.1 Write test_init in tests/test_init.rs (maps to C: test_flashdb_init)
- [ ] 6.1.2 ...

### Batch 2: KV Tests
- [ ] 6.2.1 Write test_kv_set_get in tests/test_kv.rs (maps to C: test_kv_basic)
- [ ] 6.2.2 ...

## Phase 8: Semantic Audit
- [ ] 8.1 Write invariant tests for reset behavior
- [ ] 8.2 Write invariant tests for error state preservation
- [ ] 8.3 ...
```

Tasks must reference the spec requirement they implement (e.g., `REQ-core-001`).

### 4. Create implement-plan.md

Define batches for Phase 5 (implement) and Phase 6 (test). Each batch must be independently buildable.

```
# Implementation Plan

## Batch Strategy
- Batch size: 5-8 functions per batch
- Each batch produces a compilable increment
- Batches ordered by dependency (types → utilities → core → features)

## Phase 5 Batches

### Batch 5.1: Project Scaffold + Core Types
- Module: src/types.rs, src/lib.rs
- Functions: FlashDB::new(), Status enum, Result type
- C sources: flashdb.h, flashdb.c (type definitions)
- Specs: specs/core/spec.md
- Build check: cargo build --locked

### Batch 5.2: KV Store Module
- Module: src/kv.rs
- Functions: set(), get(), del(), iter()
- C sources: flashdb_kv.c, flashdb_kv.h
- Specs: specs/kv/spec.md
- Build check: cargo build --locked

### Batch 5.3: ...
...

## Phase 6 Batches

### Batch 6.1: Core Tests
- Module: tests/test_core.rs
- C tests covered: test_flashdb_init, test_flashdb_deinit
- Specs: specs/test-migration/spec.md (Batch 1 entries)
- Test check: cargo test --locked

### Batch 6.2: KV Tests
...
```

### 5. Define OUTPUT_DIR Layout

Specify the initial Rust project structure:

```
OUTPUT_DIR/
├── Cargo.toml
├── src/
│   ├── lib.rs          (module declarations, re-exports)
│   ├── types.rs        (Status, Result, core types)
│   ├── core.rs         (FlashDB struct, new, reset)
│   └── kv.rs           (KV operations)
└── tests/
    ├── test_core.rs
    └── test_kv.rs
```

## Output

Write two files:
```
openspec/changes/OPENSPEC_CHANGE/tasks.md
openspec/changes/OPENSPEC_CHANGE/implement-plan.md
```

## Gate

- `PHASE_PASS` — both files written, batches are well-defined, each batch has spec references and build check
- `PHASE_BLOCKED` — specs insufficient to create a plan (missing modules, empty requirements)
- `PHASE_DEGRADED` — plan exists but some batches are underspecified or dependency order is unclear
