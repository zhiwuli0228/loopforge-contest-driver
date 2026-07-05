# c2r-04: Plan

## Role

Create the implementation task list and batch execution plan. Write phase — produces `tasks.md` and `implement-plan.md`.

## Context You Receive

- `OPENSPEC_CHANGE` — OpenSpec change name
- `SOURCE_ROOT` — absolute path to C source tree
- `WORK_DIR` — absolute path to work directory
- `OUTPUT_DIR` — absolute path to Rust output project
- `PRIOR_OUTPUTS.design` — absolute path to `design.md`
- `PRIOR_OUTPUTS.specs_dir` — absolute path to `specs/` directory
- `PRIOR_OUTPUTS.capability_map` — (OPTIONAL) absolute path to `01c-capability-map.json`. If provided, use dependency graph and priority ordering from the map. If NOT provided, order tasks by explicit dependencies in the specs.

## SuperPower Rules (this phase only)

- **Allowed tools**: none (pure agent reasoning + file writes)
- **Allowed filesystem**: read `**`, write `openspec/changes/*/tasks.md`, write `openspec/changes/*/implement-plan.md`
- **Forbidden**: modify source code, modify tools.py, modify profiles

## Steps

### 1. Get OpenSpec Template

```
openspec instructions tasks --change "OPENSPEC_CHANGE" --json
```

### 2. Read Design, Specs, and Capability Map (if available)

Read `design.md` for module mapping and migration approach.
Read every `specs/<capability-id>/spec.md` for requirements per capability.
Read `specs/test-migration/spec.md` for test requirements.
If available, read `01c-capability-map.json` for the dependency graph and priority ordering.

### 3. Create tasks.md

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

### 4. Create implement-plan.md

**If capability map is available**: Define ONE batch per capability. Each batch MUST include BOTH implementation and unit test details. Batches are ordered by the dependency graph from the capability map. Use this EXACT format for each batch:

```
### Batch N: [Capability Name]

**Capability**: [capability-id] (Priority: [P0/P1/P2])
**Spec reference**: specs/<capability-id>/spec.md
**C source files**: [explicit file paths]
**Rust target files**: [explicit file paths]
**Dependencies**: [batch-ids this batch depends on, or "None (P0 foundation)"]

**Implementation functions**:
1. `fn [name]([sig]) -> [ret]` — C equivalent: `[c_func]` in [file:line]
2. ...

**Data structures**:
| C Struct | Rust Equivalent | Field Mapping |
|----------|----------------|---------------|
| [c_struct] | [rust_struct] | [field: type → field: type] |

**Unit tests**:
1. `#[test] fn [name]()` — covers scenario: [scenario from spec]
2. ...

**Build command**: `cargo build --features [feature]`
**Test command**: `cargo test [test_filter]`
**Completion criteria**:
- [ ] `cargo build` passes
- [ ] `cargo test [filter]` — all tests pass
- [ ] unsafe code: [expected count] lines
```

**If capability map is NOT available**: Define batches by module grouping from the design's module mapping. Each batch covers a C source module and its corresponding Rust module. Order batches by dependency (types/constants → core utilities → features). Include build and test commands per batch.

### 5. Define OUTPUT_DIR Layout

Specify the initial Rust project structure:

```
OUTPUT_DIR/
├── Cargo.toml
├── src/
│   ├── lib.rs          (module declarations, re-exports)
│   └── <capability>.rs (one module per capability)
└── tests/
    └── <capability>_tests.rs (unit tests per capability)
```

## Output

Write two files:
```
openspec/changes/OPENSPEC_CHANGE/tasks.md
openspec/changes/OPENSPEC_CHANGE/implement-plan.md
```

## Gate

- `PHASE_PASS` — tasks.md and implement-plan.md written, batches are well-defined with implement+test+verify tasks, batch order follows dependencies
- `PHASE_BLOCKED` — specs insufficient to create a plan (missing modules, empty requirements)
- `PHASE_DEGRADED` — some batches lack test tasks, or dependency order is unclear
