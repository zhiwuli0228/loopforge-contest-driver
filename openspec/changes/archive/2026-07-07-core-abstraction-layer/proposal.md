## Why

Change 2 已经把一致性校验的执行契约、阶段边界和权限约束固定下来，但后续实现仍缺少一套语言无关的核心数据模型。现在补上 Core 抽象层，才能让 Java 适配器、generic fallback、traceability 和 drift 分析共享同一套结构，而不是把语言细节直接渗入后续流水线。

## What Changes

- 新增语言无关的 Core 抽象模型，覆盖设计对象、实现对象、映射关系、漂移分类、证据引用、严重级别和报告结构。
- 为 Core 模型定义字段边界和职责分层，确保其可以同时支撑设计扫描、实现扫描、traceability 构建和 drift 报告。
- 明确 Core 层禁止出现 Java 专有概念，适配器层必须负责把语言细节转换为统一模型。
- 将现有执行契约与新 Core capability 对齐，确保后续阶段和 runtime 可以引用同一套模型术语。

## Capabilities

### New Capabilities
- `consistency-core-models`: 定义设计对象、实现对象、traceability、drift taxonomy、evidence、severity 和 report 所需的语言无关核心模型契约。

### Modified Capabilities
- `consistency-execution-contracts`: 补充执行契约对 Core 模型产物和模型术语的依赖要求，使阶段与 profile 可以引用稳定的核心对象结构。

## Impact

- 影响 `work/core/` 下的核心模型文件布局与职责切分。
- 影响后续 `work/adapters/`、`work/runtime/`、`work/subagent/` 对设计对象、实现对象、evidence 和 drift finding 的输入输出约定。
- 影响 `openspec/specs/` 中的一致性校验能力定义，需要为 Core 模型新增 capability，并更新执行契约中的依赖关系。
- 不实现语言适配器扫描逻辑，不修改业务源码，也不引入写入业务代码的执行路径。
