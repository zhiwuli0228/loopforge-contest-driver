## ADDED Requirements

### Requirement: Consume only coherent verified generation inputs
系统 MUST 仅消费通过 Change 1 和 Change 2 门禁、具有兼容 schema 且运行身份和输入摘要可追溯一致的源码事实、行为契约、状态转换、语义不变量和 Rust 迁移计划。

#### Scenario: Generate from a coherent evidence chain
- **WHEN** 分析与语义规划证据均验证通过且父子 run ID、输入摘要和引用完整一致
- **THEN** 生成运行记录整个证据链身份，并以这些证据定义核心函数、公开 API、模块和调用边分母

#### Scenario: Receive stale or mixed planning evidence
- **WHEN** 任一输入未通过门禁、来自不同运行或摘要与其父证据不一致
- **THEN** 系统输出 `BLOCKED_WITH_REPORT`，且不替换当前已验证 Rust 工程

### Requirement: Generate a complete evidence-driven Rust Cargo project
系统 SHALL 生成真实可用的 Cargo 工程，并 MUST 实现迁移计划中的公共 API、领域状态、持久化逻辑和规划端口边界。系统 MUST NOT 根据项目名、领域词、符号前缀或固定样例选择实现。

#### Scenario: Generate the full project
- **WHEN** 全部生成输入有效且不存在不可迁移核心项目
- **THEN** 输出包含锁定依赖、模块树和具体函数实现的完整 Cargo 工程，每个生成模块均可追溯到迁移计划

#### Scenario: Generate an unrelated project with the same mechanism
- **WHEN** 输入是任意满足相同分析与规划 schema 的 C 项目
- **THEN** 系统仅根据该项目的证据生成模块、类型、端口与函数，不读取任何项目专属 profile 或黄金答案

#### Scenario: A core function cannot be implemented
- **WHEN** 生成器已尝试所有项目无关、证据驱动的通用生成/修复规则后，仍无法根据已验证契约实现任一核心函数或公开 API
- **THEN** 该项目写入 `unsupported-functions.json` 和最终生成报告中的未解决诊断，并阻止工程被标记为生成成功

#### Scenario: A function-level generation issue is encountered before the final phase
- **WHEN** 单个函数、模块边或测试映射在主生成过程中暂时无法生成
- **THEN** 系统 MUST 记录结构化诊断并继续生成其它模块、工程骨架和可验证证据，直到最终统一修复与验证阶段
- **AND** 最终报告 MUST 记录 `final_repair_summary`，包含尝试、已解决、未解决数量以及对应符号列表

#### Scenario: The final repair pass resolves a recorded issue
- **WHEN** 最终阶段的项目无关修复规则可以从源码事实或行为契约证明缺失实现
- **THEN** 系统 SHALL 写入真实 Rust 实现、标记该诊断为已解决，并将该符号纳入实现映射
- **AND** `final_repair_summary.resolved_count` 和 `resolved_symbols` SHALL 反映该修复

### Requirement: Preserve complete implementation and module-edge mappings
系统 MUST 为全部核心 C 函数、公开 API、核心模块和核心调用边建立到实际 Rust 模块、符号和源码位置的映射；核心函数和公开 API 映射率 MUST 为 100%，核心调用边 MUST 直接保留或具有已验证的等价映射。

#### Scenario: Verify a mapped public API
- **WHEN** 公开 API 被生成到 Rust 工程
- **THEN** `implementation-map.json` 记录其稳定 API ID、行为契约、Rust 符号、模块、源码范围、依赖端口和状态效果

#### Scenario: A core call edge is missing
- **WHEN** 上游分母中的核心调用边既不存在对应 Rust 调用边，也没有规划批准的依赖反转或等价实现
- **THEN** `module-edge-map.json` 标记该边未覆盖且总体生成状态为 `BLOCKED_WITH_REPORT`

### Requirement: Reject placeholders and pseudo-implementations
系统 MUST 拒绝 `todo!()`、`unimplemented!()`、作为占位的 panic、空函数、与行为契约不符的恒定返回值以及用未使用输入掩盖有状态逻辑的伪实现，并 SHALL 独立验证映射符号具有具体可达实现。

#### Scenario: Detect an explicit placeholder
- **WHEN** 任一核心实现包含 `todo!()`、`unimplemented!()` 或标记为临时占位的 panic
- **THEN** 占位扫描列出符号和位置并阻止生成门禁通过

#### Scenario: Detect a vacuous state-changing implementation
- **WHEN** 状态修改 API 忽略关键输入或状态并恒定返回成功而未实现契约中的状态效果
- **THEN** 验证器将其判定为伪实现并输出关联契约和缺失效果

### Requirement: Build with locked dependencies
系统 MUST 对候选工程执行 `cargo build --locked`，并 SHALL 记录工具链、工作目录、命令、退出码及完整日志；只有退出码为零时构建门禁才可通过。

#### Scenario: Locked build succeeds
- **WHEN** 候选工程的清单、锁文件和 Rust 源码完整且编译成功
- **THEN** 构建证据记录退出码零，并将该结论与同一生成 run ID 绑定

#### Scenario: Build fails or lock file is stale
- **WHEN** `cargo build --locked` 返回非零或锁文件不能满足清单
- **THEN** 系统保留完整错误日志并输出 `BLOCKED_WITH_REPORT`

### Requirement: Enforce a justified unsafe ratio below ten percent
系统 MUST 使用固定、不可由格式化稀释且分母非零的统计口径证明生成 Rust 工程的 `unsafe` 比例严格小于 0.10，并 MUST 为每处 `unsafe` 记录必要性、安全不变量、封装边界和源码位置。

#### Scenario: Audit limited necessary unsafe code
- **WHEN** 工程包含必要的布局或平台边界 `unsafe`
- **THEN** 审计证据逐处说明其约束，且计算所得比率小于 0.10 时该门禁才可通过

#### Scenario: Unsafe is excessive or unexplained
- **WHEN** 比率大于或等于 0.10、统计分母为空或任一 `unsafe` 缺少必要性说明
- **THEN** 安全门禁失败并列出比例计算和未审计位置

### Requirement: Publish coherent generation evidence atomically
系统 SHALL 原子发布 Rust 工程及 `implementation-map.json`、`unsupported-functions.json`、`module-edge-map.json` 和生成验证报告；这些产物 MUST 共享生成 run ID、输入证据链摘要和工程内容摘要。

#### Scenario: All generation gates pass
- **WHEN** 实现与调用边完整、无不支持项或占位、锁定构建成功且 unsafe 门禁通过
- **THEN** 验证报告记录每项分母、覆盖结果和证据路径，并允许测试迁移阶段消费该工程

#### Scenario: Evidence publication is interrupted
- **WHEN** 任一工程文件、证据文件、schema 或交叉引用校验失败
- **THEN** 系统不发布部分候选结果，并保留上一个完整已验证工程
