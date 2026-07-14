# LoopForge Consistency Check Driver

这是一个面向设计与实现一致性校验与受限修复的无人值守驱动工程。它以**标准提交包**作为外部输入模型，要求目标项目按固定比赛格式接入，而不是让框架去适配任意仓库结构。默认运行在 `consistency-check` / `repair-and-verify` 基线上，优先对齐 `README.md + design-docs/` 验收基线、修复 `code/`，最后再用公开黑盒验证收敛最终结论，而不是以黑盒测试替代前置分析。

## 目标

- 对比标准提交包中的设计资产与实现内容，识别偏差、遗漏和风险。
- 在默认 `repair-and-verify` 模式下只允许修改 `SUBMISSION_ROOT/code/**` 和显式声明的验证支撑资产。
- 将基线提取、差异建模、修复执行、验证和报告分离为可追踪工件。
- 输出面向比赛交付的最终 verdict，而不是只停留在漂移报告。

## 标准提交包

外部输入根记为 `SUBMISSION_ROOT`。标准格式为：

```text
SUBMISSION_ROOT/
├── README.md
├── design-docs/
├── code/
├── test-cases/
└── contest.meta.yaml   # optional
```

职责划分：

- `README.md`：比赛说明、冻结契约、验证命令、修改边界。
- `design-docs/`：业务设计真相源。
- `code/`：业务实现区，也是 repair-and-verify 模式默认允许修改的区域。
- `test-cases/`：黑盒验证资产，默认只读。
- `contest.meta.yaml`：可选结构化补充，用于减少 README 解析歧义。

## 架构概览

```text
                        ┌──────────────────────────────────┐
                        │         INSTRUCTION.md           │
                        │       (权威执行入口)              │
                        └──────────────┬───────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              ▼                        ▼                        ▼
    ┌─────────────────┐    ┌─────────────────────┐    ┌──────────────────┐
    │   Phase 1 (Python)  │    │   Phase 2 (Agent)    │    │  Phase 3 (Python) │
    │   结构性扫描         │    │   业务级分析+修复     │    │   验证/重试/报告   │
    │                     │    │                      │    │                    │
    │  dic-00 基线提取    │    │  2a. 逐模块分析(并行) │    │  dic-05 分层验证   │
    │  dic-01 模块发现    │    │  2b. 协调器           │    │  dic-06 重试分流   │
    │                     │    │  2c. 聚合(并行)       │    │  dic-07 最终报告   │
    │  → analysis-        │    │  2d. 合并器           │    │                    │
    │    context.json     │    │  2e. 逐批修复(并行)   │    │  → final-report.md │
    └─────────┬───────────┘    │  2f. 汇总结果         │    └─────────┬──────────┘
              │                │                      │              │
              │                │  → agent-work-       │              │
              │                │    results.json      │              │
              │                └──────────┬───────────┘              │
              │                           │                          │
              └───────────────────────────┼──────────────────────────┘
                                          │
                          ┌───────────────┼───────────────┐
                          ▼               ▼               ▼
                   ┌──────────┐   ┌────────────┐   ┌──────────────┐
                   │ OpenSpec │   │  Profiles   │   │   Adapters   │
                   │ 治理/契约 │   │ 阶段/守卫    │   │  语言适配器   │
                   └──────────┘   └────────────┘   └──────────────┘
```

- **Phase 1 (Python)** — `loopforge_runner.py --run`：负责结构性扫描（基线提取、模块发现、适配器选择），产出 `analysis-context.json` 后退出 `AGENT_ANALYSIS_READY`，不执行任何业务级分析。
- **Phase 2 (Agent)** — 读取 `analysis-context.json`，按 `dic-agent-analysis.md` 的 SOP 调度子 agent 完成逐模块分析、跨模块聚合、修复批次生成和逐批修复。所有数据通过磁盘交接，主 agent 上下文使用率低于 10%。
- **Phase 3 (Python)** — `loopforge_runner.py --resume`：重新加载阶段工件，检测 Agent 产出，执行分层验证、重试分流和最终报告。如存在未处理的 follow-on 队列则返回 `AGENT_DELEGATION_READY`，可多次 `--resume` 直至收敛。
- **OpenSpec** 只管理仓库级治理与契约变更；稳定契约下的运行时修复、报告调整和业务实现应复用已有理解工件并拆成有界批次执行。
- **Profiles**（superpower / superspec）定义受限可写边界、分阶段执行和文件交接约束。
- **Adapters**（Java / Generic）提供语言感知的源码扫描、符号索引和测试检测。

## 项目结构

```text
loopforge-contest-driver/
├── INSTRUCTION.md             # 权威执行说明（Phase 1→2→3 完整流程）
├── README.md                  # 本文件 — 项目概览与架构
├── openspec/                  # OpenSpec 治理：schema、specs、templates
├── work/                      # 静态运行时资产
│   ├── loopforge.config.yaml  # 中心配置：模式、profile、执行策略
│   ├── design/                # 仓库内部设计契约
│   ├── runtime/               # Python 数据层与运行器
│   │   ├── loopforge_runner.py    # 主入口：Stage 1 / Stage 2
│   │   ├── tools.py               # CLI 工具集（scan-design / scan-code / …）
│   │   ├── design_scanner.py      # dic-00: 基线提取
│   │   ├── code_inventory.py      # dic-01: 源码清单
│   │   ├── module_discovery.py    # dic-01: 模块图构建
│   │   ├── verification_runner.py # dic-05: 分层验证
│   │   ├── repair_provider.py     # 修复执行与 follow-on 队列
│   │   ├── report_writer.py       # dic-07: 报告写入
│   │   └── tests/                 # 运行时单元测试
│   ├── skills/                # Agent 执行指引
│   │   ├── loopforge-driver/      # 仓库级编排器
│   │   ├── design-implementation-consistency/  # 阶段契约技能
│   │   └── code-implementation/   # 编码修复规则
│   ├── subagent/              # 阶段包与 SOP（dic-00 ~ dic-07）
│   ├── profiles/              # Profile 定义
│   │   ├── examples/              # 示例 profile（Java、consistency-check 等）
│   │   ├── superpower/            # 守卫策略
│   │   ├── superspec/             # 阶段定义
│   │   └── templates/             # Profile 模板
│   ├── adapters/              # 语言适配器（Java / Generic）
│   ├── scripts/               # 启动脚本与验证脚本
│   └── rules/                 # 工作流规则
├── result/                    # 评估输出（output.md, issues/）
└── logs/                      # 运行时证据（trace/, interaction.md）
```

## 默认运行方式

### 完整三阶段运行

```bash
# Phase 1 — 结构性扫描
SUBMISSION_ROOT="/path/to/submission" bash work/scripts/run.sh --run
# → 返回 AGENT_ANALYSIS_READY，写入 analysis-context.json

# Phase 2 — Agent 执行（由平台 Agent 按 dic-agent-analysis.md 调度）
# Agent 读取 analysis-context.json → 逐模块分析 → 聚合 → 修复 → agent-work-results.json

# Phase 3 — 验证与报告
SUBMISSION_ROOT="/path/to/submission" bash work/scripts/run.sh --resume
# → 验证、重试分流、最终报告
```

### 仅预检

```bash
SUBMISSION_ROOT="work/code" bash work/scripts/run.sh --self-check
```

### 底层 CLI 命令（tools.py 仍可用）

```bash
python work/runtime/tools.py scan-design \
  --design-root "$SUBMISSION_ROOT/design-docs" \
  --submission-readme "$SUBMISSION_ROOT/README.md" \
  --output logs/trace/consistency/00-design-inventory.json \
  --model-output logs/trace/consistency/00-acceptance-baseline.json \
  --emit-acceptance-baseline

python work/runtime/tools.py scan-code \
  --source-root "$SUBMISSION_ROOT/code" \
  --output logs/trace/consistency/01-source-inventory.json \
  --selection-output logs/trace/consistency/01-adapter-selection.json

python work/runtime/tools.py run-verification \
  --project-dir "$SUBMISSION_ROOT/code" \
  --submission-root "$SUBMISSION_ROOT" \
  --profile work/profiles/examples/default-java-consistency.yaml \
  --output logs/trace/consistency/05-layered-verification.json

python work/runtime/tools.py write-report \
  --result-dir result \
  --trace-root logs/trace/consistency \
  --trace-dir logs/trace \
  --payload-output logs/trace/consistency/07-final-report-input.json
```

## 三阶段流水线详解

### Phase 1 — 结构性扫描（Python）

执行 `dic-00`（基线提取）和 `dic-01`（模块发现），产出：

| 阶段 | 工件 |
|------|------|
| dic-00 | `logs/trace/consistency/01-acceptance-baseline.json` |
| dic-01 | `logs/trace/consistency/02-source-inventory.json`、`02-adapter-selection.json`、`02-module-graph.json` |

Phase 1 同时写入 `logs/trace/consistency/analysis-context.json`（Agent 结构上下文包），然后退出 `AGENT_ANALYSIS_READY`。Python 运行时**不执行**任何业务级分析或修复。

### Phase 2 — Agent 分析与修复

Agent 按 `work/subagent/dic-agent-analysis.md` 中的 SOP 以薄编排器模式运行，所有数据通过磁盘流转，主 agent 上下文保持在 10% 以下：

1. **逐模块分析**（并行，`dic-02`）：每个模块一个子 agent，读取源码与设计文档，写紧凑 findings（每条 ≤300 字节）到 `logs/trace/consistency/module-findings/<module>.json`
2. **协调器**：一个轻量子 agent 只读 finding 元数据（计数 + 严重度），产出 `allocation-plan.json`（每聚合组 ≤80 条 findings）
3. **聚合**（并行，`dic-03`）：每组一个子 agent，聚类分配的 findings，产出 `partial-clusters-{id}.json`
4. **合并器**：一个子 agent 综合所有 partial clusters，产出 `03-module-analysis.json`、`04-issue-clusters.json`、`05-repair-batches.json`
5. **逐批修复**（并行，安全时，`dic-04`）：每批次一个子 agent，应用有界修复。收集门控令牌：`BATCH_APPLIED | BATCH_NO_CHANGES | BATCH_FAILED | BATCH_BLOCKED`
6. **汇总**：主 agent 将所有修复结果写入 `agent-work-results.json`

### Phase 3 — 验证与报告（Python）

`--resume` 重新加载 Phase 1 工件，检测 Agent 产出，执行：

| 阶段 | 内容 |
|------|------|
| dic-05 | 分层验证（构建、安装、黑盒测试）→ `05-layered-verification.json` |
| dic-06 | 重试分流（失败分类、follow-on 队列）→ `06-retry-decision.json` |
| *暂停* | 如有 follow-on 队列，返回 `AGENT_DELEGATION_READY`，不进入 dic-07 |
| Agent | 处理 follow-on 队列 → `agent-work-results-round-02.json` |
| 恢复 | 再次 `--resume` 检测 follow-on 结果，重新验证 |
| dic-07 | 最终报告（组装、定稿）→ `final-report.md` |

**Follow-on 循环**：`--resume` 可多次调用。每轮遇到验证失败时创建 follow-on 队列并返回 `AGENT_DELEGATION_READY`。流水线在验证通过或 `max_repair_rounds` 耗尽时自然终止。

## Batch Executor（外部执行器）

当环境设置 `LOOPFORGE_BATCH_EXECUTOR_COMMAND` 时，runtime 以此命令派发每个修复批次为子进程。该命令以 `SUBMISSION_ROOT` 为工作目录运行，接收以下环境变量：

- `LOOPFORGE_BATCH_REQUEST` / `LOOPFORGE_BATCH_RESPONSE`
- `LOOPFORGE_BATCH_CONTEXT` / `LOOPFORGE_BATCH_ID` / `LOOPFORGE_BATCH_INDEX`
- `LOOPFORGE_SUBMISSION_ROOT` / `LOOPFORGE_CODE_ROOT` / `LOOPFORGE_DESIGN_ROOT`
- `LOOPFORGE_TRACE_DIR`

未配置时，runtime 产出 `deferred` 执行结果，通过 `agent-work-queue.json` / `agent-work-results.json` 协议交还 Agent 处理。

## 默认工件

运行结束后，优先查看：

- `result/output.md`
- `result/issues/00-summary.md`
- `logs/trace/final-report.md`
- `logs/trace/consistency/`
- `logs/trace/consistency/verification-logs/`

其中 `logs/trace/consistency/05-layered-verification.json` 和 `07-final-report-input.json` 只保留紧凑摘要、失败摘录和证据路径；完整验证 stdout/stderr 保存在 `verification-logs/` 下，不再重复内嵌进最终 payload。

预检与诊断参考：

- `logs/trace/run-summary.json`
- `logs/trace/consistency/00-preflight-self-check.json`
- `logs/trace/consistency/00-submission-layout.json`

## OpenSpec 治理范围

OpenSpec 变更只用于治理、契约、stage graph、guard 边界和权威输入输出变化；不要求为每个 runtime 修复或业务实现批次重开一个大变更。Agent 必须区分治理范围变更（schema、stage contracts、guard policies）和有界实现批次（在声明的可写目标内的源码级修复）。仅治理范围变更需要 OpenSpec change artifacts。

## 工作原则

1. 输入标准化，只接受符合约定布局的 `SUBMISSION_ROOT`。
2. `README.md` 与 `design-docs/` 共同组成验收基线，其中 `README.md` 的冻结 API、错误码和验证命令是一等输入。
3. 默认受限修复，只允许修改 `code/` 和显式声明的验证支撑资产。
4. 阶段隔离，跨阶段只通过工件交接。
5. 先产出 acceptance baseline、module graph、implementation model、traceability 和 issue clusters，再基于这些理解工件拆分有界执行批次。
6. OpenSpec 变更只用于治理、契约、stage graph、guard 边界和权威输入输出变化；不要求为每个 runtime 修复或业务实现批次重开一个大变更。
7. 最终结论以修复后验证结果收敛，而不是只输出分析报告。
8. 公开黑盒测试用于最终验证和失败回流，不是默认的一线修复驱动。
