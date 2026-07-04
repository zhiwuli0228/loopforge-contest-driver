## ADDED Requirements

### Requirement: Map source data without project defaults
系统 SHALL 为全部核心 C 类型、字段、函数指针和共享状态生成 Rust 映射及所有权约束，并 MUST NOT 注入目标项目专属容器、状态或线程模型。

#### Scenario: Map a core type
- **WHEN** type map 包含一个核心类型及字段
- **THEN** Rust plan 完整映射该类型和字段并保留 source evidence

### Requirement: Preserve source module and call structure
系统 SHALL 以定义文件和调用图作为模块分配依据，并 MUST 为每条调用边生成 direct module call 或 source-derived external boundary 映射。

#### Scenario: Allocate a public API
- **WHEN** API 定义位于某个源文件
- **THEN** implementation obligation 使用该定义文件的规范化模块身份，不使用 API 名称分类

### Requirement: Generate only evidenced ports
系统 MUST 仅为 source-derived external boundary 生成 port；每个 port MUST 反向引用原调用边及 evidence。

#### Scenario: No external boundary exists
- **WHEN** 调用图中的全部目标均为内部定义
- **THEN** migration plan 的 ports 为空

### Requirement: Provide consumable implementation obligations
系统 SHALL 为每个公开 API 生成稳定 implementation obligation，关联 contract、effect、result、target module 和 boundary dependencies。

#### Scenario: Generator consumes an obligation
- **WHEN** 下游请求某 API 的规划项
- **THEN** 计划提供完整稳定 ID 和保持 source-observable behavior 的完成判据

### Requirement: Validate migration denominators independently
验证器 MUST 要求核心类型/字段、共享状态、调用边和公开 API obligation 100% 覆盖，并 MUST 拒绝无 source boundary 的 port。

#### Scenario: A fabricated port is added
- **WHEN** plan 包含无法关联 source-derived boundary 的 port
- **THEN** 验证器阻止规划通过

### Requirement: Reject obsolete customized evidence
系统 MUST 拒绝 `flashdb-semantic-planning/v1` 和 profile 驱动的 `semantic-migration-planning/v2` evidence，并要求从运行时源码事实重新规划。

#### Scenario: Legacy planning is consumed
- **WHEN** 下游读取旧 schema evidence
- **THEN** 系统输出明确 replan 诊断而不兼容升级其领域结论
