# Implementation Tasks

[If a capability map is available, use per-capability batches (format A below). If no capability map, use numbered task groups (format B).]

---

## Format A (with capability map): Per-Capability Batches

## Batch 1: [Capability Name]

关联 capability: [capability-id]
关联 spec: specs/[capability-id]/spec.md
C 源文件: [file1.c, file2.h]
Rust 目标文件: [src/module.rs, tests/module_tests.rs]
依赖 batch: [batch-ids this batch depends on, or "无"]

### 实现

- [ ] 1.1 实现 fn [function_name]([signature]) — REQ-[capability-id]-001
- [ ] 1.2 实现 fn [function_name]([signature]) — REQ-[capability-id]-002
- [ ] 1.3 定义 struct/enum [type_name] — 对应 C: [c_type] in [file:line]

### 单元测试

- [ ] 1.T1 #[test] fn [test_name] — 覆盖场景: [normal path scenario name]
- [ ] 1.T2 #[test] fn [test_name] — 覆盖场景: [error path scenario name]
- [ ] 1.T3 #[test] fn [test_name] — 覆盖场景: [boundary condition scenario name]

### 验证

- [ ] 1.V1 cargo build 通过
- [ ] 1.V2 cargo test [test_filter] 通过

---

## Batch 2: [Capability Name]

关联 capability: [capability-id]
关联 spec: specs/[capability-id]/spec.md
C 源文件: [file1.c, file2.h]
Rust 目标文件: [src/module.rs, tests/module_tests.rs]
依赖 batch: [batch-ids or "无"]

### 实现

- [ ] 2.1 实现 fn [function_name]([signature]) — REQ-[capability-id]-001

### 单元测试

- [ ] 2.T1 #[test] fn [test_name] — 覆盖场景: [scenario name]

### 验证

- [ ] 2.V1 cargo build 通过
- [ ] 2.V2 cargo test [test_filter] 通过

---

## Integration Tests (Phase 6)

关联 spec: specs/test-migration/spec.md
依赖 batch: [all implementation batch ids]

- [ ] INT.1 #[test] fn [integration_test_name] — 覆盖跨能力场景: [scenario description]
- [ ] INT.2 C test coverage verification: [N/M C tests covered]

---

## Format B (without capability map): Numbered Task Groups

[Use this format when no capability map is available. Group tasks by module or phase.]

## 1. Core Types and Utilities
- [ ] 1.1 Define core types (Status enum, Result type) in src/types.rs
- [ ] 1.2 Implement [Module] struct and new() in src/[module].rs
- [ ] 1.3 ...

## 2. [Module Name]
- [ ] 2.1 Implement [function] in src/[module].rs — REQ-[module]-001
- [ ] 2.2 Write tests for [function] in tests/[module]_tests.rs

## 3. Tests
- [ ] 3.1 Write test_[name] in tests/[file].rs (maps to C: test_[c_func])
- [ ] 3.2 ...
