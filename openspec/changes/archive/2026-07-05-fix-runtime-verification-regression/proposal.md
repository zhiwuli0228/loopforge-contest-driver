## Why

V2 架构重构后，`source_analysis.py` 的 `build_complete_analysis()` 在回退/恢复过程中丢失了 verification dict 的 `"passed"` 和 `"status"` 聚合字段。该函数是 `tools.py parse-source` 的数据源——V2 agent 流程中 subagent 通过 `tools.py` 获取解析数据，下游 `semantic_planning.load_analysis_evidence()` 要求 `verification.passed === true` 和 `verification.status === "PASSED"`。字段缺失导致整个语义规划→Rust 工程生成→测试验证流水线阻塞（24 个测试 KeyError）。

## What Changes

- `source_analysis.py`: `build_complete_analysis()` 返回的 verification dict 补充 `"passed"` 和 `"status"` 字段，基于已计算的 `failures` 列表推导

## Capabilities

### New Capabilities

None. This is a regression fix — no new capabilities are introduced.

### Modified Capabilities

None. No spec-level behavior changes.

## Impact

- 受影响模块: `source_analysis.py`
- V2 调用链: `tools.py parse-source` → `build_complete_analysis()` → `semantic_planning.load_analysis_evidence()` → `rust_project_generation` → `test_migration_validation`
- 预期修复 24 个因 `KeyError: 'passed'` 失败的测试
- 无 API 变更，无依赖引入
