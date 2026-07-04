# LoopForge Contest Driver

通用 C/C++ 到 Rust 迁移 Harness，面向无人值守执行与自动化评测设计。

以预置的 `work/design/README.md` 为唯一需求契约，以只读 `SOURCE_ROOT` 为源码输入，自动完成项目发现、深度源码分析、Rust 工程生成、编译自愈、测试迁移、语义审计和质量门禁验证。

## 比赛要求满足情况

| 要求 | 实现方式 |
|------|----------|
| 跨文件深度关联上下文管理 | 7 阶段源码分析校验门禁，生成 call graph、type map、include graph，100% API 覆盖检查；增量重构支持依赖闭包边界 |
| 编译与编译自愈闭环 | 诊断分类 → repair IR → 隔离沙箱修复 → scope/test/unsafe 完整性审计，最多 5 轮自动修复 |
| 语义等价 | 语义不变量提取 → 全路径测试场景生成 → 断言扫描 + 变异测试(7 类) + 差分向量验证 |
| `SOURCE_ROOT` 只读 | 构造函数路径校验 + 生成目录校验 + 修复作用域校验 + 源树快照比对 + 完整性清单 |

## 交付件与验收标准

| 验收标准 | 强制机制 |
|----------|----------|
| 核心 C/C++ 实现完整映射到 Rust | 7 阶段源码分析校验，100% API 覆盖门禁，unsupported 函数阻塞生成 |
| 原始测试项迁移或等价覆盖 | 13 项测试校验（断言扫描 + 变异测试 + 差分向量 + cargo test 执行验证） |
| `cargo build` 成功 | SelfHealingOrchestrator 隔离沙箱修复，scope/test/unsafe 完整性审计 |
| `cargo test` 成功且测试实际执行 | `returncode == 0 AND count > 0` 双重校验 |
| 语义审计证据证明行为未被破坏 | 10 项语义检查 + 不变量提取 + 6 类故障注入(各 3 次) |
| `unsafe` 比例 < 10% | `#![forbid(unsafe_code)]` 编译器级禁止 + 运行时比例检查 |
| `SOURCE_ROOT` 运行前后不变 | 路径校验 + 快照比对 + linux_acceptance 完整性清单 |

## 快速开始

```bash
# Linux 正式评测
SOURCE_ROOT="/path/to/flashdb" bash work/scripts/run.sh --run

# 直接调用 Python 入口
python work/runtime/loopforge_runner.py \
  --work-dir work \
  --source-root /path/to/flashdb \
  --result-dir result \
  --log-dir logs \
  --run
```

`SOURCE_ROOT` 可指向 FlashDB 项目本身或包含该项目的上层目录，Harness 会根据翻译单元、构建文件、测试文件和目录结构自动定位唯一项目根目录。

## 整体架构

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        LoopForge Contest Driver                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │  OpenSpec     │    │  SuperSpec   │    │  SuperPower          │  │
│  │  产物管理     │    │  阶段编排     │    │  权限边界             │  │
│  │              │    │              │    │                      │  │
│  │ • schema DAG │    │ • 8 阶段定义  │    │ • default-deny       │  │
│  │ • 模板+指令   │    │ • 子代理绑定  │    │ • 读/写 glob 控制    │  │
│  │ • 变更追踪   │    │ • 门禁值     │    │ • 禁止操作清单       │  │
│  └──────┬───────┘    └──────┬───────┘    └──────────┬───────────┘  │
│         │                   │                       │              │
│         └───────────────────┼───────────────────────┘              │
│                             │                                      │
│                             ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Orchestrator (SKILL.md v2)                 │  │
│  │                                                              │  │
│  │  读取 SuperPower 规则 → 派发子代理 → 检查门禁 → 下一阶段    │  │
│  │  上下文大小: ~3K tokens (不携带完整工作状态)                  │  │
│  └──────────────────────────┬───────────────────────────────────┘  │
│                             │                                      │
│         ┌───────────────────┼───────────────────┐                  │
│         ▼                   ▼                   ▼                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│  │  Phase 0    │    │  Phase 1    │    │  Phase N    │            │
│  │  Preflight  │    │  Understand │    │  Finalize   │            │
│  │             │    │             │    │             │            │
│  │  ~5K ctx   │    │  ~5K ctx   │    │  ~5K ctx   │            │
│  │  自包含    │    │  自包含    │    │  自包含    │            │
│  └─────────────┘    └─────────────┘    └─────────────┘            │
│         │                   │                   │                  │
│         └───────────────────┼───────────────────┘                  │
│                             │                                      │
│                             ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Python Runtime (22 模块)                   │  │
│  │                                                              │  │
│  │  c_project_root_resolver → c2rust_analysis → verify_gate    │  │
│  │  semantic_planning → c2rust_project_generator               │  │
│  │  c2rust_repair → self_healing_loop → semantic_audit         │  │
│  │  test_migration_validation → loopforge_runner               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                             │                                      │
│         ┌───────────────────┼───────────────────┐                  │
│         ▼                   ▼                   ▼                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│  │ work/output/ │    │  result/    │    │   logs/     │            │
│  │ Rust 工程    │    │ 评测报告    │    │ 执行证据    │            │
│  └─────────────┘    └─────────────┘    └─────────────┘            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 上下文治理：子代理架构

传统单体 LLM 驱动的迁移工具面临上下文窗口膨胀问题：随着分析深入，上下文累积导致性能下降和幻觉增加。LoopForge 采用**两级上下文注入**架构解决此问题：

```text
┌─────────────────────────────────────────────────────────────────┐
│                    上下文隔离模型                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Orchestrator (SKILL.md v2)                                     │
│  ├── 上下文: ~3K tokens                                         │
│  ├── 职责: 阶段序列、门禁检查、子代理派发                        │
│  └── 不携带: 源码内容、分析结果、生成代码                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Subagent (每个阶段独立)                                 │   │
│  │  ├── 上下文: ~5-8K tokens                                │   │
│  │  ├── 读取: 自己的声明文件 + 声明的输入文件                │   │
│  │  ├── 写入: 声明的输出文件                                │   │
│  │  └── 返回: 门禁值 (PASS/BLOCKED/DEGRADED)               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  关键设计:                                                       │
│  • 子代理是自包含的 Markdown 提示文件 (~1-2K tokens)             │
│  • 上下文隔离通过文件分离实现，非运行时沙箱                      │
│  • 编排器永不持有完整工作状态                                    │
│  • 每个子代理只读取自己需要的文件                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

子代理文件示例 (`work/subagent/c2r-01-understand.md`):

```markdown
# Phase 1: Understand

## Role
Analyze SOURCE_ROOT and produce a complete source inventory.

## Inputs
- SOURCE_ROOT (read-only)
- work/design/README.md

## Outputs
- logs/trace/c-to-rust/01-source-inventory.json
- logs/trace/c-to-rust/01-source-inventory.md

## Tools
- python work/runtime/tools.py parse-source

## Gate
Return PHASE_PASS if inventory is complete, PHASE_BLOCKED otherwise.
```

## OpenSpec + SuperSpec + SuperPower：三层执行治理

LoopForge 借鉴并整合了三个互补的执行治理框架：

### OpenSpec：产物管理

OpenSpec 是一个 schema 驱动的产物管理系统，定义了产物的依赖 DAG、模板和生成指令：

```text
┌─────────────────────────────────────────────────────────────┐
│                    OpenSpec Schema (c2r-migration)           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  proposal ──→ specs ──→ design ──→ tasks ──→ implement     │
│     │          │         │          │          │            │
│     │          │         │          │          ▼            │
│     │          │         │          │     verification      │
│     │          │         │          │          │            │
│     └──────────┴─────────┴──────────┴──────────┘            │
│                                                             │
│  每个产物:                                                   │
│  • template: Markdown 模板                                  │
│  • instruction: 生成指令                                    │
│  • dependencies: 前置产物列表                               │
│                                                             │
│  CLI: openspec instructions <artifact> --change <name>      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### SuperSpec：阶段编排

SuperSpec 定义了分阶段的工作包，强制子代理执行和门禁检查：

```yaml
# work/profiles/superspec/consistency-check-stages.yaml
superspec:
  subagent_required: true
  parent_direct_execution_allowed: false
  file_handoff_required: true

stages:
  - id: "00-preflight"
    subagent: "opencode-preflight-subagent"
    input: ["INSTRUCTION.md", "loopforge.config.yaml"]
    output: "logs/trace/consistency/00-preflight-report.md"
    success_gate: "READY_FOR_DESIGN_READ"
    failure_gate: "BLOCKED_WITH_REPORT"

  - id: "01-design-read"
    subagent: "opencode-design-read-subagent"
    input: ["work/design/README.md"]
    output: "logs/trace/consistency/01-design-summary.md"
    success_gate: "READY_FOR_IMPLEMENTATION_MAPPING"
    # ... 更多阶段
```

### SuperPower：权限边界

SuperPower 定义了 default-deny 的权限边界，控制每个阶段可以读/写/执行什么：

```yaml
# work/profiles/superpower/c-to-rust-migration-guards.yaml
phases:
  preflight:
    allowed_tools: []
    allowed_fs:
      read: ["SOURCE_ROOT/**", "work/design/**"]
      write: ["logs/**"]
    forbidden: ["any source modification"]

  implement:
    allowed_tools: ["run-verification"]
    allowed_fs:
      read: ["SOURCE_ROOT/**", "logs/trace/**"]
      write: ["work/output/**/*.rs", "work/output/**/Cargo.toml"]
    forbidden:
      - "modify tools.py"
      - "modify profiles/**"
      - "modify openspec/**"
      - "git operations"
```

### 三层协同

```text
┌─────────────────────────────────────────────────────────────┐
│                    三层执行治理协同                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  OpenSpec          SuperSpec           SuperPower           │
│  ────────          ─────────           ──────────           │
│  "生产什么"        "怎么编排"          "能做什么"            │
│                                                             │
│  产物 DAG    ───→  阶段流水线    ───→  权限边界              │
│  模板+指令         子代理绑定          读/写/执行控制        │
│  变更追踪          门禁值             default-deny           │
│                                                             │
│  协同效果:                                                   │
│  • OpenSpec 定义产物依赖，SuperSpec 定义执行顺序             │
│  • SuperPower 确保每个阶段只能访问声明的资源                 │
│  • 即使子代理产生幻想，SuperPower 的 YAML 定义硬边界         │
│  • 编排器在派发前强制检查权限                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Rust 编码技能：可插拔的专业能力

LoopForge 的技能系统将领域专业知识封装为可插拔模块：

### 技能架构

```text
┌─────────────────────────────────────────────────────────────┐
│                    技能系统架构                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  c-to-rust-migration/SKILL.md (v1, 单体)            │   │
│  │  └── 7 步内联执行: 源码清单→API映射→计划→生成→     │   │
│  │      测试迁移→验证→最终报告                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  c-to-rust-migration-v2/SKILL.md (v2, 编排器)       │   │
│  │  └── 11 阶段线性编排，每阶段委托给子代理文件        │   │
│  │      c2r-00-preflight.md → c2r-10-finalize.md       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  code-implementation/SKILL.md (通用补丁技能)         │   │
│  │  └── 读取修复计划 → 修改声明的文件 → 写入补丁摘要   │   │
│  │      声明替换合约: 相同输入/输出/门禁/写入范围       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  关键抽象: 替换合约 (Replacement Contract)                   │
│  • 相同的输入契约                                           │
│  • 相同的输出产物路径                                       │
│  • 相同的门禁值                                             │
│  • 相同的写入范围限制                                       │
│  → 更强的技能可以无缝替换，不改变编排逻辑                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 技能加载与应用

在 `work/loopforge.config.yaml` 中声明技能的加载时机：

```yaml
coding_skill:
  enabled: true
  required: true
  skill: "skills/c-to-rust-migration/SKILL.md"
  apply_at:
    - "source_inventory"
    - "api_mapping"
    - "migration_plan"
    - "rust_project_generation"
    - "test_migration"
    - "verification"
```

技能在声明的阶段自动加载，为子代理提供领域专业知识。技能文件本身是 Markdown，包含：

- **使命**：技能要完成什么
- **强制输入**：必须读取哪些文件
- **写入范围**：允许写入哪些路径
- **工作流**：分步骤的执行指令
- **完成门禁**：什么条件下返回 PASS/BLOCKED

### Rust 编码技能参考

`work/skills/code-implementation/references/` 目录包含 Rust 编码的专业参考：

| 参考文件 | 内容 |
|----------|------|
| `secure-coding.md` | 安全编码基线（输入验证、错误处理、日志、SQL、认证） |
| `rust-api-design-rules.md` | Rust API 设计规范 |
| `rust-ownership-borrowing-rules.md` | 所有权与借用规则 |
| `rust-error-handling-rules.md` | 错误处理模式 |
| `rust-unsafe-ffi-rules.md` | unsafe 和 FFI 使用规范 |
| `rust-verification-rules.md` | 验证规范 |
| `minimal-patch-rules.md` | 最小补丁原则 |

## 项目架构

```text
work/design/README.md + 只读 SOURCE_ROOT
          │
          ▼
  c_project_root_resolver.py    项目根目录自动发现（BFS + 证据评分）
          │
          ▼
  c2rust_analysis.py            深度源码分析（API/类型/宏/调用图/测试）
          │
          ▼
  source_analysis_verify_gate.py   7 阶段分析校验门禁
          │
          ▼
  semantic_planning.py          语义 IR 构建与迁移计划
          │
          ▼
  c2rust_project_generator.py   Rust 工程生成（模块/函数/测试）
          │
          ▼
  c2rust_repair.py              编译自愈闭环（诊断分类 → 修复 → 验证）
          │
          ▼
  c2rust_semantic_audit.py      语义等价审计 + 不变量测试生成
          │
          ▼
  loopforge_runner.py           生命周期编排、门禁汇总、最终报告
          │
          ├───────────────┬──────────────────┐
          ▼               ▼                  ▼
 work/output/          result/             logs/
 生成的 Rust 工程      评测入口报告         完整执行证据
```

核心模块（22 个 Python 模块，约 7600 行）：

| 模块 | 职责 |
|------|------|
| `loopforge_runner.py` | CLI 入口、阶段编排、门禁汇总和最终报告 |
| `c_project_root_resolver.py` | 从输入目录解析真实 C/C++ 项目根目录 |
| `c2rust_analysis.py` | 源码、API、测试和语义不变量分析 |
| `source_analysis_verify_gate.py` | 生成并校验分析阶段证据（7 阶段） |
| `semantic_planning.py` | 语义 IR 构建，API 契约/效果/错误/状态转换 |
| `c2rust_project_generator.py` | 创建 Rust Cargo 工程和迁移实现 |
| `c2rust_repair.py` | 编译/测试失败后的有限轮次修复 |
| `c2rust_semantic_audit.py` | 语义等价性审计 |
| `c2rust_semantic_repair.py` | 语义门禁失败后的有限轮次修复 |
| `self_healing_loop.py` | 自愈编排器（隔离沙箱 + 完整性审计） |
| `test_migration_validation.py` | 测试迁移验证（13 项检查） |
| `check_unsafe_ratio.py` | Rust `unsafe` 使用比例检查 |
| `linux_acceptance.py` | Linux 评测验收框架 |

## 通用性

LoopForge 不是为 FlashDB 定制的迁移脚本。它是一个通用的 C/C++ 到 Rust 迁移框架：

- **项目发现**：不依赖 README 或固定目录名，通过翻译单元、构建文件、测试文件和目录结构自动定位项目根目录
- **布局适配**：优先匹配 `src`/`tests` 常规布局，回退到按文件内容识别等价目录
- **语言适配**：通过 profile 和 adapter 规则支持不同迁移场景
- **修复代理**：支持外部修复程序（环境变量 `LOOPFORGE_REPAIR_COMMAND` 覆盖）

已内置的 profile 示例：

| Profile | 用途 |
|---------|------|
| `c-to-rust-migration.yaml` | C/C++ 到 Rust 迁移（本次比赛） |
| `consistency-check.yaml` | 设计与实现一致性检查 |
| `oss-defect-refactor.yaml` | 开源缺陷修复 |
| `secure-cpp-feature.yaml` | 安全 C++ 功能开发 |
| `android-to-harmonyos.yaml` | Android 到鸿蒙迁移 |

## 执行流程

一次完整 `--run` 依次执行：

1. **项目发现**：校验 `work/design/README.md`，根据源码和构建证据定位唯一 C/C++ 项目根目录
2. **资产校验**：检查运行器、规则、profile 和适配器等必要资产
3. **深度源码分析**：解析所有翻译单元，提取公共 API、类型、宏、调用图、测试用例
4. **分析校验门禁**：7 阶段独立校验（结构/数据模型/能力/状态/行为/测试覆盖/需求）
5. **语义迁移规划**：构建语义 IR，生成 API 契约、效果、错误、状态转换和不变量
6. **Rust 工程生成**：创建 Cargo 工程，迁移实现代码和测试代码
7. **编译自愈**：执行 `cargo build`/`cargo test`，失败时进入隔离沙箱修复循环
8. **语义审计**：提取语义不变量，生成并执行不变量测试
9. **质量门禁**：综合判断源码分析、构建、测试、unsafe、语义、测试映射和修复循环结果
10. **最终报告**：写入状态、问题摘要和完整 trace 证据

## 编译自愈闭环

```text
┌─────────────────────────────────────────────────────────────┐
│                    编译自愈闭环                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  cargo build/test 失败                                      │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────┐                                        │
│  │ 诊断分类         │  type_mismatch / borrow_conflict /    │
│  │ classify_        │  unresolved_symbol / return_value /   │
│  │ diagnostic()     │  state_transition / boundary_off_     │
│  │                  │  by_one / semantic_difference         │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │ Repair IR        │  结构化的修复指令                      │
│  │ normalize_       │  • 文件/行号/列号                     │
│  │ diagnostic()     │  • 错误分类                           │
│  │                  │  • 修复建议                           │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │ 隔离沙箱修复     │  复制项目到临时目录                    │
│  │ SelfHealing      │  调用修复代理                         │
│  │ Orchestrator     │  检查: 作用域/测试/unsafe 完整性      │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │ 验证回归         │  cargo build (定向)                   │
│  │                  │  cargo test (回归)                    │
│  └────────┬────────┘                                        │
│           │                                                 │
│     ┌─────┴─────┐                                           │
│     ▼           ▼                                           │
│  通过        失败 → 最多 5 轮 → BLOCKED_WITH_REPORT        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 输出与排障

执行完成后，优先查看：

| 文件 | 内容 |
|------|------|
| `result/output.md` | 最终状态、生成工程路径和各核心门禁结果 |
| `result/issues/00-summary.md` | 阻塞原因、失败门禁和建议处理动作 |
| `logs/trace/final-report.md` | 完整最终报告 |
| `logs/trace/c-to-rust/06-verification-report.md` | 构建、测试、修复和语义验证详情 |
| `logs/trace/c-to-rust/semantic-audit-report.md` | 语义审计结果 |
| `logs/trace/run-summary.json` | 适合程序消费的完整运行摘要 |

最终状态只有两种：

- `READY_FOR_EVALUATION`：所有必要门禁通过，可进入评测
- `BLOCKED_WITH_REPORT`：存在阻塞项，详细原因和证据已写入报告

## 证据链

每个关键阶段都写入 JSON 或 Markdown 证据，最终结论能够回溯到源码分析、生成结果、命令执行、修复轮次和各项门禁：

```text
logs/trace/c-to-rust/
├── 00-input-layout-resolution.json    # 输入布局解析
├── 01-source-inventory.md/json        # 源码清单
├── 01a-structure-map.json             # 结构映射
├── 01b-data-model-map.json            # 数据模型映射
├── 01c-capability-map.json            # 能力映射
├── 01d-state-transition-map.json      # 状态转换映射
├── 01e-api-behavior-map.json          # API 行为映射
├── 01f-test-coverage-map.json         # 测试覆盖映射
├── 02-api-mapping.md/json             # API 映射
├── 03-migration-plan.md/json          # 迁移计划
├── 04-test-mapping.md/json            # 测试映射
├── 05-migration-summary.md            # 实现摘要
├── 06-verification-report.md          # 验证报告
├── semantic-audit-report.md           # 语义审计
├── unsafe-ratio.json                  # unsafe 比例
├── repair-rounds.md/json              # 修复轮次
└── final-report.md                    # 最终报告
```

## 设计理念

1. **输入最小化**：运行时只要求注入 `SOURCE_ROOT`；任务信息已在提交前固化到 `work/design/README.md`
2. **静态规则与动态任务分离**：`rules/`、`skills/`、`profiles/` 定义稳定的执行约束；源代码路径、项目名称、API、测试和输出工程名由运行时分析得出
3. **先分析、后生成**：源码分析必须经过独立校验门禁，只有输入布局可解析且分析证据完整时才进入 Rust 工程生成
4. **语义保持高于语法翻译**：迁移目标不是逐行翻译 C 语法，而是恢复数据模型、所有权关系、状态变化、错误处理和外部 API 契约
5. **闭环自愈而非一次性生成**：编译器和测试反馈转化为修复输入，重新验证补丁结果，限制修复轮次确保过程可终止
6. **证据优先**：每个关键阶段都写入证据，最终结论能够回溯到源码分析、生成结果、命令执行和各项门禁
7. **源目录只读、产物隔离**：生成代码写入 `work/output/`，评测结果写入 `result/`，运行轨迹写入 `logs/`

## 环境要求

- Python 3（无第三方 Python 依赖）
- Rust 工具链：`cargo`、`rustc`
- Bash

## 开发验证

```bash
# Python 单元测试
python -m unittest discover -s work/runtime/tests -p "test_*.py"

# 平台冒烟测试
bash work/scripts/smoke-test.sh
```
