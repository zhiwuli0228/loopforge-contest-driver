## Context

Change 2 已经建立了 Skill、profile、stage 和 guard 的运行契约，但这些契约仍缺少一套真正可复用的语言无关数据模型。蓝图中的 Change 3 要先把设计对象、实现对象、traceability、drift、evidence、severity 和 report 统一建模，后续 Change 4 的 Java/generic 适配器、Change 5 的阶段化流水线以及 Change 6 的 runtime/report 才能围绕同一套对象交接，而不是各自发明字段和命名。

当前约束包括：Core 必须位于 `work/core/`；不得引入 `Controller`、`Service`、`Spring` 等 Java 专有世界观；模型既要支持设计侧抽取，也要支持实现侧扫描和最终报告；阶段间交接仍以 `logs/trace/consistency/` 为主，但文件内容必须能映射到稳定的 Core 类型。

## Goals / Non-Goals

**Goals:**
- 定义语言无关的 `design_model`、`implementation_model`、`traceability_model`、`drift_taxonomy`、`evidence_contract`、`severity_policy` 和 `report_model` 边界。
- 为每类模型明确最小必填字段、对象关系和可扩展字段，保证后续不同适配器可以汇聚到同一结构。
- 让执行契约显式依赖这些 Core 模型名称和交接语义，避免阶段文档与实现对象名漂移。
- 为后续 Change 4-6 提供可验证的导入点和结构校验方式。

**Non-Goals:**
- 不实现 Java 或 generic 扫描器。
- 不实现 runtime 命令、traceability 算法或 drift 分类规则本身。
- 不设计面向特定框架的字段，例如 Spring MVC 注解、JPA 实体或 Maven 专属结构。
- 不修改业务源码，也不改变 analyze-only 的默认执行策略。

## Decisions

1. 使用七个独立但互相关联的 Core 模块，而不是一个大而全的单文件模型。
   - `design_model.py` 负责设计侧对象，例如 capability、component、interface、data contract、constraint。
   - `implementation_model.py` 负责实现侧对象，例如 module、symbol、endpoint、data shape、config surface、test artifact。
   - `traceability_model.py` 负责设计对象与实现对象之间的 link、coverage、gap 和 unresolved reference。
   - `drift_taxonomy.py`、`severity_policy.py`、`evidence_contract.py`、`report_model.py` 负责分类、证据、严重级别和最终报告封装。
   - 相比单文件集中定义，这种拆分更适合后续适配器和 runtime 分层导入，也能降低语言适配器绕开抽象层直接写报告的概率。

2. 所有模型都采用“抽象语义 + 来源证据”双轨结构。
   - 每个核心对象既要表达语义身份，也要携带来源引用，例如设计文档位置、源码文件位置、配置位置或测试位置。
   - 这样后续 traceability 和 drift finding 可以复用对象自带证据，而不是在每个阶段重新拼接出处。
   - 相比把 evidence 只留到报告阶段补录，这种做法更容易保证证据链闭合。

3. Core 层只暴露中立术语，语言和框架特征由 adapter 归一化后再写入。
   - 例如实现模型可以表达 `service_interface`、`entrypoint`、`data_shape`，但不能直接要求 `SpringController` 或 `FastAPI router`。
   - adapter 负责把 Java/generic 世界中的具体现象映射到这些抽象类型和 tags。
   - 这样能满足蓝图要求，避免 Java 语义污染整个工程。

4. 在执行契约中固定与 Core 对齐的阶段产物名，而不固定语言适配器内部过程。
   - `dic-03` 输出 design model，`dic-04` 输出 implementation model，`dic-05` 输出 traceability，`dic-06` 输出 drift findings，`dic-07` 输出 risk classification，`dic-09` 汇总为 report。
   - stages、guards、profile 和 runtime 只需围绕这些稳定模型协作。
   - 这比在 Change 3 就规定 Java 扫描细节更稳妥。

5. 为每类模型预留扩展字段，但要求公共必填字段最小而稳定。
   - 基础字段应覆盖 `id`、`kind`、`name`、`summary`、`evidence_refs`、`attributes/tags`、`relationships/status` 等通用结构。
   - 允许 adapter 或 runtime 在命名空间扩展字段中附带语言特定元数据，但不得替代公共字段。
   - 这样既支持当前 Java 优先路线，也不堵死后续多语言适配。

## Risks / Trade-offs

- [Risk] Core 字段定义过细，会在 Change 4 适配器实现时暴露大量不必要约束。 → Mitigation: 只锁定跨阶段必需字段，把语言细节放入可选扩展字段。
- [Risk] Core 字段定义过粗，后续 traceability 和 drift 报告无法表达关键差异。 → Mitigation: 在 spec 中明确 coverage、gap、evidence、severity 和 report 的最小能力。
- [Risk] 修改 execution contract 可能影响已归档的阶段契约理解。 → Mitigation: 仅补充对 Core capability 的依赖，不改变已确立的阶段顺序和只读边界。
- [Risk] 先定义模型再实现 runtime，可能出现“文档正确但代码尚未验证”。 → Mitigation: tasks 中要求加入结构校验和最小样例，供后续 change 复用。

## Migration Plan

1. 在 `work/core/` 下建立七个核心模块文件和统一导出边界。
2. 先定义设计模型、实现模型和 evidence 的基础对象，再补充 traceability、drift、severity 和 report 组合对象。
3. 为核心对象增加最小结构校验或样例装配，验证跨模块引用关系可闭合。
4. 更新 execution contract 的 delta spec，使阶段与 profile 明确引用 Core 模型产物。
5. 将后续 adapter、subagent、runtime 的实现任务绑定到这些模型名称，而不是各自定义临时 JSON 结构。

回滚时可以删除 `work/core/` 新增模块并撤回 contract delta；由于本 change 不修改业务源码或外部状态，回滚只涉及仓库内文件。

## Open Questions

- Core 模型的序列化格式最终由 Change 5/6 固定为 JSON、YAML 还是 Python 原生对象后再落盘？
- `severity_policy` 是否只定义枚举与映射规则，还是需要同时携带阈值配置接口？
- generic adapter 是否需要在 Change 4 引入额外的 `unknown`/`partial` 状态，以表达无法精确识别的实现对象？
