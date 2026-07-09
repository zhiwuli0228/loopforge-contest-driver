# c2r-04: Plan

## Role

Create the implementation task list, batch execution plan, AND test-migration spec. Write phase — produces `tasks.md`, `implement-plan.md`, and `specs/test-migration/spec.md`.

## Context You Receive

- `OPENSPEC_CHANGE` — OpenSpec change name
- `SOURCE_ROOT` — absolute path to C source tree
- `WORK_DIR` — absolute path to work directory
- `OUTPUT_DIR` — absolute path to Rust output project
- `PRIOR_OUTPUTS.design` — absolute path to `design.md`
- `PRIOR_OUTPUTS.specs_dir` — absolute path to `specs/` directory (individual capability specs from batched Phase 3)
- `PRIOR_OUTPUTS.inventory` — absolute path to `source-inventory.json` (includes `test_functions` for test-migration spec)
- `PRIOR_OUTPUTS.capability_map` — (OPTIONAL) absolute path to `01c-capability-map.json`. If provided, use dependency graph and priority ordering from the map. If NOT provided, order tasks by explicit dependencies in the specs.

## SuperPower Rules (this phase only)

- **Allowed tools**: none (pure agent reasoning + file writes)
- **Allowed filesystem**: read `**`, write `openspec/changes/*/tasks.md`, write `openspec/changes/*/implement-plan.md`, write `openspec/changes/*/specs/test-migration/spec.md`
- **Forbidden**: modify source code, modify tools.py, modify profiles

## Steps

### 1. Get OpenSpec Template

```
openspec instructions tasks --change "OPENSPEC_CHANGE" --json
```

### 2. Read Design, Specs, and Capability Map (if available)

Read `design.md` for module mapping and migration approach.
Read every spec file under `specs/` — note that a capability's spec may be split into `spec-part-1.md`, `spec-part-2.md`, etc. Read all parts for each capability and treat them as one logical spec.
Read `source-inventory.json` for `test_functions` list.
If available, read `01c-capability-map.json` for the dependency graph and priority ordering.

### 3. Write Test-Migration Spec

Create `specs/test-migration/spec.md`. This is the binding contract between C tests and Rust tests, consumed by Phase 6 (integration test).

**C Test Inventory**: List every entry from `test_functions` in the source inventory.

**C→Rust Mapping Table**:
```
| C Test Function | C Source File | Rust Test Function | Rust Test File | Status |
|-----------------|---------------|-------------------|----------------|--------|
| test_flashdb_init | tests/test_init.c | test_init | tests/test_init.rs | mapped |
| test_legacy_api | tests/test_legacy.c | — | — | N/A: deprecated API |
```

Every C test function must appear in this table. Status is `mapped` (has a corresponding Phase 5b unit test or Phase 6 integration test) or `N/A` with a reason.

**Additional Test Requirements**: Scenarios not covered by C tests but required for semantic equivalence:
```
REQ-TEST-001: Boundary condition — SHALL test <scenario> with <inputs>
  WHEN <condition> THEN <expected outcome>
```

### 4. Create tasks.md

**If capability map is available**: Organize tasks by capability, in dependency order (P0 first, then P1, then P2). Within each priority level, follow the dependency graph. Each batch = ONE capability = implementation tasks + unit test tasks + verification. Use this EXACT format:

```
# Implementation Tasks

## Batch N: [Capability Name]

关联 capability: [capability-id]
关联 spec: specs/<capability-id>/spec.md
C 源文件: [file list]
Rust 目标文件: [file list]
依赖 batch: [batch-ids or "无"]

### 实现
- [ ] N.1 实现 fn [function_name]([signature]) — REQ-[capability-id]-NNN
- [ ] N.2 实现 fn [function_name]([signature]) — REQ-[capability-id]-NNN

### 单元测试
- [ ] N.T1 #[test] fn [test_name] — 覆盖场景: [scenario description]
- [ ] N.T2 #[test] fn [test_name] — 覆盖场景: [scenario description]

### 验证
- [ ] N.V1 cargo build 通过
- [ ] N.V2 cargo test [test_filter] 通过
```

Every batch MUST have: implementation tasks, unit test tasks, and verification tasks. Never separate implementation and testing into different batches.

**If capability map is NOT available**: Group related tasks under ## numbered headings. Use this format:

```
# Implementation Tasks

## 1. [Phase Name]
- [ ] 1.1 Task description — REQ-<module>-NNN
- [ ] 1.2 Task description — REQ-<module>-NNN

## 2. [Phase Name]
- [ ] 2.1 Task description
```

Tasks should be small enough to complete in one session. Order by dependency.

```
# Implementation Tasks

## Batch N: [Capability Name]

关联 capability: [capability-id]
关联 spec: specs/<capability-id>/spec.md
C 源文件: [file list]
Rust 目标文件: [file list]
依赖 batch: [batch-ids or "无"]

### 实现
- [ ] N.1 实现 fn [function_name]([signature]) — REQ-[capability-id]-NNN
- [ ] N.2 实现 fn [function_name]([signature]) — REQ-[capability-id]-NNN

### 单元测试
- [ ] N.T1 #[test] fn [test_name] — 覆盖场景: [scenario description]
- [ ] N.T2 #[test] fn [test_name] — 覆盖场景: [scenario description]

### 验证
- [ ] N.V1 cargo build 通过
- [ ] N.V2 cargo test [test_filter] 通过
```

Every batch MUST have: implementation tasks, unit test tasks, and verification tasks. Never separate implementation and testing into different batches.

### 5. Create implement-plan.md

**If capability map is available**: Define ONE batch per capability. Each batch MUST include BOTH implementation and unit test details. Batches are ordered by the dependency graph from the capability map.

**File contract**: Each batch's `Rust target files` list SHALL contain at least one `.rs` file path. No file path SHALL appear in more than one batch's `Rust target files` list. The scheduling algorithm (Phase 5) verifies this contract before parallel dispatch — duplicate file entries will force sequential execution.

Use this EXACT format for each batch:

```
### Batch N: [Capability Name]

**Capability**: [capability-id] (Priority: [P0/P1/P2])
**Spec reference**: specs/<capability-id>/spec.md
**C source files**: [explicit file paths]
**Rust target files**: [explicit file paths]
**Dependencies**: [batch-ids this batch depends on, or "None (P0 foundation)"]
**Features**: [Cargo.toml feature flag names, space-separated; for the first P0 batch (scaffold), list ALL feature flags from all batches so the scaffold subagent can pre-declare them]

**Implementation functions**:
1. `fn [name]([sig]) -> [ret]` — C equivalent: `[c_func]` in [file:line]
2. ...

**Data structures**:
| C Struct | Rust Equivalent | Field Mapping |
|----------|----------------|---------------|
| [c_struct] | [rust_struct] | [field: type → field: type] |

**Unit tests** (executed by Phase 5b):
1. `#[test] fn [name]()` — covers test case: [test case #N from spec Test Specification table]
2. ...

**Build command** (Phase 5a): `cargo build --features [feature]`
**Test command** (Phase 5b): `cargo test [test_filter]`
**Completion criteria**:
- [ ] Phase 5a: `cargo build` passes (compile verification)
- [ ] Phase 5b: `cargo test [filter]` — all tests pass
- [ ] Phase 5b: every test case from spec Test Specification table is covered
- [ ] unsafe code: [expected count] lines
```

**Field naming consistency**: The `**Rust target files**` field uses the markdown key `Rust target files`. When referenced in code (parsing, scheduling, subagent prompts), this field is referred to as `rust_target`. The scaffold batch (Phase 5) and orchestrator parse this exact key to extract the file list. Use the same key name consistently across all batch entries.

**If capability map is NOT available**: Define batches by module grouping from the design's module mapping. Each batch covers a C source module and its corresponding Rust module. Order batches by dependency (types/constants → core utilities → features). Include build and test commands per batch.

### 5a. Validate implement-plan.md

Before finalizing `implement-plan.md`, verify:

1. **Every batch declares at least one `Rust target file`**: Each batch entry SHALL have a non-empty `Rust target files` field. If a batch has no target file, reassign it or merge it with another batch.

2. **No file appears in more than one batch's target list**: Scan all `Rust target files` entries. If the same `.rs` file path appears in two or more batches, restructure the plan — split the shared module into capability-specific sub-modules, or assign the shared file to exactly one batch and have other batches depend on it.

3. **The first P0 batch declares all features**: The `**Features**` field in the scaffold batch (lowest batch_id at P0) SHALL list every feature flag referenced in any batch's `**Build command**` (the `--features` argument). This allows the scaffold subagent to pre-declare all `[features]` entries in `Cargo.toml`.

### 6. Define OUTPUT_DIR Layout

Specify the initial Rust project structure:

```
OUTPUT_DIR/
├── Cargo.toml          (Phase 5a scaffold batch)
├── src/
│   ├── lib.rs          (Phase 5a scaffold batch)
│   └── <capability>.rs (Phase 5a per batch)
└── tests/
    ├── <capability>_tests.rs (Phase 5b per batch — unit tests)
    └── integration_tests.rs  (Phase 6 — cross-capability integration tests)
```

## Output

Write three files:
```
openspec/changes/OPENSPEC_CHANGE/tasks.md
openspec/changes/OPENSPEC_CHANGE/implement-plan.md
openspec/changes/OPENSPEC_CHANGE/specs/test-migration/spec.md
```

## Gate

- `PHASE_PASS` — tasks.md and implement-plan.md written, batches are well-defined with implement+test+verify tasks, batch order follows dependencies, test-migration spec has complete C→Rust mapping table
- `PHASE_BLOCKED` — specs insufficient to create a plan (missing modules, empty requirements)
- `PHASE_DEGRADED` — some batches lack test tasks, or dependency order is unclear, or some C test functions lack Rust mapping in test-migration spec
