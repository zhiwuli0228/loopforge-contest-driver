## Why

Change 1 已将工程入口和默认配置切换到 `consistency-check`，但实际执行仍缺少统一的 Skill、阶段、权限和 profile 契约。现在建立这些契约，可以让后续 Core、适配器和流水线变更基于稳定的输入输出与安全边界实施，而不是继续依赖口头约定或旧 C2Rust 资产。

## What Changes

- 新增设计与实现一致性校验主 Skill，定义任务输入、阶段职责、文件交接、证据要求和最终结果。
- 新增默认 Java consistency profile，规定 Java 优先、Generic fallback、分析维度和验证命令选择策略。
- 新增 10 阶段 staged execution 定义，明确各阶段的输入、输出、gate 和失败保留行为。
- 新增 superpower guard 契约，限制各阶段的读取范围、写入范围和源码修改权限。
- 统一现有通用 consistency profile 与新专用契约的职责，避免多个默认配置源产生冲突。

## Capabilities

### New Capabilities
- `consistency-execution-contracts`: 定义一致性校验 Skill、默认 Java profile、阶段执行和权限 guard 必须共同满足的运行契约。

### Modified Capabilities

## Impact

- 新增或调整 `work/skills/design-implementation-consistency/` 下的 Skill 与参考文档。
- 新增 `work/profiles/examples/default-java-consistency.yaml`、`work/profiles/superspec/design-implementation-consistency-stages.yaml` 和 `work/profiles/superpower/design-implementation-consistency-guards.yaml`。
- 影响后续 Core、语言适配器和子代理流水线对输入输出路径、阶段名称及权限边界的约定。
- 不实现 Core 数据模型、语言扫描器或 runtime 命令，也不启用业务源码修改。
