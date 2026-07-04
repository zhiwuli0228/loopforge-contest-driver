## ADDED Requirements

### Requirement: Publish one canonical evidence denominator
系统 SHALL 发布唯一 canonical evidence manifest，冻结 source test、source assertion、public API、behavior contract 和 semantic invariant 的稳定 ID、来源与集合摘要。

#### Scenario: Downstream stage consumes evidence
- **WHEN** 规划、生成、测试迁移、差分或最终语义审计开始
- **THEN** 该阶段验证 manifest identity 和 digest，并仅引用 manifest 内实体

#### Scenario: A stage derives a different denominator
- **WHEN** 任一阶段缺少实体、增加未声明实体或 ID 集合摘要不同
- **THEN** 系统输出分母差异并阻止成功，而不是只比较数量

### Requirement: Prove semantic coverage by linked execution
每条 source assertion、public API 和 semantic invariant 的覆盖 MUST 引用具体测试断言或差分 comparison ID，以及当前 run 的执行记录。

#### Scenario: Invariant has a semantically linked executed check
- **WHEN** assertion 或 comparison 引用该 invariant ID 且所属测试或向量实际执行通过
- **THEN** invariant 可标记为 covered

#### Scenario: Coverage uses an arbitrary shared assertion
- **WHEN** 多个实体仅因存在首个断言、首个向量或测试文件而被统一标记覆盖
- **THEN** 系统拒绝映射并输出 `BLOCKED_WITH_REPORT`

### Requirement: Reject legacy synthetic success evidence
新验证链 MUST 拒绝缺少独立执行身份、canonical manifest digest 或实际 mutation 记录的旧 schema 成功报告。

#### Scenario: Legacy report claims passed
- **WHEN** 旧报告包含 `PASSED` 但缺少新 schema 的强制执行证据
- **THEN** 系统只将其作为诊断输入并重新验证，不得继承成功状态
