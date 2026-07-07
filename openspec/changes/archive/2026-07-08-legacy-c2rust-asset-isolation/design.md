## Context

前六个一致性变更已经把仓库的默认叙事、阶段契约、Core 模型、语言适配器和 runtime 闭环切换到 design-implementation consistency，但仓库内仍存在完整的 C2Rust skill、profile、rule、subagent 和 runtime 资产族群。当前检索结果表明，这些遗留资产不仅仍然存在于 `work/skills/`、`work/profiles/`、`work/subagent/`、`work/rules/` 和 `work/runtime/` 下，还继续被 `work/runtime/loopforge_runner.py`、`work/scripts/run.sh`、`work/skills/loopforge-driver/SKILL.md` 以及部分 consistency 参考文档直接引用。

蓝图与设计文档已经给出 Change 7 的边界：旧资产不建议直接删除，而应迁入 `work/archived/c-to-rust/` 或明确标记为非默认；默认 consistency-check 路径则必须不再依赖这些 C2Rust 语义。本变更因此是一次默认入口净化和遗留资产隔离，而不是功能移除或兼容性抹除。

## Goals / Non-Goals

**Goals:**
- 将 legacy C2Rust 资产从默认 consistency-check 发现路径、文档入口和运行时调用链中剥离。
- 使用单一归档根 `work/archived/c-to-rust/` 收纳仍需保留的旧 skill、profile、rule、subagent 和 runtime 资产。
- 为保留的 legacy 资产增加显式“非默认/仅归档”标识，避免调用方误认为它们仍是权威入口。
- 增加一组静态校验，验证权威 consistency-check 文件、脚本和运行时不再回落到 `c-to-rust` / `c2r` 路径。

**Non-Goals:**
- 不删除历史资产，也不承诺保留旧 C2Rust 流程的零改动执行兼容性。
- 不在本变更中重构一致性 runtime、本地验证逻辑或十阶段 consistency 流水线本身。
- 不清理所有历史设计参考文档；只有会误导默认流程的入口引用需要迁移、替换或显式标注。
- 不把 C2Rust 能力重新包装成新的默认 adapter；本变更只做隔离，不做重新定位。

## Decisions

1. 采用 `work/archived/c-to-rust/` 作为唯一遗留归档根。
   - `work/docs/loopforge-design-implementation-consistency-design.md` 已明确推荐这个目录，沿用它可以避免再创建 `work/legacy/`、`work/deprecated/` 等第二套命名。
   - 该归档根下保留原有大类结构，如 `skills/`、`profiles/`、`rules/`、`subagent/`、`runtime/`，以降低迁移后检索和追溯成本。
   - 备选方案是在原路径就地保留并仅加 warning 注释，但这无法从默认发现路径中摘除资产，因此不采用。

2. 默认路径以“迁移资产”而不是“软禁用”为主，原位置只保留必要说明文件或兼容占位。
   - 直接迁移目录和脚本文件可以让 `rg`、自动发现逻辑、路径白名单和运行时默认值自然失效，降低误用概率。
   - 若某个旧路径短期内仍需存在，其内容必须退化为 README、stub 或指针文件，并明确声明新的归档位置和“非默认”属性。
   - 备选方案是完全删除旧资产，但这会损失历史追踪和回溯价值，因此不采用。

3. 按资产族迁移，并同步修正所有权威 consistency 入口引用。
   - 第一类是 `work/skills/c-to-rust-migration/`、`work/skills/c-to-rust-migration-v2/` 等 skill 入口。
   - 第二类是 `work/profiles/examples/c-to-rust-migration.yaml`、`work/profiles/superspec/c-to-rust-migration-stages.yaml`、`work/profiles/superpower/c-to-rust-migration-guards.yaml` 等 profile/stage/guard。
   - 第三类是 `work/subagent/c2r-*` 与 `work/subagent/c-to-rust-*.md`。
   - 第四类是 `work/rules/loopforge/adapters/c-to-rust/` 与 `work/runtime/rust_project_generation.py`、`check_unsafe_ratio.py`、`test_migration_validation.py` 等 runtime helper。
   - 迁移过程中必须同时修正 `work/runtime/loopforge_runner.py`、`work/scripts/run.sh`、`work/skills/loopforge-driver/SKILL.md` 以及任何权威 consistency 文档中的旧路径引用。

4. 用“权威入口清单 + 禁止 legacy 引用校验”保证隔离效果。
   - 权威入口至少包括默认 consistency skill、默认 Java profile、consistency stages/guards、runtime tools 入口以及仓库级运行脚本。
   - 为这些入口增加静态校验，要求它们的默认执行链不再包含 `c-to-rust` trace namespace、`c2r-` subagent、旧 migration profile 或旧 skill。
   - 备选方案是仅通过人工 review 保证，但这对后续演化不稳定，因此不采用。

5. 历史参考文档分层处理，避免误伤纯历史材料。
   - 位于 `work/references/design/` 的 C2Rust 设计稿可保留为历史材料，但不得继续被默认 consistency skill、runner 或 profile 当作当前权威输入。
   - 若 consistency 文档仍需提及旧资产，只能以“历史来源/已归档”语义出现，并指向归档路径。
   - 这样既保留知识资产，也避免默认流程叙事反向污染。

## Risks / Trade-offs

- [Risk] 迁移 legacy 文件会打断仍依赖旧路径的脚本或测试。 → Mitigation: 先建立资产清单和引用扫描，再按族迁移，并在必要时保留显式 stub/README 指针。
- [Risk] 只隔离入口、不清理引用，最终仍可能从 `loopforge_runner.py` 或驱动 Skill 回落到旧流程。 → Mitigation: 将“权威入口不得解析到 legacy 路径”写入 spec，并增加静态验证。
- [Risk] 历史文档中仍大量出现 `c-to-rust` 术语，可能导致审查者误判为未完成。 → Mitigation: 区分“归档参考资料”与“权威执行入口”，仅对后者施加零 legacy 依赖要求。
- [Risk] 将不同种类资产集中到归档根后，路径迁移量较大。 → Mitigation: 按 skills/profiles/subagents/rules/runtime 五类分批迁移，并优先修正默认入口而非一次性全量重排。

## Migration Plan

1. 盘点 legacy C2Rust 资产及其所有仓库内引用，形成迁移清单。
2. 创建 `work/archived/c-to-rust/` 及其子结构，按资产族迁移旧 skills、profiles、rules、subagents 和 runtime helpers。
3. 将旧路径替换为归档说明或兼容占位，并在其中标记“非默认，仅历史保留”。
4. 修正所有权威 consistency 入口文件，确保默认 skill、profile、runner、脚本和文档不再引用 legacy 路径。
5. 增加静态校验或 focused tests，验证默认 consistency-check 路径不包含 `c-to-rust` trace namespace、旧 skill/profile 或 `c2r-*` subagent 依赖。
6. 执行一次 consistency 默认流程的 smoke 校验，并执行一次 legacy 资产可定位性检查，确认隔离与保留两端都成立。

回滚时可将 `work/archived/c-to-rust/` 中的资产迁回原路径，并恢复入口引用；由于本变更只做目录与引用整理，不涉及业务源码回滚。

## Open Questions

- 哪些旧测试和辅助脚本应随资产一同迁入归档根，哪些应直接删除以减少维护面？
- 是否需要保留一个专门的 `README.md` 或 manifest，列出每个归档资产的原路径和迁移原因，供后续审计使用？
