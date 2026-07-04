## Context

V2 蓝图定义了三层执行治理：OpenSpec（产物管理）、SuperSpec（阶段编排）、SuperPower（权限边界）。当前 SuperSpec 目录下只存在 `consistency-check-stages.yaml`，缺少 C-to-Rust 迁移专用的阶段编排文件。该文件是 SKILL.md v2 编排器在派发子代理时的权威参考——它声明每个阶段使用哪个 subagent、输入哪些文件、输出哪些产物、通过/失败/阻塞的门禁值。

现有 artifacts 已就绪：11 个 subagent 文件 (`c2r-00` → `c2r-10`)、SuperPower guards (`c-to-rust-migration-guards.yaml`)、tools.py CLI、SKILL.md v2 编排 prompt。本变更补全缺失的 SuperSpec 阶段编排配置。

## Goals / Non-Goals

**Goals:**
- 定义 11 个阶段的完整 subagent 绑定、输入输出契约和门禁规则
- 遵循现有 `consistency-check-stages.yaml` 的格式约定
- 引用通用变量路径（`SOURCE_ROOT`、`WORK_DIR`、`OUTPUT_DIR`）——零项目定制
- 与现有 subagent 文件、SuperPower guards、tools.py 命令保持一致

**Non-Goals:**
- 不修改任何现有 subagent 文件或 SKILL.md
- 不引入新 Python 模块或 tools.py 命令
- 不在配置文件中编码任务特定信息（如 API 名称、项目名称）

## Decisions

### Decision 1: 阶段定义来源

**选择:** 基于 SKILL.md v2 的 Phase Sequence 表和 subagent 文件头部定义来提取每个阶段的 subagent、输入、输出和门禁。

**理由:** SKILL.md v2 和 subagent 文件是两个已存在的权威来源。stages yaml 是它们的结构化镜像——不创造新信息，只做格式转换。`consistency-check-stages.yaml` 已为此格式提供了模板。

**替代方案:** 从 V2 蓝图原文拼接——但蓝图是设计文档而非结构化规范，字段不全（缺少 input/output 细节）。

### Decision 2: 文件路径模式

**选择:** 使用通用变量占位符模式：
- `SOURCE_ROOT/**` — 源码树（只读）
- `work/design/README.md` — 设计契约
- `work/runtime/tools.py` — CLI 入口
- `logs/trace/c-to-rust/*.json` — trace 证据
- `work/output/*/src/**/*.rs` — 生成的 Rust 源码
- `result/output.md`, `result/issues/00-summary.md` — 最终报告

不使用任何具体的项目名、API 名或硬编码路径。

**理由:** 比赛规则要求"零定制、零硬编码"。通用路径模式 + 运行时变量注入确保框架适用于任何 C/C++ 项目。

### Decision 3: 门禁值设计

**选择:** 三门禁制——`success_gate`（通过，继续下一阶段）、`failure_gate`（失败但可降级）、`blocked_gate`（阻塞，终止流水线）。

**理由:** 与 consistency-check-stages.yaml 和 SKILL.md v2 的三态门禁（`PHASE_PASS`/`PHASE_DEGRADED`/`PHASE_BLOCKED`）保持一致。

### Decision 4: can_modify_code 标记

**选择:** 只有 Phase 5 (implement)、Phase 6 (test)、Phase 7 (repair)、Phase 8 (semantic-audit) 标记 `can_modify_code: true`，其余阶段为 `false`。

**理由:** 只有实现/测试/修复阶段可以写 Rust 源码。分析/规划/验证阶段只读。这与 SuperPower guards 中的读写权限边界一致。

## Risks / Trade-offs

- **subagent 文件与 yaml 不一致的风险:** subagent 文件日后可能独立修改而 yaml 未同步 → 建议在 CI 中增加一致性校验脚本（已有 `validate_subagent_contract.py`）
- **YAML 格式严格性:** stages yaml 仅用于编排器在派发前的权限/输入验证。如果格式有误，编排器会因无法解析而阻塞，不会静默产生错误结果
