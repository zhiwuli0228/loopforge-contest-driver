## ADDED Requirements

### Requirement: Evidence-driven project-neutral diagnostics
系统 SHALL 仅将当次运行的编译器、目标测试、完整回归和差分验证证据归一化为 Repair IR，并且 SHALL NOT 通过目标项目名称、领域词、符号前缀、目录、API、错误码、固定计数、profile 或专用模板选择诊断或修复行为。

#### Scenario: Normalize a compiler diagnostic
- **WHEN** 生成 Rust 工程产生包含位置和诊断代码的编译错误
- **THEN** 系统生成绑定运行身份、证据位置、诊断类别和允许修改根的 Repair IR，且决策溯源只引用当次运行证据

#### Scenario: Reject project-specific dispatch
- **WHEN** 修复配置、规则或代码包含按目标项目身份、领域词或符号名称分派的逻辑
- **THEN** 系统将其记录为合规定制异常并禁止该逻辑参与修复，同时继续发布完整异常报告

### Requirement: Bounded minimal repair loop
系统 SHALL 对每个 Repair IR 执行有界的最小修复循环，候选补丁 SHALL 仅修改生成 Rust 工程内与诊断位置或直接图依赖相关的文件和行。

#### Scenario: Commit a verified local repair
- **WHEN** 候选补丁位于允许范围且目标验证和完整回归均通过
- **THEN** 系统原子提交补丁并保存修复任务、补丁、变更行和验证日志

#### Scenario: Reject an unrelated patch
- **WHEN** 候选补丁修改只读输入、提交包规则或诊断图范围外的文件
- **THEN** 系统不提交补丁，将原因和候选差异写入异常台账，并继续后续可执行流程

### Requirement: Non-failing degradation with exception ledger
系统 SHALL 将诊断解析失败、补丁生成失败、补丁冲突、工具启动失败、超时及验证失败转换为结构化异常，而 SHALL NOT 允许单项异常导致顶层编排异常终止或缺失报告。

#### Scenario: Repair cannot be produced
- **WHEN** 在局部轮次上限内无法生成可验证补丁
- **THEN** 系统保留原始诊断和全部尝试，将该项标记为 deferred，并继续执行不依赖该修复的阶段

#### Scenario: Stage raises an unexpected exception
- **WHEN** 任一修复或验证阶段抛出未预期异常
- **THEN** 顶层编排捕获并登记异常，标记受依赖影响的阶段，执行其他独立阶段并最终正常发布报告

### Requirement: One final deferred repair pass
系统 SHALL 在全部编码和验证流程结束后，对所有 deferred 异常统一执行恰好一次最终复修，并允许使用同一运行后续阶段新增的有效证据，但 SHALL NOT 放宽补丁或合规门禁。

#### Scenario: Final retry succeeds
- **WHEN** 后续证据使 deferred 异常能够产生通过全部门禁的补丁
- **THEN** 系统提交补丁，将异常标记为 final-retry-repaired，并记录新增证据和验证结果

#### Scenario: Final retry remains unresolved
- **WHEN** 最终复修仍无法产生通过门禁的补丁
- **THEN** 系统将异常标记为 unresolved，保留完整尝试历史和影响范围，停止继续重试并在最终报告中明确记录

### Requirement: Separate execution completion from compliance result
系统 SHALL 分别报告执行完成状态和合规状态；流程完成并产出报告 SHALL NOT 自动表示修复或合规成功。

#### Scenario: Pipeline completes with unresolved exceptions
- **WHEN** 编排流程已执行完毕但异常台账仍包含 unresolved 项
- **THEN** 系统正常完成报告发布，执行状态为 completed，合规状态明确为未满足，并列出所有未解决异常

### Requirement: Per-attempt repair evidence
系统 SHALL 为每轮故障或实际诊断修复生成可关联的原始诊断、`repair-task.json`、候选补丁、`changed-lines.json`、目标验证日志和完整回归日志，并校验运行身份和内容哈希一致。

#### Scenario: Evidence is incomplete
- **WHEN** 某次修复缺少必需证据、引用陈旧运行或聚合计数与明细不一致
- **THEN** 系统将该次结果记录为证据异常，不将其计为成功，并纳入最终复修或 unresolved 报告
