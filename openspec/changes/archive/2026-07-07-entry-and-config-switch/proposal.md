## Why

当前仓库的根叙事、工作区说明和默认配置仍然围绕 `C/C++ -> Rust` 迁移，这与蓝图定义的下一阶段目标不一致。先完成入口与配置切换，可以把后续所有 change 的执行语义统一到 `consistency-check`，避免继续在旧术语和旧默认值上叠加实现。

## What Changes

- 将仓库根 `README.md`、`INSTRUCTION.md`、`work/README.md` 的主叙事切换为设计与实现一致性校验。
- 更新 `work/loopforge.config.yaml` 的默认模式与执行策略，使新工程默认进入 `consistency-check` 与 `analyze-only`。
- 重写 `work/design/README.md` 的职责描述，使其成为一致性校验任务契约，而不是迁移题目说明。
- 统一工作区对外术语，减少后续 change 在文档、配置和运行时语义上的歧义。

## Capabilities

### New Capabilities
- `consistency-entry-config`: 定义仓库入口、工作区说明和默认配置切换到一致性校验语义所需的契约。

### Modified Capabilities

## Impact

- 影响仓库根文档与工作区说明。
- 影响 `work/loopforge.config.yaml` 中的默认任务语义、模式选择和执行策略。
- 影响后续 OpenSpec change 的命名、术语和默认运行预期。
- 不引入新的运行时依赖，也不修改业务代码路径。
