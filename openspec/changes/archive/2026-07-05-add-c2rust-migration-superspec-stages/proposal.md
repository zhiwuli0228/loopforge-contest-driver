## Why

V2 蓝图（`work/docs/V2-DESIGN-BLUEPRINT.md`）明确要求新建 `work/profiles/superspec/c-to-rust-migration-stages.yaml` 作为 C-to-Rust 迁移的阶段编排配置文件。当前只存在 `consistency-check-stages.yaml`，缺少迁移专用的阶段定义。SuperSpec 阶段编排是 V2 三层执行治理（OpenSpec + SuperSpec + SuperPower）的关键组成部分——它定义每个阶段的 subagent 绑定、输入输出契约、门禁值和权限边界。

## What Changes

- 新建 `work/profiles/superspec/c-to-rust-migration-stages.yaml`：定义 11 阶段（c2r-00-preflight → c2r-10-finalize）的完整编排
- 每个阶段声明：subagent 文件、输入文件（通用路径模式）、输出产物、成功/失败/阻塞门禁值、是否允许修改代码
- 引用现有 subagent 文件（`work/subagent/c2r-*.md`）、SuperPower guards（`work/profiles/superpower/c-to-rust-migration-guards.yaml`）和 tools.py 命令

## Capabilities

### New Capabilities

- `c2rust-migration-superspec`: C-to-Rust 迁移的 SuperSpec 阶段编排——定义 11 个阶段的 subagent 绑定、输入输出契约和门禁规则

### Modified Capabilities

None. 这是新增配置文件，不修改现有能力。

## Impact

- 新增文件: `work/profiles/superspec/c-to-rust-migration-stages.yaml`
- 被引用方: `work/skills/c-to-rust-migration-v2/SKILL.md`（编排 prompt）、各 `work/subagent/c2r-*.md`（子代理文件）
- 零定制数据——所有路径使用通用变量模式（`SOURCE_ROOT/**`, `work/`, `logs/trace/c-to-rust/`）
