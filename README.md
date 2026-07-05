# LoopForge Contest Driver

通用 C/C++ 到 Rust 迁移 Harness — Agent 驱动、工具层零判断、面向无人值守执行与自动化评测。

以 `work/design/README.md` 为唯一需求契约，以只读 `SOURCE_ROOT` 为源码输入，通过 11 阶段子代理流水线自动完成项目发现、源码分析、Rust 工程生成、编译自愈、测试迁移、语义审计和质量门禁验证。

## 架构概览

```
                         Agent（全部判断）
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   SKILL.md v2          SuperPower            OpenSpec
   阶段编排               权限边界              产物框架
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
              ┌───────────────────────────┐
              │   tools.py（零判断数据层）  │
              │   parse-source             │
              │   run-verification         │
              │   check-unsafe             │
              │   fault-injection           │
              │   neutrality-audit          │
              │   write-report             │
              └───────────────────────────┘
```

- **Agent** 做所有判断：理解、设计、代码生成、测试、修复、门禁
- **tools.py** 是唯一 Python CLI 入口，只返回原始数据，不做 pass/fail
- **OpenSpec** 提供 schema 驱动的产物框架（proposal → design → specs → tasks）
- **SuperSpec** 定义 11 阶段执行流水线与子代理绑定
- **SuperPower** 定义 default-deny 权限边界，控制每阶段读/写/执行范围

## 快速开始

```bash
# Linux 正式评测
SOURCE_ROOT="/path/to/flashdb" bash work/scripts/run.sh --run

# 直接调用 Python 入口（数据准备阶段）
python work/runtime/loopforge_runner.py \
  --work-dir work \
  --source-root /path/to/flashdb \
  --result-dir result \
  --log-dir logs \
  --run
```

`SOURCE_ROOT` 可指向 FlashDB 项目本身或包含该项目的上层目录，Harness 会根据翻译单元、构建文件和目录结构自动定位唯一项目根目录。

## 执行流水线（11 阶段）

| # | 阶段 | 子代理 | tools.py | 产出 |
|---|------|--------|----------|------|
| 0 | Preflight | `c2r-00-preflight.md` | — | 环境就绪确认 |
| 1 | Understand | `c2r-01-understand.md` | `parse-source` | `source-inventory.json` |
| 2 | Design | `c2r-02-design.md` | — | `design.md` |
| 3 | Spec | `c2r-03-spec.md` | — | `specs/<module>/spec.md` |
| 4 | Plan | `c2r-04-plan.md` | — | `tasks.md`, `implement-plan.md` |
| 5 | Implement | `c2r-05-implement.md` | `run-verification` | `src/**/*.rs` |
| 6 | Test | `c2r-06-test.md` | `run-verification` | `tests/**/*.rs` |
| 7 | Repair | `c2r-07-repair.md` | `run-verification` | 修复补丁 |
| 8 | Semantic Audit | `c2r-08-semantic-audit.md` | `run-verification` | 不变量测试 |
| 9 | Quality Gates | `c2r-09-quality-gates.md` | `check-unsafe`, `fault-injection`, `neutrality-audit` | 门禁汇总 |
| 10 | Finalize | `c2r-10-finalize.md` | `write-report` | `result/output.md` |

每阶段子代理返回一个门禁值：`PHASE_PASS`（继续）、`PHASE_DEGRADED`（警告后继续）、`PHASE_BLOCKED`（终止）。

## 子代理上下文隔离

编排器（SKILL.md v2）本身约 3K tokens，不携带源码内容、分析结果或生成代码。每个子代理是自包含的 Markdown 提示文件（~1-2K tokens），只读取自己声明的输入文件，写入声明的输出文件，返回约 500 tokens 的结果摘要。总上下文控制在 5-8K tokens。

```
编排器（~3K tokens）
  ├── 派发 Phase 0 子代理 → 检查门禁 → 记录产出
  ├── 派发 Phase 1 子代理 → 检查门禁 → 记录产出
  ├── ...
  └── 派发 Phase 10 子代理 → 输出最终报告
  
每个子代理：
  - 注入 prompt ~2K tokens
  - 按需读取文件内容
  - 返回 ~500 tokens 摘要
  - 文件交接为唯一跨阶段通信方式
```

## Python 运行时

14 个模块，约 4800 行：

| 模块 | 职责 |
|------|------|
| `tools.py` | 统一 CLI 入口，6 个子命令，零判断数据层 |
| `loopforge_runner.py` | CLI 入口、环境校验、数据准备、Agent 上下文包生成 |
| `source_analysis.py` | C 源码深度解析（API/类型/宏/调用图/全局状态/测试） |
| `source_analysis_verify_gate.py` | 7 阶段分析校验门禁 |
| `semantic_planning.py` | 语义 IR 构建与迁移计划 |
| `rust_project_generation.py` | Rust Cargo 工程生成 |
| `self_healing_loop.py` | 编译自愈编排（隔离沙箱 + 完整性审计） |
| `test_migration_validation.py` | 测试迁移验证、变异测试、断言扫描、中立性审计 |
| `check_unsafe_ratio.py` | Rust `unsafe` 使用比例统计 |
| `c_project_root_resolver.py` | C/C++ 项目根目录自动发现 |
| `agent_task_packet.py` | Agent 任务包与运行时路径契约 |
| `linux_acceptance.py` | Linux 评测验收框架 |
| `linux_acceptance_cli.py` | Linux 验收 CLI |
| `timeout_policy.py` | 超时策略配置 |

## tools.py 命令

```bash
# 源码解析 — 返回结构化数据
python tools.py parse-source --source-root /path --work-dir work

# 验证执行 — 运行 cargo build/test，返回原始结果
python tools.py run-verification --project-dir /path --commands '["cargo build --locked"]'

# unsafe 统计 — 返回比例数据
python tools.py check-unsafe --project-dir /path

# 故障注入 — 执行变异测试，返回注入数据
python tools.py fault-injection --project-dir /path --trace-dir logs/trace

# 中立性审计 — 扫描禁止术语
python tools.py neutrality-audit --paths '["src/**/*.rs"]' --forbidden-terms '["flashdb","FlashDB"]'

# 报告写入 — 格式化输出到 result/
python tools.py write-report --result-dir result --data '{"status":"READY_FOR_EVALUATION"}'
```

所有命令输出 `{"ok": bool, "command": str, "data": {...}}`，不做判断。

## 项目技能

| 技能 | 路径 | 用途 |
|------|------|------|
| c-to-rust-migration-v2 | `work/skills/c-to-rust-migration-v2/SKILL.md` | Agent 驱动的 11 阶段编排器 |
| code-implementation | `work/skills/code-implementation/SKILL.md` | 最小安全补丁，含 Rust 编码参考 |
| loopforge-driver | `work/skills/loopforge-driver/SKILL.md` | 竞赛入口，读取设计 README 并驱动无人值守运行 |

## 比赛要求满足情况

| 要求 | 实现方式 |
|------|----------|
| 跨文件深度关联上下文管理 | 7 阶段源码分析校验门禁，生成 call graph、type map、include graph，100% API 覆盖检查 |
| 编译与编译自愈闭环 | 诊断分类 → 隔离沙箱修复 → scope/test/unsafe 完整性审计，最多 5 轮自动修复 |
| 语义等价 | 语义不变量提取 → 全路径测试场景生成 → 断言扫描 + 变异测试(7 类) + 差分向量验证 |
| `SOURCE_ROOT` 只读 | 路径校验 + 生成目录校验 + 修复作用域校验 + 源树快照比对 + 完整性清单 |

## 交付件与验收标准

| 验收标准 | 强制机制 |
|----------|----------|
| 核心 C/C++ 实现完整映射到 Rust | 7 阶段源码分析校验，100% API 覆盖门禁 |
| 原始测试项迁移或等价覆盖 | 断言扫描 + 变异测试 + 差分向量 + cargo test 执行验证 |
| `cargo build` 成功 | SelfHealingOrchestrator 隔离沙箱修复，scope/test/unsafe 完整性审计 |
| `cargo test` 成功且测试实际执行 | `returncode == 0 AND count > 0` 双重校验 |
| 语义审计证据证明行为未被破坏 | 不变量提取 + 6 类故障注入(各 3 次) |
| `unsafe` 比例 < 10% | `#![forbid(unsafe_code)]` 编译器级禁止 + 运行时比例检查 |
| `SOURCE_ROOT` 运行前后不变 | 路径校验 + 快照比对 + linux_acceptance 完整性清单 |

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

最终状态：
- `READY_FOR_EVALUATION`：所有必要门禁通过
- `BLOCKED_WITH_REPORT`：存在阻塞项，详细原因和证据已写入报告

## 证据链

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

## 设计原则

1. **Agent 做判断，Python 做数据**：tools.py 只返回原始数据，所有 pass/fail/threshold 判断由 Agent 完成
2. **输入最小化**：运行时只要求注入 `SOURCE_ROOT`；任务信息已在提交前固化到 `work/design/README.md`
3. **上下文隔离**：每个子代理自包含，文件交接为唯一跨阶段通信方式
4. **语义保持高于语法翻译**：迁移目标不是逐行翻译 C 语法，而是恢复数据模型、所有权关系、状态变化和外部 API 契约
5. **闭环自愈而非一次性生成**：编译器反馈转化为修复输入，限制 5 轮修复确保过程可终止
6. **证据优先**：每个关键阶段写入 JSON 或 Markdown 证据，最终结论可回溯
7. **源目录只读、产物隔离**：生成代码写入 `work/output/`，评测结果写入 `result/`，运行轨迹写入 `logs/`

## 通用性

LoopForge 不是为 FlashDB 定制的迁移脚本：

- **项目发现**：通过翻译单元、构建文件、测试文件和目录结构自动定位项目根目录
- **布局适配**：优先匹配 `src`/`tests` 常规布局，回退到按文件内容识别等价目录
- **语言适配**：通过 profile 和 adapter 规则支持不同迁移场景
- **内置 profile 示例**：`c-to-rust-migration`、`consistency-check`、`oss-defect-refactor`、`secure-cpp-feature`、`android-to-harmonyos`

## 环境要求

- Python 3（依赖：pycparser，已打包在 `work/vendor/`）
- Rust 工具链：`cargo`、`rustc`
- Bash
- Node.js（可选，用于 OpenSpec CLI；不可用时自动回退到 bash 解析器）

## 开发验证

```bash
# Python 单元测试
python -m unittest discover -s work/runtime/tests -p "test_*.py"

# 平台冒烟测试
bash work/scripts/smoke-test.sh
```
