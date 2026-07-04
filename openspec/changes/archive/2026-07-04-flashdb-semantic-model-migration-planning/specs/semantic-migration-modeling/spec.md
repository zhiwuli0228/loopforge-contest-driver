## ADDED Requirements

### Requirement: Consume only coherent runtime evidence
系统 MUST 仅消费当次运行中通过完整性门禁、run ID 和 source digest 一致的源码分析证据；系统 MUST NOT 加载仓库内目标项目 profile、固定 revision 或预制领域模型。

#### Scenario: Build from coherent analysis evidence
- **WHEN** 全部分析 evidence 来自同一已验证运行
- **THEN** semantic planning 绑定父 analysis run、source digest 和 input digest

#### Scenario: Bundled project knowledge is present
- **WHEN** runtime 配置或代码要求目标项目专属 profile、capability 表或默认路径
- **THEN** 通用性检查失败且该提交不得通过

### Requirement: Derive project-independent semantic obligations
系统 SHALL 为每个公开 API 建立签名、source result space、source-observable effect 和行为保持义务，并 MUST 为每项结论记录非空 source evidence IDs。

#### Scenario: Model a public API
- **WHEN** public API map 包含一个有声明和定义证据的 API
- **THEN** semantic IR 生成唯一 contract、result obligation、effect obligation 和 transition obligation

#### Scenario: Business meaning is not statically proven
- **WHEN** 源码结构证据不足以证明具体业务语义
- **THEN** 系统生成保持全部源码可观察行为的义务，不猜测 capability、持久化或错误类别

### Requirement: Prohibit domain and name-based inference
系统 MUST NOT 根据项目名、API 名、类型前缀或文件名推断 capability、读写类别、目标模块、错误码或端口，并 MUST NOT 包含目标项目专属常量或 fixture。

#### Scenario: API name resembles a domain operation
- **WHEN** API 名称包含 `set`、`get`、`kv`、`ts`、`gc` 或其他业务字符串
- **THEN** 名称不改变其语义分类或基础设施边界

### Requirement: Derive resources and boundaries from source structure
系统 SHALL 从 global-state map 建立 resource，从 type map 建立类型/函数指针事实，并 SHALL 仅从未解析为内部定义的调用边建立 external boundary。

#### Scenario: Call target is internal
- **WHEN** 调用目标属于项目内部定义集合
- **THEN** 该边规划为 module call，不生成外部 port

#### Scenario: Call target is external
- **WHEN** 调用目标不属于项目内部定义集合
- **THEN** 系统生成关联原调用边 evidence 的 external boundary 和 port obligation

### Requirement: Validate semantic completeness independently
验证器 MUST 独立重算公开 API、类型/字段、共享状态和调用边分母，要求 contract 和 obligation 完整覆盖且所有 source evidence 非空。

#### Scenario: An API is omitted
- **WHEN** semantic IR 删除父分析 evidence 中的任一公开 API
- **THEN** 覆盖检查失败并输出 `BLOCKED_WITH_REPORT`

### Requirement: Produce deterministic coherent evidence
系统 SHALL 原子发布 `semantic-migration-planning/v3` evidence；全部文档 MUST 共享 planning run、parent analysis run、source digest、semantic IR digest 和 input digest。

#### Scenario: Repeat unchanged runtime evidence
- **WHEN** 相同分析输入重复规划
- **THEN** 除运行元数据外，规范化 semantic IR 和 migration plan 完全一致

