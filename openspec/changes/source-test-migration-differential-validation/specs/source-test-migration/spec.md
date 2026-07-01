## ADDED Requirements

### Requirement: Consume only coherent verified test migration inputs
系统 MUST 仅消费通过 Change 1、Change 2 和 Change 3 门禁且运行身份、输入摘要、schema 版本和工程内容摘要一致的源码测试清单、行为契约、语义不变量、Rust 迁移计划和实现映射。

#### Scenario: Load a coherent evidence chain
- **WHEN** 源码分析、语义规划和 Rust 工程生成证据均验证通过且父子 run ID、输入摘要和工程摘要完整一致
- **THEN** 测试迁移运行记录整个证据链身份，并以这些上游证据定义源测试、源断言、语义不变量和 Rust 实现分母

#### Scenario: Receive stale or mixed test inputs
- **WHEN** 任一输入未通过门禁、来自不同运行、摘要不一致或引用不存在的 Rust 实现 ID
- **THEN** 系统输出 `BLOCKED_WITH_REPORT`，且不得生成或发布候选测试成功证据

### Requirement: Build a complete source test map
系统 SHALL 为全部原始 C 测试场景、fixture、步骤和断言生成 `source-test-map.json`；系统 MUST NOT 将无法迁移的测试或断言从覆盖分母中删除。

#### Scenario: Map all source test scenarios
- **WHEN** 上游源码事实包含非空源测试和断言清单
- **THEN** `source-test-map.json` 记录每个源测试 ID、源断言 ID、对应 Rust 测试、差分向量、行为契约和证据位置

#### Scenario: A source assertion cannot be migrated
- **WHEN** 任一源断言无法转换为 Rust 断言、差分比较项或经证据批准的等价覆盖
- **THEN** `source-test-map.json` 保留该断言在分母中，记录阻塞原因，并使总体状态为 `BLOCKED_WITH_REPORT`

#### Scenario: Source tests are empty
- **WHEN** 上游 `source_test_count` 或 `source_assertion_count` 为零
- **THEN** 系统拒绝通过测试迁移门禁，并报告缺失的不可真空通过证据

### Requirement: Generate effective Rust tests from project-neutral test IR
系统 SHALL 通过项目无关测试 IR 生成 Rust 测试，并 MUST 为每个迁移测试记录源测试 ID、行为契约 ID、语义不变量 ID、输入 fixture、断言和期望观测值。

#### Scenario: Generate a migrated Rust test
- **WHEN** 源测试步骤、fixture 和期望结果可由上游证据建模
- **THEN** 系统生成可执行 Rust 测试，且该测试包含至少一个来自源断言、行为契约或语义不变量的有效断言

#### Scenario: Reject project-specific migration logic
- **WHEN** 测试迁移器、测试 IR 生成器或 Rust 测试模板通过项目名、领域名、文件名、符号前缀、固定 API 名称列表或黄金答案选择逻辑
- **THEN** 反定制门禁失败并输出命中位置、控制流依据和 `BLOCKED_WITH_REPORT`

#### Scenario: Run the same migration mechanism on an unrelated project
- **WHEN** 输入是任意满足相同证据 schema 的非 FlashDB C 项目
- **THEN** 系统使用同一测试 IR、映射和生成流程完成结构门禁，不读取任何项目专属 profile 或内置例外

### Requirement: Reject vacuous and weakened assertions
系统 MUST 扫描生成测试并拒绝恒真断言、自比较断言、全匹配断言、空测试、仅检查命令退出码的测试、删除源断言效果的测试以及与语义不变量无关的占位断言。

#### Scenario: Detect a vacuous assertion
- **WHEN** 生成测试包含 `assert!(true)`、`assert_eq!(x, x)`、`assert!(matches!(x, _))` 或等价恒真模式
- **THEN** 断言有效性扫描记录测试名、源码位置和模式，并阻止测试迁移门禁通过

#### Scenario: Detect a weakened migrated assertion
- **WHEN** 源断言要求具体返回值、状态变化或持久化效果，但生成测试只验证函数可调用或命令成功
- **THEN** 系统将该源断言标记为未有效覆盖，并输出 `BLOCKED_WITH_REPORT`

### Requirement: Cover semantic invariants with executed tests
系统 MUST 为每个语义不变量建立到至少一个实际执行测试或差分比较项的映射，并生成 `semantic-invariant-test-map.json`。

#### Scenario: Map all semantic invariants
- **WHEN** 上游语义规划包含非空语义不变量集合
- **THEN** `semantic-invariant-test-map.json` 记录每个不变量的测试、差分向量、断言位置和执行结果

#### Scenario: A semantic invariant has no executed coverage
- **WHEN** 任一语义不变量没有对应实际执行测试、断言或差分比较项
- **THEN** 系统阻止测试迁移门禁通过，并保留该不变量在覆盖分母中

### Requirement: Execute generated tests with locked Cargo dependencies
系统 MUST 对生成 Rust 工程执行 `cargo test --locked -- --nocapture`，并 SHALL 记录工具链、工作目录、命令、退出码、完整日志、实际执行测试数量和测试名称。

#### Scenario: Cargo tests pass with non-empty execution
- **WHEN** 生成测试编译并执行成功，且实际执行测试数量大于零
- **THEN** `cargo-test.log` 和测试报告记录退出码零、测试名称、运行身份和关联证据路径

#### Scenario: Cargo tests fail or execute no tests
- **WHEN** `cargo test --locked -- --nocapture` 返回非零、测试数量为零或日志无法绑定到当前运行
- **THEN** 系统输出 `BLOCKED_WITH_REPORT`，并保留完整日志供后续修复阶段使用
