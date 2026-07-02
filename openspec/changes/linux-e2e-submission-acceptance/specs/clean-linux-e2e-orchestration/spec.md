## ADDED Requirements

### Requirement: Run in a clean controlled Linux environment
系统 MUST 为每次正式验收创建唯一运行身份和一次性 Linux 工作区，将输入源码以只读方式提供，并从空的输出、日志、结果、临时构建目录开始运行，不得消费仓库内预生成 Rust 文件、陈旧报告或其他运行的可变缓存。

#### Scenario: Start a clean acceptance run
- **WHEN** 正式 Linux E2E 启动
- **THEN** 系统验证所有可写产物目录初始为空，并记录内核、架构、工具链、locale、时区、环境变量、挂载模式和提交摘要到 `linux-environment.json`

#### Scenario: Stale artifact is visible to the run
- **WHEN** 输出目录非空或运行能够读取未声明的预生成源码、报告或跨运行状态
- **THEN** 系统记录隔离异常、排除该证据并禁止输出 `READY_FOR_EVALUATION`，同时继续发布本次运行报告

### Requirement: Resolve project roots without target identity
系统 SHALL 使用同一套通用 C 工程结构证据解析项目根，支持 `SOURCE_ROOT` 直接指向工程或包含工程的上层目录，且不得依赖项目名称、README、领域词、符号前缀、已知路径或固定布局。

#### Scenario: Resolve direct and parent layouts
- **WHEN** 分别以工程根和其上层目录作为 `SOURCE_ROOT`
- **THEN** 解析器依据可审计的通用结构证据定位同一唯一工程，并记录所有候选、评分依据和选择结果

#### Scenario: Source project has no README
- **WHEN** 合法 C 工程不包含 README
- **THEN** 根定位和完整流水线仍按源文件、头文件、构建与测试结构证据执行

#### Scenario: Root resolution is ambiguous
- **WHEN** 没有候选或多个候选无法用通用规则唯一判定
- **THEN** 系统记录根定位异常、不猜测默认项目，并继续执行仍可独立完成的审计与报告阶段

### Requirement: Preserve the complete source tree
系统 MUST 在运行前后比较输入树的相对路径集合、文件内容、权限、文件类型和符号链接目标，任何变化均为合规异常；所有生成、修复、测试和临时文件只能写入声明的可写根。

#### Scenario: Source remains unchanged
- **WHEN** E2E 流程收敛
- **THEN** `source-before.sha256`、`source-after.sha256` 及结构化清单证明输入集合、内容、权限和链接完全一致

#### Scenario: A source attribute changes
- **WHEN** 任一输入文件被新增、删除、改写、改权或链接目标变化
- **THEN** 系统记录具体路径和前后证据、判定源码完整性门禁失败，并继续最终报告发布

### Requirement: Execute the complete evidence pipeline unattended
系统 MUST 无人值守执行源码分析、语义规划、Rust 生成、测试迁移、差分验证、自愈、Cargo 构建测试、unsafe 检查和最终验收；每个阶段 MUST 绑定同一运行身份并声明输入、输出、依赖、超时和可写边界。

#### Scenario: Complete pipeline succeeds
- **WHEN** 所有阶段及硬门禁完成且证据有效
- **THEN** 从空目录生成完整 Rust Cargo 工程及同次运行的全部验收证据

#### Scenario: A stage raises an exception
- **WHEN** 阶段启动、执行、超时、解析或产物校验发生异常
- **THEN** 编排器将异常写入台账并继续所有前置条件仍有效的独立阶段，不以未捕获异常终止流程

### Requirement: Prove repeatability across fresh runs
系统 SHALL 对每种正式输入布局连续执行两次全新运行，并使用项目无关的最小规范化规则比较生成文件、内容哈希、结构化证据、计数和最终状态。

#### Scenario: Consecutive runs are equivalent
- **WHEN** 两次运行从各自空目录完成
- **THEN** 可重复性报告列出全部比较项、允许规范化字段和相同结论，且语义产物与门禁状态一致

#### Scenario: Consecutive runs diverge
- **WHEN** 非白名单字段、生成源码、测试、计数、诊断或状态存在差异
- **THEN** 系统记录最小差异、判定可重复性门禁失败并在最终报告中保留异常
