## ADDED Requirements

### Requirement: Build deterministic C and Rust differential vectors
系统 SHALL 从源测试、行为契约、状态转换和语义不变量生成 `differential-test-vectors.json`；每个向量 MUST 包含相同输入、初始存储状态、随机种子、故障计划、执行步骤和规范化观测定义。

#### Scenario: Generate a vector from source evidence
- **WHEN** 源测试或行为契约描述可执行操作序列和期望观测
- **THEN** 差分向量记录 API 调用、输入数据、初始状态、比较项、关联源测试和行为契约 ID

#### Scenario: Differential vector set is empty
- **WHEN** 无法生成任何差分向量或 `differential_scenario_count` 为零
- **THEN** 系统拒绝通过差分门禁，并输出不可真空通过的阻塞报告

### Requirement: Execute C original and Rust rewrite against the same scenario
系统 MUST 在隔离工作目录中执行 C 原实现 Oracle 和 Rust 重写实现，并确保两侧使用同一输入、初始存储镜像、随机种子、时间控制和故障注入计划。

#### Scenario: Run a deterministic differential scenario
- **WHEN** 差分向量被执行
- **THEN** C 侧和 Rust 侧均记录执行命令、环境摘要、输入摘要、输出观测和退出状态，并绑定到同一向量 ID

#### Scenario: One side cannot execute
- **WHEN** C Oracle 或 Rust 重写任一侧无法构建、启动、执行向量或产生规范化观测
- **THEN** 差分报告记录失败侧、日志路径和阻塞原因，且总体状态为 `BLOCKED_WITH_REPORT`

### Requirement: Compare complete observable behavior
系统 SHALL 比较返回值、错误码或错误类别、KV/TS 可见数据、遍历顺序、容量边界、关闭重开后的持久化状态、中断或损坏后的恢复行为、GC 前后可见状态和契约声明的副作用。

#### Scenario: Observable behavior matches
- **WHEN** C 原实现和 Rust 重写在同一向量上完成执行
- **THEN** `differential-test-report.json` 记录每个比较项的 C 观测、Rust 观测、规范化规则和一致结论

#### Scenario: A comparison differs
- **WHEN** 任一返回值、错误、状态、顺序、持久化或恢复比较项不一致
- **THEN** 差分报告记录最小失败向量、差异路径、两侧观测值和关联行为契约，并输出 `BLOCKED_WITH_REPORT`

### Requirement: Run fixed-seed state machine differential tests
系统 MUST 根据行为契约和状态转换生成固定随机种子的状态机测试，并在 C 原实现和 Rust 重写两侧比较每一步后的规范化观测。

#### Scenario: State machine sequences match
- **WHEN** 固定种子操作序列执行完成
- **THEN** 差分报告记录种子、步骤、每步观测摘要和最终一致状态

#### Scenario: State machine detects divergence
- **WHEN** 任一步操作后的可见状态、错误或后续可执行操作集合出现差异
- **THEN** 系统记录首个分歧步骤、前置状态、操作和两侧观测，并阻止差分门禁通过

### Requirement: Prove test effectiveness with mutation testing
系统 MUST 注入固定关键语义缺陷并生成 `mutation-test-report.json`；测试和差分门禁 MUST 检测这些缺陷，不能在 mutation 存在时仍全部通过。

#### Scenario: Mutations are detected
- **WHEN** 注入错误返回码、删除行为缺失、容量边界 off-by-one、遍历顺序错误、持久化重开丢失或恢复路径忽略损坏等固定缺陷
- **THEN** 至少一个迁移测试、差分向量、状态机测试或语义不变量检查失败，并在 mutation 报告中关联检测证据

#### Scenario: A mutation survives
- **WHEN** 任一固定关键语义 mutation 注入后全部测试和差分验证仍通过
- **THEN** 系统将测试有效性标记为失败，记录幸存 mutation 和缺失检测面，并输出 `BLOCKED_WITH_REPORT`

### Requirement: Reject FlashDB-specific differential customization
系统 MUST 扫描差分 harness、Oracle 适配器、向量生成器、比较器、mutation runner、配置和报告模板，拒绝通过 FlashDB 名称、领域词、源路径、符号前缀、固定 API 列表或黄金输出驱动的控制流。

#### Scenario: Detect project-specific comparator logic
- **WHEN** 比较器对特定项目名、领域名、文件名、符号前缀或硬编码 API 名称采用特殊比较规则
- **THEN** 反定制扫描记录命中位置和分支依据，并阻止差分门禁通过

#### Scenario: Project strings appear only as input evidence
- **WHEN** 项目名称或符号作为只读输入证据、报告数据或日志内容出现，而不影响控制流、配置选择或比较规则
- **THEN** 系统允许该数据出现，并在反定制报告中将其裁决为非控制流引用

### Requirement: Publish coherent differential evidence
系统 SHALL 原子发布 `differential-test-vectors.json`、`differential-test-report.json`、`mutation-test-report.json` 和最终测试验证报告；这些产物 MUST 共享运行身份、输入摘要、工程摘要、测试数量、差分场景数量和阻塞状态。

#### Scenario: All differential gates pass
- **WHEN** 源测试映射完整、Cargo 测试通过、差分一致、状态机一致、mutation 被检测且反定制扫描无未裁决核心命中
- **THEN** 系统发布成功证据，并允许后续自愈阶段消费该验证结果

#### Scenario: Evidence is missing or inconsistent
- **WHEN** 任一报告缺失、schema 无效、路径不存在、运行身份混合、测试数量不一致或状态字段冲突
- **THEN** 系统拒绝成功状态并输出 `BLOCKED_WITH_REPORT`
