## Context

Change 1 已将入口文档、任务配置和设计输入切换为 `consistency-check` / `analyze-only`。仓库同时保留了 C2Rust Skill、阶段与 guard，以及若干通用 consistency profile 雏形，但尚无与蓝图一致的专用主 Skill 和完整契约组合。后续 Change 3-6 将依赖这些文件定义模型边界、适配器选择、阶段交接和运行权限，因此本变更必须先提供稳定且可校验的声明式接口。

约束包括：默认只读分析；Java 是默认适配器但不能成为全局世界观；Generic 必须作为 fallback；阶段间通过 `logs/trace/consistency/` 交接；工具层不负责最终一致性判断；旧 C2Rust 资产的归档不属于本变更。

## Goals / Non-Goals

**Goals:**
- 提供可作为唯一编排入口的设计与实现一致性校验 Skill。
- 通过默认 Java profile 明确适配器选择、分析维度和验证策略。
- 用 10 阶段 superspec 定义输入、输出、gate 和失败保留语义。
- 用 superpower guards 强制阶段级读取、写入和源码修改边界。
- 让 Skill、profile、stages、guards 使用同一组阶段标识、路径和默认策略。

**Non-Goals:**
- 不实现 Core 模型、Java/Generic Adapter 或 runtime 工具。
- 不创建 10 个阶段的子代理提示文件；本变更只定义其后续必须实现的契约。
- 不启用自动补丁、代码生成或业务源码写入。
- 不归档或删除旧 C2Rust 资产。

## Decisions

1. 使用四类声明文件组成一个联合运行契约。
   - 主 Skill 负责总体编排和证据规则；example profile 负责项目/语言默认值；superspec 负责阶段图；superpower profile 负责权限边界。
   - 相比把所有规则塞进 Skill，这种分层允许后续替换语言 profile，而不复制阶段和安全规则。

2. 使用稳定阶段 ID `dic-00` 到 `dic-09`，并将阶段产物固定在 `logs/trace/consistency/`。
   - 稳定 ID 便于 Change 5 的子代理文件和 Change 6 的 runtime 输出直接绑定契约。
   - 不复用 C2Rust 阶段 ID，避免新旧执行链发生隐式耦合。

3. Java profile 只定义适配器默认值，不把 Java 术语放入通用阶段契约。
   - `java` 为首选、`generic` 为 fallback；superspec 和 guards 只引用抽象的 design/implementation model。
   - 相比建立 Java 专用流水线，这保留了后续多语言扩展能力。

4. 默认权限采用 deny-by-default，并由阶段逐项开放。
   - 所有阶段禁止修改 `SOURCE_ROOT`；只有声明输出路径可写；源码内容读取从 inventory 到 implementation extraction 按需开放。
   - 即使配置误设，契约仍要求 `allow_patch=false` 和 `allow_code_generation=false` 时拒绝写源码。

5. 现有通用 consistency 文件作为迁移输入，而不是第二套权威默认值。
   - 实现时检查并复用其中仍有效的字段；新蓝图命名文件成为本工程的权威契约，旧通用文件需明确为兼容/模板用途或对齐引用关系。
   - 相比直接复制现有文件，这能防止阶段名、输出路径和权限策略漂移。

## Risks / Trade-offs

- [Risk] 声明式契约暂时没有 runtime 强制执行。 → Mitigation: 在 tasks 中加入结构和交叉引用校验，并将执行器落地留给后续 change。
- [Risk] 新旧 consistency profile 并存可能让调用方选错。 → Mitigation: 明确新专用文件为默认权威来源，并对现有文件进行用途标注或引用对齐。
- [Risk] 过早固定阶段产物名会限制后续实现。 → Mitigation: 只固定蓝图已定义的阶段边界与核心产物，允许阶段内部增加辅助文件。
- [Risk] deny-by-default 会增加后续阶段授权配置量。 → Mitigation: 以共享只读根和逐阶段输出白名单减少重复，同时保持可审计性。

## Migration Plan

1. 审核现有 consistency profiles 和旧 Skill 中可复用的结构。
2. 新增主 Skill 及其按需引用的契约参考文档。
3. 新增默认 Java example profile，并对齐 Change 1 的配置默认值。
4. 新增 10 阶段 superspec 和 deny-by-default guards。
5. 校验四类文件的阶段 ID、输入输出路径、适配器和只读策略一致。
6. 标注或调整现有通用 consistency 文件的角色，消除默认来源歧义。

回滚时删除新增的专用契约文件，并恢复对现有通用 profile 的引用；不需要迁移运行数据或业务源码。

## Open Questions

- 后续 Change 5 是否需要为每个阶段单独提供机器可读 schema，还是先以 YAML 中的输入输出字段作为唯一契约？
- 现有 `consistency-check*.yaml` 文件应保留为通用模板还是在 Change 7 中统一归档？

