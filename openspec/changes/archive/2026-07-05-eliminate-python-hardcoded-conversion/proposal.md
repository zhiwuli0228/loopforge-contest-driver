## Why

当前 C→Rust 转换的核心代码生成逻辑由 Python 硬编码实现（`c2rust_project_generator.py` ~930 行，`c2rust_analysis.py` ~500 行），将 C 函数分类为 11 种 body_kind 然后用固定规则映射到 Rust。在 AI 比赛中，用 Python 写代码转换规则是本末倒置——应该让 LLM 做所有需要判断的工作（理解、设计、生成、门禁），Python 只做零判断的纯工具（解析数据、执行命令、输出报告）。当前架构在以 C 代码多样性为考核点的比赛中会直接淘汰。

## What Changes

- **BREAKING**: 删除 `c2rust_project_generator.py` — 所有硬编码 C→Rust 类型映射、body_kind 渲染、struct 生成
- **BREAKING**: 删除 `c2rust_analysis.py` — 所有 body_kind 分类、translation_status 标记逻辑
- **BREAKING**: 删除 `c2rust_repair.py` — Python 修复循环
- **BREAKING**: 删除 `c2rust_semantic_repair.py` — Python 语义修复
- **BREAKING**: 删除 `c2rust_semantic_audit.py` — 硬编码语义审计
- **BREAKING**: 删除 `c2rust_invariant_tests.py` — 硬编码不变量测试渲染
- **BREAKING**: 删除 `opencode_repair_provider.py` — V1 opencode 桥接
- **BREAKING**: 删除 `generation_agent_provider.py` — V1 LLM 桥接，被 subagent 替代
- **BREAKING**: 重写 `loopforge_runner.py` — 从单体 Python 编排改为薄层：数据准备 + Agent 委托
- 清理 `source_analysis.py` — 移除 body_kind/translation_status 相关逻辑，保留纯数据提取
- 更新 `c2r-05-implement.md` subagent — 移除对 Python 生成器的引用，Agent 从 C source + spec 直接生成 Rust 代码
- 更新 `c2r-06-test.md` subagent — 移除对 `_render_tests()` 的引用
- 更新 `c2r-07-repair.md` subagent — 明确纯 LLM 修复路径
- 更新 `c2r-08-semantic-audit.md` subagent — 明确纯 LLM 不变量推导
- 更新 `work/skills/c-to-rust-migration-v2/SKILL.md` — 作为唯一编排入口

## Capabilities

### New Capabilities

- `agent-driven-code-generation`: Agent (LLM) 从 C source + spec + design 直接生成 Rust 代码，不做任何 Python 中间转换。每个模块由独立 subagent 生成，以 spec 为契约，以 C source 为参考。
- `agent-driven-test-generation`: Agent (LLM) 从 C 测试清单 + spec scenarios 生成 Rust 测试，覆盖正常路径、错误路径、边界条件。
- `agent-driven-repair`: Agent (LLM) 分析 build/test 错误，直接修复 Rust 代码或测试，不做 Python 规则匹配修复。
- `agent-driven-semantic-audit`: Agent (LLM) 从 C source 推导语义不变量，生成并执行不变量测试，记录失败而不是静默修复。
- `agent-orchestration`: loopforge_runner.py 改为薄编排层：调用 tools.py 获取数据，调用 semantic_planning.py 生成计划，然后委托 Agent (SKILL.md) 完成所有需判断的阶段。

### Modified Capabilities

- `source-parsing`: 移除 body_kind 分类和 translation_status 标记。`tools.py parse-source` 只返回结构化数据（files, functions, types, call_graph），不做任何"能否翻译"的判断。
- `superpower-guards`: 更新 phase 定义，移除对已删除 Python 函数的引用，所有代码生成阶段指向 subagent。

## Impact

- **删除**: `work/runtime/c2rust_project_generator.py`, `c2rust_analysis.py`, `c2rust_repair.py`, `c2rust_semantic_repair.py`, `c2rust_semantic_audit.py`, `c2rust_invariant_tests.py`, `opencode_repair_provider.py`, `generation_agent_provider.py`
- **重写**: `work/runtime/loopforge_runner.py` (~1139 行 → ~200 行薄编排层)
- **修改**: `work/runtime/source_analysis.py` (移除 body_kind 分类), `work/runtime/tools.py` (移除 body_kind 相关导入)
- **修改**: `work/subagent/c2r-05-implement.md`, `c2r-06-test.md`, `c2r-07-repair.md`, `c2r-08-semantic-audit.md`
- **修改**: `work/skills/c-to-rust-migration-v2/SKILL.md`
- **依赖**: V2 subagent 文件已存在，OpenSpec schema 已存在，tools.py 数据命令已存在
