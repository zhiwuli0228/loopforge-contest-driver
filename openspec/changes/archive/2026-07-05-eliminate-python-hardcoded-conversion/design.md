## Context

当前系统有两层架构并存但未连接:

1. **V1 Python 硬编码层** (实际运行): `loopforge_runner.py` → `c2rust_analysis.py` (body_kind 分类) → `c2rust_project_generator.py` (硬编码类型映射 + 11 种 body_kind 渲染) → `c2rust_repair.py` (Python 修复循环) → `c2rust_semantic_audit.py` (硬编码不变量检测)

2. **V2 Agent 层** (已设计，未接线): `work/skills/c-to-rust-migration-v2/SKILL.md` (10 阶段编排) + 11 个 `work/subagent/c2r-*.md` 文件 (每阶段 bounded context prompt) + `tools.py` (6 个零判断 CLI 命令)

`loopforge_runner.py` 在第 844 行直接调用 `generate_project()` — Python 硬编码生成器。V2 subagent 文件从未被 runner 使用。

这次变更的约束:
- `tools.py` 及其 6 个子命令 (`parse-source`, `run-verification`, `check-unsafe`, `fault-injection`, `neutrality-audit`, `write-report`) 保持不变——它们是零判断的数据层
- `source_analysis.py` 的 pycparser 解析 + JSON 输出保留，但 body_kind/translation_status 相关逻辑移除
- `semantic_planning.py` 保留——从分析结果生成迁移计划（确定性计算，非判断）
- `rust_project_generation.py` 的 `validate_candidate()` / `audit_unsafe()` 保留——纯验证逻辑
- 11 个 subagent 文件已存在于 `work/subagent/`

## Goals / Non-Goals

**Goals:**
- 彻底删除所有 Python 硬编码 C→Rust 转换逻辑（8 个文件）
- `loopforge_runner.py` 变为薄编排层: 数据准备 + Agent 委托
- Agent 负责所有需要判断的阶段: 理解、设计、规格、生成、测试、修复、语义审计、门禁判定
- Python 只做零判断工具: 解析源码 → JSON、执行 cargo → 原始输出、扫描文件 → 数据
- 所有 Rust 代码由 LLM subagent 直接生成，以 C source + spec 为上下文

**Non-Goals:**
- 不修改 `tools.py` 的 CLI 接口（6 个子命令不变）
- 不修改 OpenSpec schema
- 不修改 `semantic_planning.py` 或 `rust_project_generation.py` 的验证逻辑
- 不创建新的 subagent 文件（现有 11 个已足够，只更新内容）
- 不改变 SuperPower 权限文件的结构

## Decisions

### 1. 三层架构: Agent = 判断, Python = 工具

```
Layer 1: Python Tools (零判断)
  tools.py parse-source → 结构化 JSON（文件列表、函数签名、类型定义）
  tools.py run-verification → cargo build/test 原始输出
  tools.py check-unsafe → unsafe 行计数
  tools.py fault-injection → 变异测试原始结果
  tools.py neutrality-audit → 禁用词扫描结果
  tools.py write-report → 格式化数据写入 markdown

Layer 2: Python Planning (确定性计算)
  semantic_planning.py → 从分析结果计算迁移计划
  rust_project_generation.py::validate_candidate() → 验证生成的 Rust 项目
  source_analysis.py (清理后) → pycparser 解析 + 结构化 JSON

Layer 3: Agent (所有判断)
  SKILL.md → 10 阶段编排
  Subagent → 每阶段的判断和生成
  Phase 0-4: 理解 C 源码、设计架构、写 spec、做计划
  Phase 5: 直接生成 Rust 代码（不再经过 Python 中间表示）
  Phase 6: 直接生成 Rust 测试
  Phase 7: 分析错误、修复代码
  Phase 8: 推导语义不变量、编写不变量测试
  Phase 9-10: 门禁判断、最终报告
```

替代方案: 保留部分 Python 生成作为"兜底"——被否决。用户要求彻底铲除，在比赛中任何残留的硬编码规则都是淘汰理由。

### 2. Agent 直接从 C source 生成 Rust，不经过 Python 中间表示

当前流程: C source → pycparser → body_kind 分类 → Python 渲染 → Rust

新流程: C source → tools.py parse-source (数据) → semantic_planning (计划) → Agent 读 C source + spec + plan → Rust

关键变化: Agent 直接阅读 `.c`/`.h` 源文件作为上下文的一部分。不去依赖 Python 对函数体的"理解"（body_kind）。Agent 自己能读懂 C 代码。

替代方案: 增强 body_kind 覆盖更多模式 → 仍然是硬编码，治标不治本。

### 3. loopforge_runner.py 的职责收缩

当前 `loopforge_runner.py` (~1139 行):
- 自检、解析配置、创建 AgentTaskPacket
- 调用 `analyze_source()` → Python 分析
- 调用 `generate_project()` → Python 硬编码生成
- 调用 `run_repair_loop()` → Python 修复
- 调用 `evaluate_semantic_equivalence()` → Python 审计
- 大量 trace 输出、报告生成

新 `loopforge_runner.py` (~200 行):
- 自检、解析配置、创建上下文包
- 调用 `tools.py parse-source` 获取结构化数据
- 调用 `semantic_planning.py` 获取迁移计划
- 组装上下文 JSON 写入文件
- 输出"请执行 SKILL.md"指令 + 上下文路径
- 不再调用任何生成/修复/审计函数

也就是说，runner 变成一个"任务分发器": 准备所有数据，然后交给 Agent 执行 SKILL.md。

### 4. 上下文传递: 文件-based，非内存-based

Agent (Claude) 和 subagent 通过文件交换数据。SKILL.md 定义的 `PRIOR_OUTPUTS` 机制不变:

```
Phase 1 → source-inventory.json (写)
Phase 2 → design.md (写, 读 source-inventory.json)
Phase 3 → specs/**/*.md (写, 读 design.md)
Phase 4 → tasks.md + implement-plan.md (写, 读 specs)
Phase 5 → src/**/*.rs (写, 读 implement-plan + specs + C source)
...
```

所有路径为绝对路径。每个 subagent 独立读取需要的文件。

替代方案: 通过上下文变量传递所有数据 → 上下文窗口浪费，subagent 间耦合。

### 5. 被删除文件的处理

8 个文件直接删除（git rm）:
- `c2rust_project_generator.py` — 核心硬编码转换引擎
- `c2rust_analysis.py` — body_kind 分类器
- `c2rust_repair.py` — Python 修复循环
- `c2rust_semantic_repair.py` — Python 语义修复
- `c2rust_semantic_audit.py` — 硬编码语义审计
- `c2rust_invariant_tests.py` — 硬编码不变量测试渲染
- `opencode_repair_provider.py` — V1 opencode 桥接
- `generation_agent_provider.py` — V1 LLM 桥接

相关的 test 文件同步清理。

### 6. source_analysis.py 的清理

保留: pycparser 解析、文件收集、函数签名提取、类型定义提取、include graph、macro table、test detection

移除: `SUPPORTED_BODY_KINDS` 常量、`_classify_body_kind()` 或等效逻辑、`translation_status` 字段、所有 "这个函数能不能翻译" 的判断逻辑

`tools.py parse-source` 返回的数据中:
- 保留: `files`, `source_tests`, `public_apis`, `functions` (签名、文件位置), `types`, `call_graph`
- 移除: `body_kind`, `translation_status`, `body_value` — 这些是 Python 生成器专用的中间表示

## Risks / Trade-offs

- **[Risk] Agent 生成质量不稳定** — 同样 C 代码不同运行可能生成不同 Rust。→ Mitigation: spec 作为契约约束生成质量；Phase 6 测试验证正确性；Phase 8 语义审计检测偏差
- **[Risk] subagent 上下文窗口可能不够** — 大型 C 源文件可能超出 token 限制。→ Mitigation: implement-plan 把工作拆成小批次（每批 5-8 个函数）；subagent 只读相关 C 文件片段
- **[Risk] 删除 Python 生成器后首次生成失败率可能高** — 没有兜底方案。→ Mitigation: Phase 7 repair subagent 有最多 5 轮修复（来自配置 `max_repair_rounds`）
- **[Trade-off] 删除 8 个 Python 文件失去对 V1 的回退能力** — 但 V1 本质上是比赛淘汰项，保留没有意义

## Migration Plan

1. 重写 `loopforge_runner.py` → 薄编排层
2. 清理 `source_analysis.py` → 移除 body_kind 逻辑
3. 更新 `tools.py` 的 parse-source → 移除 body_kind 相关字段
4. 更新 4 个 subagent 文件（c2r-05/06/07/08）
5. 更新 SKILL.md
6. 删除 8 个硬编码 Python 文件及其测试
7. 端到端测试: 用 FlashDB 作为测试 C 项目，验证完整 V2 管道
8. 验证 `result/output.md` 和 `result/issues/00-summary.md` 输出符合预期

## Open Questions

- `loopforge_runner.py` 重写后是否还需要作为 Python 脚本存在？还是完全变成 Agent 指令？（当前决定: 保留为 Python 脚本，但只做数据准备 + 输出上下文包）
- Phase 5 subagent 是否需要 pycparser 的 AST 输出帮助理解 C 代码？还是直接读原始 `.c` 文件？（当前决定: subagent 直接读原始 C 文件，LLM 对 C 语法的理解比 pycparser 更好）
