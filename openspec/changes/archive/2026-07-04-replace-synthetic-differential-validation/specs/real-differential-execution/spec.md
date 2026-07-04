## ADDED Requirements

### Requirement: Execute independent C and Rust adapters
系统 MUST 在隔离工作目录中独立启动 C Oracle 和 Rust rewrite adapter，并 SHALL 记录命令、受控环境、输入摘要、退出码、完整日志和结构化观测摘要。

#### Scenario: Both adapters produce valid observations
- **WHEN** 差分向量具有可执行的两侧 adapter、相同输入镜像、种子和故障计划
- **THEN** 系统保存两次独立执行记录并仅比较 schema 有效的规范化观测

#### Scenario: Adapter evidence is absent
- **WHEN** 任一 adapter、命令、日志或结构化观测缺失、陈旧或无法绑定当前 run
- **THEN** 系统输出 `BLOCKED_WITH_REPORT` 且不得合成或复制另一侧观测

### Requirement: Compare contract-linked observations
每个差分比较项 MUST 关联 behavior contract、source assertion 或 semantic invariant，并 MUST 保存两侧独立值、规范化规则和首个差异。

#### Scenario: Independent observations differ
- **WHEN** 两侧任一契约声明的返回、错误、状态、顺序、持久化、恢复或副作用观测不同
- **THEN** 系统记录最小失败向量和关联证据并阻止成功

### Requirement: Execute real mutation campaigns
系统 MUST 在隔离候选副本中实际应用固定 mutation，验证补丁改变目标，再运行关联检测面。

#### Scenario: Mutation is killed by linked evidence
- **WHEN** baseline 通过且 mutation 后关联测试或差分向量失败
- **THEN** 报告记录补丁摘要、命令、失败证据和 killed 状态

#### Scenario: Mutation was not injected or survived
- **WHEN** 工程摘要未改变、没有执行检测面或全部关联检查仍通过
- **THEN** mutation 标记为 survivor 并使最终验证阻塞
