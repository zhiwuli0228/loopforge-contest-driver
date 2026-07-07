## Context

Change 2 已经在 `work/profiles/superspec/design-implementation-consistency-stages.yaml` 中声明了 `dic-00` 到 `dic-09` 的十阶段执行契约，Change 3 和 Change 4 又补上了 Core 模型与语言适配器输出边界，但这些契约还停留在“声明式定义”层面。蓝图中的 Change 5 需要把这些声明落实为 `work/subagent/` 下的阶段包，使每个阶段都能在受限上下文中工作，并通过文件交接而不是主上下文堆积来推进。

当前约束包括：阶段顺序、阶段名称和主要职责已经在 execution contract 中固定；默认流程仍为 `analyze-only`，不得修改业务源码；所有中间产物需要落到 `logs/trace/consistency/`；失败时需要保留阶段证据，且最终阶段仍应能汇总已有结果。该变更还必须和已有 Java / Generic 适配器、Core 模型命名与产物路径对齐，否则 Change 6 的 runtime 闭环会继续出现编排漂移。

## Goals / Non-Goals

**Goals:**
- 定义 `work/subagent/dic-00-preflight.md` 到 `work/subagent/dic-09-finalize.md` 的统一模板、职责边界和最小输入输出。
- 固定阶段间 handoff 机制，要求各阶段仅通过 `logs/trace/consistency/` 下的声明文件、摘要文件和 evidence 路径交接。
- 明确主 Skill / 编排器与阶段包的边界，使主流程只负责调度、摘要传递和 gate 判定，不直接在主上下文中持有完整源码或完整中间模型。
- 为失败保留、always-finalize、repair-plan 只读输出和证据完整性定义一致的阶段行为，确保 Change 6 可以直接消费这些阶段资产。

**Non-Goals:**
- 不在本变更中实现 runtime 命令、traceability 算法、drift 分类器或报告渲染器本身。
- 不新增超出十阶段之外的执行阶段，也不改写 Change 2 已确立的阶段顺序。
- 不开放业务源码 patch、代码生成或任何突破 `analyze-only` 的写权限。
- 不把具体语言扫描逻辑塞进阶段包内部；阶段包只定义消费何种实现模型和证据，而不重写适配器能力。

## Decisions

1. 采用“阶段包文档 + 声明式交接文件”的实现方式，而不是让主 Skill 直接内联十阶段提示词。
   - 每个 `dic-0x-*.md` 文件都固定包含阶段目标、允许输入、必需输出、gate、失败处理和交接清单。
   - 主编排器按阶段 ID 选择对应阶段包，并只向阶段传递必要的文件路径、短摘要和 guard 限制。
   - 这样可以避免主上下文持续膨胀，也能使阶段边界在仓库中可审计。

2. 所有跨阶段状态一律文件化到 `logs/trace/consistency/`，而不是依赖隐式会话记忆。
   - 阶段输出使用稳定命名约定，例如阶段摘要、结构化模型、gate 状态和 evidence 索引。
   - 下游阶段只能读取上游声明产物，禁止通过主编排器再额外注入未声明的大块源码内容。
   - 相比“主代理记住所有中间结果”，文件交接更容易回放、失败恢复和最终汇总。

3. 主编排器保持轻量，只负责调度、校验和 fail-fast/fail-soft 决策。
   - 阶段包负责生成其领域产物；编排器负责判断 gate 是否通过、是否继续下一阶段、以及是否触发最终 finalize。
   - `always_finalize=true` 时，即使中间 gate 失败，编排器也要把已有产物和失败原因交给 `dic-09` 生成最终汇总。
   - 这种划分让运行时编排与阶段内容解耦，便于后续 runtime 工具替换具体执行载体。

4. repair plan 阶段只输出建议，不获得业务源码写权限。
   - `dic-08` 可以基于 drift findings 和风险等级生成建议性的 repair plan、候选 patch 描述或验证建议。
   - guard 仍限制其只写 `logs/trace/consistency/`、`result/` 等声明输出路径。
   - 这保持了 analyze-only 主线，同时为未来受控修复能力预留出口。

5. 执行契约需要显式绑定“声明阶段”和“阶段包资产”，而不是仅声明阶段名称。
   - `consistency-execution-contracts` 在修改后将要求每个阶段 ID 都存在唯一对应的阶段包文件，且该文件声明的输入输出与 superspec/guard 保持一致。
   - 新 capability `consistency-stage-packages` 只负责定义阶段包本身的行为，不替代已有 profile、guard、adapter 或 core capability。
   - 这样可以把“有哪些阶段”和“阶段如何落地执行”分层表达，减少规范重叠。

## Risks / Trade-offs

- [Risk] 阶段包写得过细，会把实现细节和提示词策略过早固化。 → Mitigation: 只固定职责、输入输出、gate 和交接格式，不锁死内部分析方法。
- [Risk] 文件交接过多，可能增加执行开销和样板文件数量。 → Mitigation: 统一命名约定，要求每阶段至少产出一个摘要和必要结构化文件，避免无意义重复落盘。
- [Risk] execution contract、guard 和阶段包之间容易出现路径或阶段名漂移。 → Mitigation: 在 spec 中要求一一映射，并在任务中加入一致性校验。
- [Risk] `always_finalize` 语义处理不清，会导致失败阶段后既没停住也没正确汇总。 → Mitigation: 明确编排器只允许两类行为：gate 通过继续，或保留证据后跳转 finalize。

## Migration Plan

1. 在 `work/subagent/` 下建立十个 `dic-0x` 阶段包文件，并统一文档模板。
2. 为每个阶段定义输入、输出、gate、失败保留和 handoff 规则，确保交接路径落在 `logs/trace/consistency/`。
3. 更新主 Skill、stages superspec 和 guard，使它们引用同一组阶段 ID、文件路径和失败行为。
4. 增加阶段映射与交接校验，验证任一阶段失败时都能保留证据，并在启用 `always_finalize` 时进入 `dic-09`。
5. 回滚时可移除新增阶段包与对应 spec delta，并恢复 execution contract 对实际阶段包的绑定；由于不写业务源码，回滚范围仅限编排资产。

## Open Questions

- 阶段交接的结构化载体是否统一采用 JSON/YAML，还是允许不同阶段使用最适合的格式，只要路径与字段契约稳定？
- `dic-09` 最终汇总是否应强制消费 `result/output.md` 和 `result/issues/00-summary.md`，还是先只要求汇总 `logs/trace/consistency/` 中的阶段产物？
- 主 Skill 是否应直接声明每个阶段包的路径，还是通过独立的阶段注册表解析 `dic-0x` 到文件名的映射？
