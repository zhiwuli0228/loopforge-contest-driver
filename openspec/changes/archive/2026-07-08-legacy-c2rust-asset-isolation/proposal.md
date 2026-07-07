## Why

前六个一致性变更已经建立了默认入口、阶段契约、Core 模型、语言适配器、子代理流水线和 runtime 闭环，但仓库中仍保留大量旧的 C2Rust skill、profile、rule、subagent 和 runtime 资产。这些遗留资产继续暴露在默认路径下，会让使用者误入旧语义，也会让新的 consistency-check 工程在文档、工具入口和验证路径上继续受到污染。

## What Changes

- 新增一个专门的遗留资产隔离 capability，定义哪些 C2Rust 资产必须归档、迁移或显式标记为非默认路径。
- 规定默认 consistency-check 工作流只能暴露设计与实现一致性校验相关的 skill、profile、subagent 和 runtime 入口，不再依赖旧的 C2Rust 叙事完成任务。
- 要求保留旧资产的可追溯访问方式，但这些资产必须位于归档或 legacy 命名空间中，并带有明确的非默认说明。
- 更新执行契约，要求权威入口、阶段引用和运行时命令不能再把默认调用链解析到 C2Rust 相关目录、提示词或验证脚本。

## Capabilities

### New Capabilities
- `consistency-legacy-asset-isolation`: 定义遗留 C2Rust 资产的归档范围、默认可见性限制、兼容保留方式和验证要求。

### Modified Capabilities
- `consistency-execution-contracts`: 收紧默认 consistency-check 合同，禁止权威入口、阶段定义和默认 profile 回落到旧的 C2Rust 资产路径。

## Impact

- 影响 `work/skills/c-to-rust-migration/`、`work/skills/c-to-rust-migration-v2/`、`work/profiles/examples/c-to-rust-migration.yaml`、`work/profiles/superspec/c-to-rust-migration-stages.yaml`、`work/profiles/superpower/c-to-rust-migration-guards.yaml` 等 legacy 入口的归档或隔离方式。
- 影响 `work/subagent/c2r-*`、`work/subagent/c-to-rust-*.md` 的默认可见性和引用关系。
- 影响 `work/rules/loopforge/adapters/c-to-rust/` 以及 `work/runtime/rust_project_generation.py`、`check_unsafe_ratio.py`、`test_migration_validation.py` 的默认暴露边界。
- 影响一致性工程的文档、脚本和验证逻辑，需要增加“默认流程不触发 legacy 语义”的检查。
