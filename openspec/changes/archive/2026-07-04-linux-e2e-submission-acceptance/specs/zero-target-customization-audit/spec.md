## ADDED Requirements

### Requirement: Reject target-specific submission assets
系统 MUST 扫描最终提交 manifest 覆盖的实现、脚本、规则、技能、提示词、配置、模板、fixture、测试以及文件和目录名，并拒绝任何 FlashDB 名称或变体、领域概念、符号/API、错误码、专用路径或布局、固定业务计数、黄金输出、专用补丁和项目 profile。

#### Scenario: Direct customization is present
- **WHEN** 提交资产包含目标名称、知识、标识符、预期行为或专用路径等静态定制
- **THEN** 审计报告记录文件、位置、匹配类别和证据摘要，合规状态直接判定为不合格且流程继续生成报告

#### Scenario: Submission assets are target-neutral
- **WHEN** manifest 内全部静态资产仅表达语言、构建系统和证据 schema 等通用规则
- **THEN** 静态审计记录完整扫描清单、规则版本、文件哈希和零未裁决命中

### Requirement: Reject indirect identity-based control flow
系统 SHALL 审计配置来源、默认值、映射表、编码常量和控制流，禁止项目身份或其派生值选择根目录、阶段、生成策略、测试、比较规则、修复策略、门禁或报告结论。

#### Scenario: Encoded or indirect dispatch is found
- **WHEN** 项目身份通过别名、哈希、环境默认值、profile、文件组合或其他间接形式影响行为
- **THEN** 结构审计记录数据流和受影响决策，并判定零定制门禁失败

#### Scenario: Behavior is selected from current-run evidence
- **WHEN** 策略仅依据版本化通用配置和当次输入分析产生的结构、类型、调用、诊断或测试证据选择
- **THEN** 审计将决策标记为项目无关并保留来源链

### Requirement: Trace runtime decisions and tainted target data
系统 MUST 为根定位、阶段选择、生成、测试、差分、修复和最终判定记录运行时决策溯源；目标名称、路径和符号等外部输入数据 MUST 被标记且不得进入控制条件或策略选择。

#### Scenario: Target data appears only as evidence
- **WHEN** 目标字符串仅来自只读输入并作为清单、诊断或报告事实传递
- **THEN** 动态审计允许其作为数据出现，并证明它未影响控制流、配置选择或预期结果

#### Scenario: Target data influences a decision
- **WHEN** 被标记的目标数据到达分支、策略选择、比较规则、补丁模板或验收结论
- **THEN** 系统记录完整来源与汇点，直接判定提交不合格并禁止就绪状态

### Requirement: Validate neutrality with project-neutral tests
系统 MUST 使用不复制目标名称、API、布局、行为或标识符的领域中立 fixture 验证通用路径，并注入直接和间接定制以证明审计能够检出。

#### Scenario: Neutral fixtures exercise all paths
- **WHEN** 运行根定位、生成、验证、修复、降级和报告的中立集成测试
- **THEN** 测试覆盖每类决策来源且不依赖目标项目资产

#### Scenario: Injected customization is detected
- **WHEN** 测试分别注入名称特判、领域规则、符号映射、路径 profile、黄金输出和编码身份分派
- **THEN** 每项注入均使零定制合规门禁失败，同时 runner 正常完成并明确报告命中

### Requirement: Treat any unresolved customization finding as disqualifying
系统 MUST 对零定制审计采取零容忍；任何未裁决命中、扫描范围缺失、审计器异常、决策溯源缺口或定制注入漏检均不得降级为合规通过。

#### Scenario: Audit evidence is complete and clean
- **WHEN** 静态、结构和动态审计均完成，manifest 覆盖完整，所有负向测试被检出且无未裁决命中
- **THEN** 零定制门禁可以通过

#### Scenario: Audit cannot prove neutrality
- **WHEN** 任一审计未执行、证据缺失、范围不完整、命中未裁决或负向测试未检出
- **THEN** 系统在异常台账和最终报告中标记直接淘汰风险，并禁止 `READY_FOR_EVALUATION`
