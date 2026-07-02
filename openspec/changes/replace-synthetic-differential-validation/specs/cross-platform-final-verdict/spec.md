## ADDED Requirements

### Requirement: Compute one authoritative final verdict
runner SHALL 从完整 gate manifest 计算唯一最终状态，所有 Windows/Linux 包装入口 MUST 透传该状态和退出码，不得自行推断 READY。

#### Scenario: Cargo passes but semantic gate fails
- **WHEN** `cargo build` 与 `cargo test` 成功但 semantic、differential、mutation 或 evidence coherence 任一门禁失败
- **THEN** runner 与所有入口均报告 `BLOCKED_WITH_REPORT`

#### Scenario: Every required gate passes
- **WHEN** 完整 gate manifest 的必需门禁均有当前 run 的非真空成功证据
- **THEN** runner 和平台入口一致报告 `READY_FOR_EVALUATION`

### Requirement: Use platform-neutral generation policy
Windows 与 Linux MUST 使用同一显式生成 provider 策略、模型配置、轮次和验证命令；provider 不可用或超时时 MUST fail closed。

#### Scenario: Same configuration runs on both platforms
- **WHEN** 相同输入与提交版本分别在 Windows 和 Linux 执行
- **THEN** 两端采用相同 provider policy，平台差异只记录为环境证据

### Requirement: Prove normalized repeatability and source integrity
系统 MUST 在干净隔离工作区连续执行至少两次，并比较规范化结果，同时验证 SOURCE_ROOT 前后内容、模式和链接摘要不变。

#### Scenario: Consecutive runs are stable
- **WHEN** 相同输入、配置和提交执行两次完整流程
- **THEN** 除允许的时间、绝对路径和平台工具链字段外，实体集合、生成源码摘要、测试集合、观测和最终 verdict 一致

#### Scenario: Output or source is unstable
- **WHEN** 规范化摘要不同或 SOURCE_ROOT 发生任何变化
- **THEN** repeatability 或 source-integrity 门禁失败并阻止 READY
