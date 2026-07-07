## Why

Change 5 已经把十阶段流水线和子代理交接骨架固定下来，但仓库仍缺少真正把设计扫描、源码扫描、实现抽取、映射、验证和最终报告串起来的 runtime 闭环。现在补上这层执行能力，才能把一致性校验从“阶段定义存在”推进到“默认 analyze-only 模式下可完整跑通并稳定落盘结果”。

## What Changes

- 新增一致性 runtime/report/verification capability，定义设计扫描、源码扫描、实现抽取、traceability 构建、验证执行和报告写入的最小闭环命令与输出契约。
- 为 `work/runtime/` 下的 runtime 模块建立明确边界，要求各工具在默认 `analyze-only` 模式下只写入 `logs/trace/consistency/`、`result/` 等声明产物路径，不修改业务源码。
- 规定最终闭环至少生成 `result/output.md`、`result/issues/00-summary.md`、`logs/trace/final-report.md` 以及对应阶段化中间产物，确保结果、问题摘要和证据链同时可审计。
- 补充验证执行与失败保留语义，要求 runtime 在验证命令不可执行、适配器信息不完整或上游阶段部分失败时仍能记录验证状态、保留可用证据并输出终态报告。
- 更新执行契约，使十阶段流水线与 runtime 命令、最终报告路径、只读默认值和阶段产物命名保持一致。

## Capabilities

### New Capabilities
- `consistency-runtime-reporting`: 定义 analyze-only 一致性校验闭环中的 runtime 命令、产物路径、验证执行和最终报告输出要求。

### Modified Capabilities
- `consistency-execution-contracts`: 补充十阶段执行契约对 runtime 命令入口、最终报告文件、验证状态记录和只读闭环输出的要求。

## Impact

- 影响 `work/runtime/tools.py` 以及 `design_scanner.py`、`code_inventory.py`、`traceability_builder.py`、`drift_classifier.py`、`verification_runner.py`、`report_writer.py` 的职责划分与命令接口。
- 影响 `logs/trace/consistency/`、`logs/trace/final-report.md`、`result/output.md`、`result/issues/00-summary.md` 的生成契约与内容边界。
- 影响 `work/subagent/dic-05` 到 `dic-09` 与 runtime 闭环之间的交接语义，尤其是 traceability、drift、verification 和 finalization 产物的命名对齐。
- 影响 `openspec/specs/` 中的一致性能力定义，需要新增 runtime/reporting capability，并更新 execution contract 对最终输出和只读分析模式的 requirement。
- 不在此变更中开放业务源码修改，也不处理 Change 7 的遗留 C2Rust 资产归档。
