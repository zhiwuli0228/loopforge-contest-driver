## ADDED Requirements

### Requirement: Convert all stage failures into structured exceptions
系统 MUST 将命令启动、超时、非零退出、解析、校验、修复、文件和报告异常规范化为 append-only 异常台账项，包含运行身份、阶段、根因类别、影响、依赖关系、尝试次数和证据路径；任何子阶段异常不得逃逸并终止顶层协议。

#### Scenario: Recoverable or unrecoverable exception occurs
- **WHEN** 任一编码或验证阶段无法正常完成
- **THEN** 系统保存原始证据、标记 `deferred` 或 `unresolved`，继续所有独立可执行阶段并最终发布报告

#### Scenario: Dependent stage cannot execute
- **WHEN** 阶段因前置异常缺少有效输入
- **THEN** 系统将其标记为 `skipped_dependency` 并关联根异常，而不制造独立根因或伪造成功产物

### Requirement: Retry deferred exceptions after all coding and verification
系统 SHALL 在所有编码和验证阶段完成或降级收敛后，对 deferred 异常统一执行恰好一次最终复修；复修 MUST 使用同次运行新增证据，且不得扩大写入范围、放宽测试、unsafe、差分、完整性或零定制门禁。

#### Scenario: Final retry repairs an exception
- **WHEN** 新增同次运行证据足以生成并验证合法修复
- **THEN** 系统记录第二次尝试、原子提交修复并重新执行所有受影响验证，成功后标记 `final_retry_repaired`

#### Scenario: Final retry still fails
- **WHEN** 最终复修无法生成、应用或完整验证合法修复
- **THEN** 系统停止继续重试，将项目标记为 `unresolved`，保留完整尝试历史并在最终报告显式列出

### Requirement: Separate execution completion from compliance
系统 MUST 独立发布 `execution_status` 和 `compliance_status`；runner 正常收敛或退出码为零不得隐含比赛合格，只有全部硬门禁通过且 unresolved 异常数为零时才能输出 `READY_FOR_EVALUATION`。

#### Scenario: Pipeline completes with residual exceptions
- **WHEN** 编排和报告发布完成但存在 unresolved、审计命中、证据缺失或硬门禁失败
- **THEN** `execution_status` 表示带异常完成，`compliance_status` 明确为未满足，并列出每项异常和影响

#### Scenario: All acceptance gates pass
- **WHEN** 当前运行全部证据有效、硬门禁通过、零定制审计干净且异常台账无 unresolved
- **THEN** 系统才可将 `compliance_status` 设置为 `READY_FOR_EVALUATION`

### Requirement: Enforce non-vacuous final gates
最终验证器 MUST 检查源码、公开 API、源测试、映射 API、差分场景、语义不变量和实际 Rust 测试计数均非零，映射完整且 unsupported 为零，并要求 locked Cargo 构建测试成功、unsafe 比例严格低于 0.10、源码不变、两种根布局和连续双跑均通过。

#### Scenario: Complete evidence satisfies every gate
- **WHEN** 所有计数、映射、命令、比率、完整性、布局和可重复性证据属于当前运行且相互一致
- **THEN** `final-verification.json` 逐项记录通过结论和证据路径

#### Scenario: Evidence is empty, stale, missing, or inconsistent
- **WHEN** 任一计数为空或为零、证据来自其他运行、路径不存在、报告冲突或硬门禁未执行
- **THEN** 最终验证器记录明确异常并禁止真空通过，同时继续发布完整失败证据

### Requirement: Atomically publish coherent final evidence
系统 SHALL 原子发布 `linux-environment.json`、源码前后清单、`cargo-build.log`、`cargo-test.log`、`unsafe-ratio.json`、零定制审计、异常台账、可重复性报告、`final-verification.json`、`result/output.md` 和 `result/issues/00-summary.md`；所有产物 MUST 共享运行身份、计数和状态。

#### Scenario: Normal report publication succeeds
- **WHEN** 最终聚合完成
- **THEN** 机器报告与两份人读报告从同一聚合模型生成，状态、异常数量、证据路径和结论一致

#### Scenario: Primary report generation fails
- **WHEN** 聚合、渲染或原子替换发生异常
- **THEN** 独立兜底发布器写出最小有效异常报告并同步输出结构化 stderr 摘要，不得伪报合格或丢失已记录异常

### Requirement: Make residual exceptions explicit to evaluators
最终人读报告 MUST 在摘要中列出每个最终未解决异常的 ID、阶段、根因、影响范围、首次修复结果、末尾复修结果和证据路径，不得仅用总数、附录或成功项掩盖异常。

#### Scenario: Residual exceptions remain
- **WHEN** 最终复修后 unresolved 数量大于零
- **THEN** `result/output.md` 和 `result/issues/00-summary.md` 在结论附近明确列出全部残留异常并声明不满足合规条件

#### Scenario: No residual exceptions remain
- **WHEN** 台账中所有异常均已修复且重新验证通过
- **THEN** 报告记录零 unresolved，并仍保留修复历史和验证证据供审计
