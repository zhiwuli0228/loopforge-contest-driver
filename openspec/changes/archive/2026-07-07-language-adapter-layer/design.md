## Context

Change 3 已经把设计对象、实现对象、traceability、evidence 和 report 的核心模型固定下来，但仓库还没有一层稳定的语言适配器把真实源码扫描结果归一化到这些模型。蓝图中的 Change 4 要先落地 Java 默认适配器，再提供 Generic fallback，这样 Change 5 的 `dic-04` 实现模型抽取阶段和 Change 6 的 runtime 命令才能消费统一结构，而不是继续直接绑定语言特定脚本。

当前约束包括：适配器代码位于 `work/adapters/`；Java 是默认路径，但失败时必须无缝退回 Generic；所有适配器都必须输出 Core 定义的实现模型与证据引用；不得把 `Controller`、`Spring`、`pom.xml` 等术语升级为跨适配器必填字段；默认流程仍保持 `analyze-only`，不修改业务源码。

## Goals / Non-Goals

**Goals:**
- 定义 `work/adapters/java/` 与 `work/adapters/generic/` 的职责边界、探测输入和标准输出。
- 规定适配器选择流程，使 source inventory 和默认 Java profile 能明确记录“命中了哪个适配器、为什么命中、何时 fallback”。
- 约束 Java 适配器至少覆盖项目识别、HTTP 入口点、数据结构、配置面和测试资产扫描。
- 约束 Generic 适配器在识别能力较弱时仍输出可追踪、可审计的部分实现模型，而不是中断整个流水线。
- 补充 Core 与执行契约对适配器来源、扩展元数据和阶段交接的要求。

**Non-Goals:**
- 不在本变更中实现 traceability 匹配算法、drift 分类器或最终报告生成器。
- 不新增业务源码修复、代码生成或自动 patch 能力。
- 不为 Java 之外的具体语言实现专用适配器。
- 不把 adapter 内部扫描算法细节固化成必须的实现方式，只固定输入输出契约和最小能力。

## Decisions

1. 采用“适配器注册表 + 统一扫描结果契约”，而不是让每个阶段直接调用任意脚本。
   - 每个适配器都声明 `adapter_id`、支持的检测信号、输入路径要求、产物类型和扩展元数据命名空间。
   - source inventory 阶段负责根据 profile 与检测结果选中一个主适配器，并记录 fallback 决策证据。
   - 这样可以让 `dic-02` 和 `dic-04` 的边界清晰：前者做选择与清点，后者做规范化抽取。

2. Java 适配器输出中保留框架细节，但只能以可选扩展字段存在。
   - 公共实现模型仍使用中立对象，例如 `module`、`entrypoint`、`data_shape`、`config_surface`、`test_artifact`。
   - Java 专有信息如注解、框架类型、构建系统、包路径可以写入 `extensions.java.*` 或等价命名空间。
   - 相比直接把 Spring/MVC 语义提升为公共字段，这种设计更符合 Core 的语言无关边界。

3. Generic fallback 必须允许“部分识别但不中断”。
   - 当 Java 识别失败，或源码不是受支持的 Java 工程时，Generic 适配器仍需输出文件、符号、配置和测试的部分实现对象。
   - 这些对象必须带上 `coverage_status`、`confidence` 或等价信号，明确哪些信息是近似推断。
   - 这样下游 traceability 可以继续运行，并把不确定性体现在 evidence 和 drift 结论中。

4. 适配器证据由“选择证据 + 抽取证据”两层组成。
   - 选择证据回答为什么选 Java 或 Generic，例如检测到 `pom.xml`、`build.gradle`、包结构，或检测失败原因。
   - 抽取证据回答每个实现对象来自哪个源码文件、配置文件或测试文件。
   - 这种拆分能帮助后续审计是“选错适配器”还是“适配器抽取不完整”。

5. 执行契约只固定适配器外部接口，不固定内部实现库。
   - Java 适配器可以先基于文件扫描、正则、轻量语法分析或后续 AST 能力实现。
   - Generic 适配器也可以根据仓库类型逐步增强。
   - 这样能先交付稳定的契约和目录边界，再让后续实现按风险逐步演进。

## Risks / Trade-offs

- [Risk] Java 适配器要求过多，会把 Change 4 变成半个 runtime 重写。 → Mitigation: 只锁定最小扫描面与标准输出，不规定完整实现细节。
- [Risk] Generic fallback 过于宽松，可能输出大量低置信度对象，影响下游判断。 → Mitigation: 要求保留置信度、部分覆盖状态和选择证据，让不确定性显式可见。
- [Risk] 修改 Core 实现模型 requirement 可能导致已有模型实现需要补字段。 → Mitigation: 只补充适配器来源和扩展元数据约束，不推翻现有中立对象分类。
- [Risk] 执行契约同时涉及 profile、stage 和 adapters，容易出现名字漂移。 → Mitigation: 在 spec 中固定 `java`、`generic`、`dic-02`、`dic-04` 以及共享产物名称。

## Migration Plan

1. 在 `work/adapters/` 下建立 Java 与 Generic 的目录、注册入口和最小文档边界。
2. 为默认 Java profile 与阶段契约补上适配器选择、fallback 和实现模型输出的规范。
3. 更新 Core capability，使实现模型显式支持适配器来源、扩展元数据和部分识别状态。
4. 先实现 Java 与 Generic 的最小扫描骨架，再补充验证样例，确保它们输出同一实现模型结构。
5. 将 `dic-04` 和后续 traceability 输入绑定到该统一结构，而不是适配器私有格式。

回滚时可以删除 `work/adapters/` 新增内容，并撤回对应的 spec 与 contract delta；由于本变更不触碰业务源码，回滚范围仅限仓库内适配器与文档资产。

## Open Questions

- Java 适配器首版是否只支持 Maven/Gradle 常见布局，还是需要同时覆盖更宽松的多模块目录变体？
- Generic 适配器的 `confidence` 与 `coverage_status` 应由 Core 枚举直接约束，还是先由 adapter 扩展字段承载？
- 适配器注册表最终放在 `work/adapters/__init__.py`、独立 registry 文件，还是交由 runtime 层统一发现？
