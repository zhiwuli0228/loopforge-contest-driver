## Why

Change 2 已经定义了十阶段执行契约，Change 3 和 Change 4 也补上了 Core 模型与语言适配器边界，但仓库仍缺少真正可执行的阶段包和子代理 handoff 资产。现在补上这层流水线封装，才能让一致性校验从“有阶段定义”进入“能按阶段文件交接执行”，并为后续 runtime 闭环提供稳定的编排骨架。

## What Changes

- 新增十阶段流水线子代理 capability，定义 `dic-00` 到 `dic-09` 各阶段包必须具备的输入、输出、gate、失败保留和 handoff 规则。
- 为 `work/subagent/` 下的十个阶段文件建立统一结构，要求每个阶段只消费声明输入、只写入声明输出，并通过 `logs/trace/consistency/` 完成交接。
- 补充主编排器与阶段包之间的边界，明确主流程只传递摘要与文件路径，不直接在主上下文中堆积完整源码或完整中间模型。
- 更新执行契约，使阶段定义文件、guard 和实际阶段包在阶段 ID、产物路径、失败行为和最终 finalize 语义上保持一致。

## Capabilities

### New Capabilities
- `consistency-stage-packages`: 定义设计与实现一致性校验的十阶段子代理包、文件交接和 gate 行为契约。

### Modified Capabilities
- `consistency-execution-contracts`: 将声明式十阶段 contract 绑定到 `work/subagent/dic-00` 到 `dic-09` 的实际阶段包与 handoff 规则。

## Impact

- 影响 `work/subagent/dic-00-preflight.md` 到 `work/subagent/dic-09-finalize.md` 的阶段职责、模板结构和交接格式。
- 影响 `work/skills/design-implementation-consistency/` 中对子代理调用、阶段摘要和最终报告聚合的编排约定。
- 影响 `work/profiles/superspec/design-implementation-consistency-stages.yaml` 与 `work/profiles/superpower/design-implementation-consistency-guards.yaml` 对阶段输出路径和失败保留行为的对齐。
- 为 Change 6 的 runtime / report / verification 闭环提供稳定的阶段化执行骨架，但本变更不实现 runtime 命令本身，也不修改业务源码。
