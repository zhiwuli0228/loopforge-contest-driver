## ADDED Requirements

### Requirement: Project-neutral fixed-category fault injection
系统 SHALL 使用领域中立的 AST/IR 选择方式注入类型不匹配、借用冲突、未解析符号、返回值差异、状态转换差异和边界 off-by-one 六类故障，每类 SHALL 至少执行三次独立的检测、修复和验证。

#### Scenario: Complete the fault matrix
- **WHEN** 修复能力执行合规验证
- **THEN** 每个固定故障类别至少有三组绑定基线哈希和种子的独立记录，且每组包含注入补丁、原始错误、修复补丁、目标验证和完整回归证据

#### Scenario: A repetition cannot be repaired
- **WHEN** 任一故障类别的某次重复在局部循环和最终复修后仍失败
- **THEN** 系统不隐藏或用其他成功重复替代该结果，并在最终报告中明确记录未解决异常

### Requirement: Test and assertion integrity
系统 SHALL 比较修复前后的测试清单、源测试映射、断言结构和断言强度，禁止通过删除测试、减少执行数量、移除断言或将断言改为恒真、自比较、全匹配及更弱条件来获得通过。

#### Scenario: Repair weakens an assertion
- **WHEN** 候选补丁删除断言或把断言改为更弱或真空通过形式
- **THEN** 系统拒绝候选补丁、恢复隔离副本并将完整差异登记为异常

#### Scenario: Test count is preserved
- **WHEN** 候选修复完成目标验证和完整回归
- **THEN** 系统证明测试和有效断言数量未减少且所有源测试映射仍可追溯，才允许提交补丁

### Requirement: Unsafe integrity
系统 SHALL 对候选补丁执行 `unsafe` 差异审计，禁止增加未经逐处必要性说明和既有安全比例门禁验证的 `unsafe`。

#### Scenario: Unexplained unsafe is introduced
- **WHEN** 候选补丁新增 `unsafe` 块、函数或实现但缺少必要性证据
- **THEN** 系统拒绝该补丁并将新增位置及原因记录为异常

### Requirement: Targeted and full regression verification
系统 SHALL 在隔离副本中先运行与诊断直接相关的目标验证，再运行完整锁定回归和适用的差分验证；只有全部通过的候选补丁才能提交。

#### Scenario: Targeted test passes but regression fails
- **WHEN** 候选补丁通过目标验证但完整回归或差分验证失败
- **THEN** 系统不提交补丁，保存两类日志并将失败送入后续局部轮次或最终复修

### Requirement: No target-project customization
系统 SHALL 对提交包中的修复实现、规则、模板、配置和静态 fixture 执行定制审计，并结合运行决策溯源证明不存在任何 FlashDB 名称或变体、领域概念、符号/目录/API/错误码特判、固定业务计数或专用修复内容。

#### Scenario: Static asset contains target-specific knowledge
- **WHEN** 合规扫描在修复实现、静态规则、配置、模板或 fixture 中检测到目标项目专属知识
- **THEN** 系统记录直接不合格异常，禁止相关资产参与执行，并确保该异常出现在最终报告

#### Scenario: Runtime decision is evidence-derived
- **WHEN** 系统为实际诊断选择修复策略和修改范围
- **THEN** 决策记录能够逐项追溯到 Repair IR、源码关系图或本次工具诊断，而不引用内置项目身份或默认 profile

### Requirement: Atomic and non-vacuous integrity report
系统 SHALL 原子发布修复完整性汇总，包含各类别实际执行次数、成功数、deferred 数、最终复修成功数、unresolved 数、拒绝补丁原因和证据路径；零实例、缺失类别或计数不一致 SHALL NOT 被判为通过。

#### Scenario: Report publication encounters an error
- **WHEN** 正常汇总报告生成或替换失败
- **THEN** 系统使用兜底路径发布包含报告异常和已收集异常台账的最小有效报告，而不无报告退出

#### Scenario: Empty evidence cannot pass
- **WHEN** 故障实例总数为零、任一固定类别少于三次或汇总无法对应逐项证据
- **THEN** 系统明确报告完整性门禁未满足，并且不得宣称自愈验证通过
