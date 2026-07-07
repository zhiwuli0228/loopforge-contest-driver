## Why

Change 3 已经固定了语言无关的 Core 抽象模型，但仓库仍缺少把真实源码结构转换成该模型的语言适配器层。现在补上 Java 默认适配器和 Generic fallback，才能让后续 traceability、drift 分析和阶段化流水线消费统一的实现模型，而不是继续依赖零散的语言特定扫描逻辑。

## What Changes

- 新增语言适配器能力，定义 Java 默认适配器与 Generic fallback 必须输出的统一实现模型、探测流程和证据要求。
- 为 Java 适配器定义项目识别、HTTP 入口点扫描、DTO/数据结构扫描、配置面扫描与测试资产扫描的最小契约。
- 为 Generic fallback 定义通用文件、符号、配置与测试扫描的最小契约，确保 Java 识别失败时仍能生成可消费的实现模型。
- 更新 Core capability 对适配器输出的约束，明确适配器必须通过规范化字段和可选扩展元数据承载语言细节。
- 更新执行契约中关于默认适配器选择、阶段输出和下游消费的一致性要求，使实现模型抽取阶段能够稳定交接给 traceability 阶段。

## Capabilities

### New Capabilities
- `consistency-language-adapters`: 定义 Java 默认适配器与 Generic fallback 的探测、扫描、规范化输出和证据要求。

### Modified Capabilities
- `consistency-core-models`: 补充实现模型对适配器来源、规范化关系和扩展元数据边界的要求。
- `consistency-execution-contracts`: 补充默认适配器选择、fallback 行为和阶段输出对语言适配器能力的依赖要求。

## Impact

- 影响 `work/adapters/java/` 与 `work/adapters/generic/` 的目录职责、扫描器边界和输出结构。
- 影响 `work/core/` 中实现模型对适配器来源、证据引用和可选扩展字段的定义。
- 影响 `work/profiles/examples/default-java-consistency.yaml`、阶段契约以及后续 `dic-04` 到 `dic-06` 的输入输出约定。
- 影响 `openspec/specs/` 中的一致性能力定义，需要新增语言适配器 capability，并更新 Core 与执行契约的相关 requirement。
- 不在此变更中实现 traceability、drift 分类、最终报告写入或业务源码修改。
