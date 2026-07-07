# LoopForge Design-Implementation Consistency Blueprint

> 版本：v0.1
> 适用分支：`loopforge-design-implementation-consistency`
> 基线：`origin/c_2_rust_claude`
> 目标文档：`work/docs/loopforge-design-implementation-consistency-design.md`

## 1. 目的

这份蓝图的目标不是重复设计文档，而是把设计文档拆成可执行、可追踪、可验收的 change 路线图。

它解决三个问题：

1. 后续每个 change 做什么。
2. 每个 change 依赖什么、产出什么。
3. 如何判断 change 已完成，可以进入下一个阶段。

## 2. 总体策略

建议将整体改造拆成 6 个主变更，外加 1 个可独立收口的清理变更。

```
Change 1  入口与配置切换
   ↓
Change 2  OpenSpec / Skill / Profile 契约
   ↓
Change 3  Core 抽象层
   ↓
Change 4  语言适配器层
   ↓
Change 5  流水线与子代理
   ↓
Change 6  Runtime / 报告 / 验证闭环
   ↓
Change 7  遗留 C2Rust 资产归档与隔离
```

原则：

- 先建立任务契约，再实现模型。
- 先做抽象层，再做语言适配器。
- 先跑通只读分析，再考虑受控修复。
- 先保证证据链，再追求识别精度。

## 3. 变更拆分

### Change 1: 入口与工程切换

目标：

- 把工程从 C2Rust 语义切换为 `consistency-check` 语义。
- 确保新工程入口、工作区说明和配置默认值都指向一致性校验。

建议范围：

- `README.md`
- `INSTRUCTION.md`
- `work/README.md`
- `work/loopforge.config.yaml`
- `work/design/README.md`

产出：

- 新工程叙述统一为设计与实现一致性校验。
- 默认模式为 `consistency-check`。
- 默认执行策略为 `analyze-only`。

完成标准：

- 仓库根入口不再以 Rust 迁移为主叙事。
- `work/design/README.md` 能作为一致性校验任务契约。
- 配置项与设计文档目标一致。

依赖：

- 无前置依赖，优先执行。

### Change 2: OpenSpec / Skill / Profile 契约

目标：

- 建立这套工程的运行规范和阶段定义。
- 把任务输入、权限边界、阶段输出、验收结果统一下来。

建议范围：

- `work/skills/design-implementation-consistency/SKILL.md`
- `work/skills/design-implementation-consistency/references/*.md`
- `work/profiles/examples/default-java-consistency.yaml`
- `work/profiles/superspec/design-implementation-consistency-stages.yaml`
- `work/profiles/superpower/design-implementation-consistency-guards.yaml`

产出：

- 一个稳定的主 Skill。
- 一套默认 Java profile。
- 一套 staged execution 定义。
- 一套 guard 约束，明确哪些阶段可以读什么、写什么。

完成标准：

- 变更执行能按阶段描述而不是靠口头约定。
- 子代理输入输出在文档层面闭合。
- 默认 Java 和 generic fallback 的策略明确。

依赖：

- Change 1 完成后再做。

### Change 3: Core 抽象层

目标：

- 建立语言无关的数据模型。
- 把设计对象、实现对象、映射关系、漂移发现、证据引用统一表示。

建议范围：

- `work/core/design_model.py`
- `work/core/implementation_model.py`
- `work/core/traceability_model.py`
- `work/core/drift_taxonomy.py`
- `work/core/evidence_contract.py`
- `work/core/severity_policy.py`
- `work/core/report_model.py`

产出：

- 可被所有适配器共享的核心数据结构。
- 核心层中不出现 `Controller`、`Service`、`Spring` 等 Java 专有概念。

完成标准：

- Core 能表达设计和实现的抽象关系。
- 证据模型足以支撑后续 drift 报告。
- severity / taxonomy 可以被后续规则复用。

依赖：

- Change 2 完成后再做，避免模型定义与阶段契约脱节。

### Change 4: 语言适配器层

目标：

- 先落地 Java 默认适配器，再提供 Generic fallback。
- 把源码扫描结果转换为统一 Implementation Model。

建议范围：

- `work/adapters/java/*`
- `work/adapters/generic/*`

产出：

- Java 项目识别、endpoint 扫描、DTO 扫描、配置扫描、测试扫描。
- 通用文件/符号/配置/测试扫描能力。
- 不同语言都输出同一实现模型结构。

完成标准：

- Java 项目可被默认识别。
- Java 识别失败时可退回 generic。
- 适配器输出可直接被 traceability 阶段消费。

依赖：

- Change 3 完成后再做。

### Change 5: 流水线与子代理

目标：

- 把设计文档里的 10 阶段流水线变成可执行的阶段包。
- 每阶段都能通过文件交接而不是主上下文堆积来推进。

建议范围：

- `work/subagent/dic-00-preflight.md`
- `work/subagent/dic-01-design-intake.md`
- `work/subagent/dic-02-source-inventory.md`
- `work/subagent/dic-03-design-model.md`
- `work/subagent/dic-04-implementation-model.md`
- `work/subagent/dic-05-traceability-map.md`
- `work/subagent/dic-06-drift-analysis.md`
- `work/subagent/dic-07-risk-classification.md`
- `work/subagent/dic-08-repair-plan.md`
- `work/subagent/dic-09-finalize.md`

产出：

- 每个阶段都有明确输入、输出和 gate。
- 阶段间仅通过 `logs/trace/consistency/` 交接。
- 主编排器不再直接吞完整源码。

完成标准：

- 10 个阶段能按顺序表达完整分析链路。
- 每阶段的职责边界清楚，没有职责重叠。
- 失败时能够停在对应 gate 并保留报告。

依赖：

- Change 2、Change 3、Change 4 都完成后再做。

### Change 6: Runtime / 报告 / 验证闭环

目标：

- 让工具真正跑通数据提取、映射、分析、报告、验证这条链。
- 默认只读分析，不修改业务代码。

建议范围：

- `work/runtime/tools.py`
- `work/runtime/design_scanner.py`
- `work/runtime/code_inventory.py`
- `work/runtime/traceability_builder.py`
- `work/runtime/drift_classifier.py`
- `work/runtime/verification_runner.py`
- `work/runtime/report_writer.py`

产出：

- `scan-design`
- `scan-code`
- `extract-implementation`
- `build-traceability`
- `run-verification`
- `write-report`

完成标准：

- 能生成 `result/output.md`。
- 能生成 `result/issues/00-summary.md`。
- 能生成 `logs/trace/final-report.md` 和阶段产物。
- 默认不写业务源码。

依赖：

- Change 5 完成后再做。

### Change 7: 遗留资产归档与隔离

目标：

- 把旧 C2Rust 语义资产与新工程隔离。
- 避免新旧规则、子代理和 runtime 互相污染。

建议范围：

- `work/skills/c-to-rust-migration/`
- `work/skills/c-to-rust-migration-v2/`
- `work/rules/loopforge/adapters/c-to-rust/`
- `work/subagent/c2r-*`
- `work/runtime/rust_project_generation.py`
- `work/runtime/check_unsafe_ratio.py`
- `work/runtime/test_migration_validation.py`

产出：

- 旧资产进入归档目录或明确标注非默认。
- 新工程入口只暴露 consistency-check 语义。

完成标准：

- 新路径不再依赖旧 C2Rust 叙事完成任务。
- 避免用户误走旧流程。

依赖：

- 可以在主链完成后单独收口。

## 4. 推荐里程碑

### Milestone A: 任务契约成立

覆盖：

- Change 1
- Change 2

验收重点：

- 工程入口、配置、profile、guard、stage 定义都已经稳定。
- 后续改造有统一术语。

### Milestone B: 抽象层成立

覆盖：

- Change 3
- Change 4

验收重点：

- Core 与 adapter 分层清晰。
- Java 默认适配器和 generic fallback 都能输出统一结构。

### Milestone C: 流水线成立

覆盖：

- Change 5

验收重点：

- 阶段化子代理和文件交接可执行。
- 任何阶段失败都能定位到对应 gate 和证据。

### Milestone D: 闭环成立

覆盖：

- Change 6

验收重点：

- 可以完成一次完整 analyze-only run。
- 结果、问题摘要、证据链都能落盘。

### Milestone E: 遗留清理完成

覆盖：

- Change 7

验收重点：

- 旧资产不再影响默认流程。

## 5. 跟踪表

建议按下面这个表持续维护每个 change 的状态。

| Change | 状态 | 目标产物 | 主要依赖 | 验收门 | 当前阻塞 |
|---|---|---|---|---|---|
| Change 1 | planned | 入口与配置统一 | 无 | `consistency-check` 可作为默认任务语义 | - |
| Change 2 | planned | Skill / Profile / Stage / Guard | Change 1 | 阶段契约可读、可执行、可追踪 | - |
| Change 3 | planned | Core 抽象模型 | Change 2 | Core 无语言污染 | - |
| Change 4 | planned | Java + Generic 适配器 | Change 3 | 统一 Implementation Model | - |
| Change 5 | planned | 10 阶段流水线 | Change 2, 3, 4 | 阶段交接闭合 | - |
| Change 6 | planned | runtime + report + verify | Change 5 | 可跑通 analyze-only 闭环 | - |
| Change 7 | optional | 旧资产归档 | Change 1-6 | 默认流程不再碰旧语义 | - |

状态建议值：

- `planned`
- `in_progress`
- `blocked`
- `done`
- `optional`

## 6. 变更完成定义

每个 change 都应该满足以下最小完成定义：

1. 目标文件或目标目录已经存在，且语义与设计文档一致。
2. 产物之间的依赖链已经闭合。
3. 有最少一条可复现的验证方式。
4. 文档里能明确写出“下一步接什么”。

如果一个 change 只改了入口文案，但没有形成后续阶段所需的契约，则不能标记为完成。

## 7. 风险点

### 风险 1: 先写代码，后补契约

后果：

- 后续 change 会频繁返工。

应对：

- 先完成 Change 1 / 2，再进入模型和适配器实现。

### 风险 2: Java 语义污染 Core

后果：

- 工程失去通用性，后续多语言扩展成本上升。

应对：

- Core 层禁止引入 Java 专有概念。

### 风险 3: 流水线过重

后果：

- 阶段太多但没有清晰交接，执行成本过高。

应对：

- 先保证文件交接和 gate，再追求精细化子代理。

### 风险 4: 报告无证据

后果：

- Drift 结论不可审计。

应对：

- 每条 finding 强制包含设计证据和实现证据。

## 8. 建议的执行顺序

1. 先完成 Change 1。
2. 再完成 Change 2。
3. 然后完成 Change 3。
4. 再完成 Change 4。
5. 接着完成 Change 5。
6. 最后完成 Change 6。
7. Change 7 作为收尾清理。

## 9. 使用方式

后续每启动一个 change，都应该先回答四个问题：

1. 这个 change 解决什么边界问题。
2. 它依赖哪些上游产物。
3. 它的完成标准是什么。
4. 它要把哪些文件交给下一步。

如果这四个问题答不清，就先不要进入实现。

