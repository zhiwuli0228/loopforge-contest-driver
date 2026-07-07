## Context

Change 5 已经把 `dic-00` 到 `dic-09` 的阶段包与文件交接骨架固定下来，但当前 `work/runtime/` 仍主要保留旧的 C2Rust 导向工具形态。`work/runtime/tools.py` 已经存在 `scan-code`、`extract-implementation`、`run-verification`、`write-report` 等命令雏形，但缺少与一致性校验设计文档对齐的 `scan-design`、`build-traceability`、drift 聚合和终态报告闭环，也没有把最终产物路径、只读边界和失败保留语义固定成统一契约。

蓝图对 Change 6 的要求很明确：默认 `analyze-only`、不修改业务源码、可生成 `result/output.md`、`result/issues/00-summary.md`、`logs/trace/final-report.md` 以及阶段中间产物。与此同时，Change 3 到 Change 5 已经定义了 Core 模型、语言适配器和十阶段阶段包，因此本变更不需要重新定义这些上游抽象，而需要把它们接成一个最小可运行闭环，并确保 runtime 输出命名与阶段 handoff 保持一致。

## Goals / Non-Goals

**Goals:**
- 将一致性校验 runtime 明确收敛为一组稳定 CLI 命令，覆盖设计扫描、源码扫描、实现抽取、traceability 构建、验证执行和最终报告写入。
- 统一 runtime 模块职责，使 `work/runtime/` 中的数据提取、映射、验证和报告写入边界清晰，并复用已有 Core 模型与适配器输出。
- 固定 analyze-only 默认行为，要求 runtime 只写声明产物路径，禁止修改 `SOURCE_ROOT` 下业务源码。
- 明确失败保留和终态汇总策略，使部分阶段失败时仍能保留证据并输出最终报告。

**Non-Goals:**
- 不在本变更中提升 Java AST 精度，也不引入复杂语义推理或自动修复。
- 不修改 Change 5 已固定的十阶段顺序，只补齐 runtime 对阶段产物的消费和落盘。
- 不处理 Change 7 的遗留 C2Rust 资产归档，只要求新闭环不依赖这些旧语义才能工作。
- 不要求所有 drift 判断都在工具内自动完成；Agent 或阶段包仍可负责最终确认，但 runtime 需要提供稳定输入输出骨架。

## Decisions

1. 继续以 `work/runtime/tools.py` 作为统一 CLI 入口，而不是拆成多个互相独立的脚本入口。
   - 现有仓库已经通过 `tools.py` 暴露 `scan-code`、`extract-implementation`、`run-verification`、`write-report`，扩展它比引入新入口更容易保持脚本、文档和调用路径一致。
   - 统一入口还便于 `INSTRUCTION.md`、`run.sh`、子代理和后续自动化测试共享同一套命令约定。
   - 备选方案是让每个 runtime 模块提供独立 CLI，但这会增加参数漂移和调用方式不一致的风险，因此不采用。

2. runtime 模块采用“结构化 JSON 中间产物 + Markdown 终态报告”的双层输出模型。
   - `scan-design`、`scan-code`、`extract-implementation`、`build-traceability`、`run-verification` 优先输出可机器消费的 JSON 文件，供阶段包和后续工具复用。
   - `write-report` 负责生成人类可读的 `result/output.md`、`result/issues/00-summary.md` 和 `logs/trace/final-report.md`，并从结构化产物汇总状态、findings、coverage 与验证结果。
   - 备选方案是所有阶段直接输出 Markdown，但这会削弱后续自动验证与复用能力，因此只把 Markdown 作为最终展示层。

3. traceability 构建与 drift 判定分层处理，但 runtime 仍需承担稳定汇总责任。
   - `build-traceability` 负责把 Design Model 与 Implementation Model 组合成候选映射、覆盖状态和缺口清单，不把所有策略复杂度压进一个命令。
   - drift 最终确认可以由 Agent 或上层阶段产物补充，但 runtime 必须能消费已有 traceability/drift 数据并产出一致的报告文件。
   - 这样既符合设计文档中“build-traceability 不做最终一致性判断”的约束，也能让第一版闭环先跑通。

4. 验证执行必须显式记录“成功、失败、不可执行、跳过”状态，而不是仅返回命令输出。
   - 当前 `run-verification` 只回传原始命令结果，无法稳定支撑最终报告中的验证结论。
   - 本变更将要求 runtime 保留命令、退出码、超时、不可执行原因和与 findings 相关的验证摘要，供 `dic-09` 与最终报告直接消费。
   - 备选方案是把验证完全留给子代理写 Markdown，总体可行但不利于稳定测试，因此不采用。

5. 最终输出路径采用固定命名，并与阶段包 handoff 保持一一对应。
   - `logs/trace/consistency/` 存放阶段中间 JSON/Markdown 产物，`logs/trace/final-report.md` 存放终态审计摘要，`result/output.md` 与 `result/issues/00-summary.md` 面向用户和评估入口。
   - runtime 和阶段包都使用同一组路径常量或约定，避免 `reports/`、`trace/`、`result/` 多套命名并存。
   - 这比“各命令自定义输出位置”更严格，但能直接降低脚本、spec 和测试之间的路径漂移。

6. analyze-only 通过产物写入边界强制体现，而不是依赖调用方自觉遵守。
   - runtime 命令默认只接收设计根、源码根、配置文件和声明产物路径，不接收业务源码回写参数。
   - 任何 repair suggestion 或 verification hint 只以报告或 trace artifact 形式输出，不写回 `SOURCE_ROOT`。
   - 这使 Change 6 在行为上与 Change 2、Change 5 的只读约束保持闭合。

## Risks / Trade-offs

- [Risk] runtime 一次性补齐太多命令，容易把 MVP 和第二阶段增强混在一起。 → Mitigation: spec 只要求最小闭环命令与产物，不把 AST 精度和复杂语义比对纳入本变更。
- [Risk] 结构化中间产物字段过早固定，后续增强可能需要兼容成本。 → Mitigation: 先固定必要字段和输出路径，允许通过扩展字段承载更多细节。
- [Risk] 仍保留部分 Agent 参与 drift 判定，会让“工具闭环”不是完全自治。 → Mitigation: 明确 runtime 负责稳定输入输出和最终汇总，复杂判定策略后续再逐步下沉。
- [Risk] 旧的 C2Rust 叙事和现有 `tools.py` 子命令仍可能对外暴露，造成混淆。 → Mitigation: 在 spec 与任务中要求一致性校验相关命令成为权威路径，并补充验证脚本覆盖最终输出。

## Migration Plan

1. 在 `work/runtime/` 中补齐设计扫描、traceability 构建、验证聚合和报告写入所需模块，并让 `tools.py` 暴露权威命令接口。
2. 对齐 `work/runtime/tools.py`、阶段包输出和脚本期望的路径命名，确保 `logs/trace/consistency/`、`logs/trace/final-report.md`、`result/output.md`、`result/issues/00-summary.md` 一致。
3. 更新执行契约 spec，使十阶段 handoff 与 runtime 命令产物形成闭环，特别是 `dic-05` 到 `dic-09` 的输入输出。
4. 增加最小 smoke/contract 验证，证明默认 analyze-only 运行可以落盘最终报告且不会修改业务源码。
5. 若需回滚，可移除新增 runtime 模块与 spec delta，恢复旧 CLI 暴露；由于默认只写 trace/result 目录，回滚不涉及业务源码恢复。

## Open Questions

- `scan-design` 的第一版是只读取 `work/design/README.md`，还是要同时支持设计目录内的多文件清单与引用跟踪？
- drift 最终确认数据是否在第一版由 runtime 直接生成结构化 findings，还是允许 `dic-06`/`dic-07` 先写入中间 JSON 后再由 `write-report` 汇总？
- `logs/trace/final-report.md` 与 `result/output.md` 是否需要不同粒度，还是允许前者偏审计轨迹、后者偏结果摘要并共享大部分内容？
