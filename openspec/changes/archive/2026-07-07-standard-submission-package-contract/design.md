## Context

当前一致性校验框架把外部输入抽象为 `work/design/README.md + SOURCE_ROOT`。这个模型的优点是通用，但副作用也很直接: 运行时、适配器、阶段包和验证逻辑都会倾向于猜测目标项目结构，并逐渐演变成“为了兼容任意仓库而加规则”。这与新的方向相反。新的方向不是继续扩大兼容面，而是把比赛题验证格式提升为统一提交契约，让目标项目围绕平台标准组织输入。

标准化之后，平台面对的对象不再是“任意源代码根”，而是“标准提交包”:

```text
SUBMISSION_ROOT/
├── README.md
├── design-docs/
├── code/
├── test-cases/
└── contest.meta.yaml   # optional
```

这里的关键变化不只是目录名替换，而是职责重新划分:

- `README.md` 承载比赛说明、冻结 API/错误码/状态规则摘要、验证命令与修改边界。
- `design-docs/` 承载业务设计真相源。
- `code/` 是唯一业务实现和未来受控修复的落点。
- `test-cases/` 是黑盒验证资产，不属于修复目标。
- `contest.meta.yaml` 为将来减少 README 解析歧义提供结构化补充，但不是唯一真相源。

## Goals / Non-Goals

**Goals:**
- 将 authoritative 外部输入根从 `SOURCE_ROOT` 切换为 `SUBMISSION_ROOT`。
- 为标准提交包定义稳定的目录职责、真相源优先级和写入边界。
- 让阶段、适配器和 runtime 围绕 `README.md`、`design-docs/`、`code/`、`test-cases/` 工作，而不是在任意仓库根自由扫描。
- 将验证流程切换为优先执行标准包声明的构建和黑盒测试命令。
- 为后续 repair-enabled 模式定义稳定边界: 默认不改，开启后仅能修改 `code/`。

**Non-Goals:**
- 本变更不实现完整自动修复闭环。
- 本变更不引入对非标准提交包的长期兼容承诺。
- 本变更不要求一次性解决 README 自然语言解析的全部语义歧义。
- 本变更不改变 Core 的语言无关建模原则。

## Decisions

1. 将 `SUBMISSION_ROOT` 设为唯一 authoritative 外部输入根，而不是继续扩展 `SOURCE_ROOT` 语义。
   - Rationale: 只要入口仍然是“任意源码根”，系统就会被迫继续做项目结构猜测，无法建立稳定标准。
   - Alternatives considered: 保留 `SOURCE_ROOT` 作为主入口并额外支持标准包。这样会让两套输入模型长期共存，契约继续分裂。

2. 采用固定目录职责，而不是从任意文件树中动态推断设计区、代码区和测试区。
   - Rationale: 比赛题标准的价值就在于输入边界稳定、验证边界稳定、可写区域稳定。固定职责还能让 preflight 在最早阶段拦截不合规输入。
   - Alternatives considered: 通过 profile 配置不同项目的目录映射。那会重新回到“我们适配目标项目”的路线。

3. 维持 `README.md + design-docs/` 的双层设计真相源模型。
   - Rationale: 比赛说明通常不仅有业务设计，还会定义冻结 API、错误码、环境依赖、验证命令和禁止修改项，这些不应全部塞进 `design-docs/`。将 README 作为规则和验收入口，`design-docs/` 作为细节设计面，更贴近标准包现实。
   - Alternatives considered: 只读 `design-docs/`，忽略 README 的规则性内容；或把 README 内容全部结构化进元数据文件。前者会丢掉验收边界，后者对输入方要求过高。

4. 默认验证命令来源从“自动探测”切换为“标准包声明优先，自动探测兜底”。
   - Rationale: 对比赛式输入，验证命令本身就是验收契约的一部分，不能继续把 `mvn test` 之类的通用猜测当主路径。
   - Alternatives considered: 完全禁止自动探测。这样在标准包声明不完整时会让系统过于脆弱，因此保留兜底，但将其降为非 authoritative。

5. 将写入边界细化为标准包内分区，而不是整个输入根只读。
   - Rationale: 后续若开启修复模式，业务修复只能落在 `code/`。继续把整个输入根一概只读会阻断 repair-enabled 设计；放开整个输入根又会污染设计和黑盒基线。
   - Alternatives considered: 继续全部只读，或放开整个提交包。前者无法支持后续修复闭环，后者会破坏验收基线。

6. 保留 `work/design/README.md` 作为仓库自说明，不再作为运行时外部任务真相源。
   - Rationale: 仓库仍需要内部蓝图和默认说明，但它不应再冒充真实提交包的比赛说明。
   - Alternatives considered: 直接删除 `work/design/README.md`。这会影响仓库自描述和现有文档链路，没有必要。

## Risks / Trade-offs

- [Risk] 从 `SOURCE_ROOT` 迁移到 `SUBMISSION_ROOT` 会触发广泛的契约改动。 → Mitigation: 先在 specs 和设计层收敛 authoritative 模型，再分阶段改脚本、profiles、guards 和 runtime。
- [Risk] README 中的验证命令和修改边界可能是自然语言，提取存在歧义。 → Mitigation: 明确 `contest.meta.yaml` 作为结构化补充来源，但保持 README 为主入口。
- [Risk] 现有适配器和阶段包大量默认假设“源代码根就是输入根”。 → Mitigation: 将 `code/` 解析提升为 preflight 和 source inventory 的显式输出，后续阶段只消费解析后的固定路径。
- [Risk] 标准包格式过严可能降低早期试用便利性。 → Mitigation: 在 preflight 中输出明确缺失项和修复建议，而不是静默降级到任意仓库模式。

## Migration Plan

1. 在契约层引入 `consistency-submission-package-contract`，并更新 execution/language-adapter/stage/runtime 相关 specs。
2. 调整配置、Skill、profile、superspec 和 guard，使 authoritative 输入根改为 `SUBMISSION_ROOT`。
3. 调整 preflight 和 source inventory，显式解析标准包目录并输出 `submission-layout` 结构化工件。
4. 调整 design scanner、adapter 输入边界和 verification runner，使其围绕固定子目录工作。
5. 调整 repair 边界与报告范围，确保未来只允许写 `code/`。

Rollback strategy:
- 在实现期如果发现对运行链路影响过大，可临时保留入口脚本对 `SOURCE_ROOT` 的兼容别名，但不得恢复其 authoritative 地位，也不得在 specs 中继续将其定义为主输入模型。

## Open Questions

- `test-cases/` 在所有标准提交包中是否一律必需，还是允许通过 `contest.meta.yaml` 显式声明缺省？
- `contest.meta.yaml` 的第一版是否只承载验证命令和目录覆盖，还是还要承载语言、构建工具、修复边界等结构化信息？
- `README.md` 中的冻结 API、错误码、命令说明是否需要单独抽取成标准 Design Model 子类型，还是先作为 evidence-bearing constraints 处理？
