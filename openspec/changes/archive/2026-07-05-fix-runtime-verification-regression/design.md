## Context

V2 架构的核心数据流是 `tools.py parse-source` → `build_complete_analysis()` → `source-inventory.json`。Subagent（c2r-01-understand）通过 `tools.py` 获取解析数据，后续阶段 `semantic_planning.load_analysis_evidence()` 读取 `analysis-verification.json` 并校验 `verification.passed` 和 `verification.status`。

回退后 `build_complete_analysis()` 的 verification dict 只包含 `checks`/`metrics`/`differences` 等中间数据，漏掉了 `passed` 和 `status` 聚合字段。`failures` 列表（line 376）已正确计算，只是未写入返回 dict。

## Goals / Non-Goals

**Goals:**
- 修复 `build_complete_analysis()` 返回值，使 verification dict 包含 `"passed"` 和 `"status"` 字段
- 零定制数据，不引入任何项目特定名称或硬编码值

**Non-Goals:**
- 不改变 `build_complete_analysis()` 的 checks 逻辑本身
- 不修改 V1 遗留模块（`loopforge_runner.py` 等）
- 不涉及架构变更

## Decisions

### Decision: verification dict 的 `"passed"` 计算方式

**选择:** 直接在 `build_complete_analysis()` 内部计算 `"passed"` 和 `"status"`，基于已有的 `failures` 列表（line 376 已计算）。

```python
# Before (line 377)
verification = {"checks": checks, "metrics": {...}, ...}

# After
verification = {"passed": not failures, "status": "PASSED" if not failures else "BLOCKED_WITH_REPORT",
                "checks": checks, "metrics": {...}, ...}
```

**理由:** `failures` 列表已经包含了所有 checks 中未通过的项。只需从 `not failures` 推导两个聚合字段。这是最小改动——一行变更，不改逻辑。

**替代方案考虑:**
- 在 `source_analysis_verify_gate.py:65` 处补全 → 该位置只在 `evidence_failures` 存在时设置 `False`，缺少 else 分支。且 `semantic_planning.py` 和多个测试直接依赖 `build_complete_analysis` 的返回值，不应让调用方各自补充字段

## Risks / Trade-offs

- **低风险:** 单文件单行变更，不改变 checks 逻辑。已有 81 个通过的测试提供回归保护
- `source_analysis_verify_gate.py:65` 的 `complete_bundle["verification"]["passed"] = False` 在修复后语义不变——它仅在 evidence_failures 存在时覆盖为 False，覆盖后结果正确（`not failures` 本应为 False，但因 parse_failures 才被强制覆盖）
