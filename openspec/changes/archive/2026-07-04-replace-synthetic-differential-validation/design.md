## Context

当前测试迁移验证器把结构完整性、Cargo 成功和合成比较结果混合为语义成功。C/Rust 差分没有独立进程，mutation 没有实际注入，invariant 覆盖没有语义关联；最终语义审计因使用另一套分母而正确阻塞。Windows 包装脚本又绕过 runner 最终门禁，形成相互冲突的结论。正式要求是 SOURCE_ROOT 只读、无项目特判、Linux 评测可运行且 Windows 调试结果一致。

## Goals / Non-Goals

**Goals:**

- 只接受真实执行产生的 C/Rust 独立观测和 mutation 检出证据。
- 所有阶段使用同一个 canonical evidence manifest 和稳定实体 ID。
- invariant 覆盖、源断言覆盖和 API 覆盖均可追溯到实际执行结果。
- runner 与所有平台入口共享唯一最终 verdict，并证明连续运行可重复。

**Non-Goals:**

- 不通过降低覆盖分母、删除测试或放宽语义要求让当前 FlashDB 输出变为成功。
- 不在通用 harness 中内置 FlashDB API、路径、构建命令或黄金输出。
- 不保证外部生成模型逐字节确定；只要求其候选产物通过确定性验证并发布规范化结果。

## Decisions

### 1. 使用 canonical evidence manifest 冻结分母

分析门禁通过后发布 manifest，包含 source test/assertion、public API、behavior contract、invariant 的稳定 ID 集合、来源和摘要。后续阶段只能引用这些 ID，不能重新推导或缩小分母。选择单一 manifest 而不是阶段间对数量，是因为相同数量仍可能对应不同实体。

### 2. 差分执行采用结构化 adapter 协议

每个向量分别声明 C adapter 与 Rust adapter；执行器在独立临时目录复制同一输入镜像，设置相同种子和故障计划，并要求两侧输出同 schema 的 observation JSON。命令、环境白名单、stdout/stderr、退出码、输入/输出摘要全部入证据。未配置 adapter 不回退到合成值，而是阻塞。

### 3. Mutation 使用隔离副本和可验证补丁

每个 mutation 在 Rust 候选工程隔离副本中应用，记录修改前后摘要和目标位置，再运行声明的检测面。只有至少一个关联测试或差分向量从 baseline pass 变为 mutation fail 才算 killed；编译失败仅在 mutation 明确属于编译型时有效。

### 4. 覆盖以稳定 ID 和执行记录连接

invariant/test/API 映射必须引用具体 assertion/comparison ID，并由 cargo test name 或 adapter execution ID 证明实际执行。禁止使用首个断言、任意向量或文件存在性代表覆盖。

### 5. 最终 verdict 是单一纯函数

runner 根据同一份 gate manifest 计算最终状态；PowerShell/Bash 入口只负责启动、保存日志并透传状态，不得自行写 READY。Cargo 成功是必要条件但不是最终成功条件。

### 6. 平台差异仅允许出现在环境字段

Windows/Linux 使用相同的生成代理启用规则、轮次和验证命令。可重复性比较排除时间、绝对路径和工具链平台字段，只比较输入身份、实体集合、生成源码、测试集合、门禁结论和规范化观测。

## Risks / Trade-offs

- [真实 C Oracle 构建方式随项目变化] → 从源码构建证据发现 adapter，不允许项目身份分支；无法构建时完整阻塞报告。
- [差分和 mutation 显著增加运行时间] → baseline 构建缓存只读复用，mutation 隔离并按检测面最小执行，完整验收仍运行固定全集。
- [跨平台观测存在路径或错误文本差异] → schema 只比较契约声明字段，环境差异单独记录，禁止为特定项目定制规范化。
- [旧证据被误消费] → 提升 schema major version并要求 canonical manifest digest；旧版只可诊断读取。

## Migration Plan

1. 引入新 schema、manifest 和负例，先让旧合成证据 fail closed。
2. 实现 adapter runner、真实差分、mutation 和 ID 覆盖映射。
3. 切换最终 verdict 与平台入口，删除重复 READY 逻辑。
4. 在通用 fixture 和真实 FlashDB 输入上执行 Windows/Linux 验收及两次干净运行。
5. 仅在新证据链全部通过后废弃旧 schema；失败时保留完整诊断并回滚到 BLOCKED，而非旧成功逻辑。

## Open Questions

- FlashDB C 测试入口是否能由现有构建证据直接发现，或需先提供通用 C adapter 生成器。
- 完整 mutation 集的运行预算需要在首次真实基准后确定，但固定关键 mutation 不得抽样省略。
