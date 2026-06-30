# LoopForge Contest Driver

LoopForge Contest Driver 是一个面向无人值守执行和自动化评测的通用 **C/C++ 到 Rust 迁移 Harness**。它以待迁移项目目录 `SOURCE_ROOT` 为运行输入，从源码、测试和项目 README 中恢复跨文件上下文，生成可构建、可测试的 Rust 工程，并通过编译自愈、测试迁移、语义审计和质量门禁验证迁移结果。

该 Harness 关注的不是某个固定代码库，而是一类可复用的系统级迁移问题：在维持模块关系、API 行为和业务语义的前提下，将已有 C/C++ 工程渐进式重构为 Rust 工程。仓库中的 `work/code/README.md` 是题目背景和能力约束的参考资料，不是待迁移源码目录，也不应被当作某个具体项目的运行配置。

> 当前仓库中真正接通的执行模式是 `migration`（C/C++ → Rust）。`work/rules/loopforge/modes/` 和 `work/profiles/templates/` 中还包含一致性检查、缺陷修复、功能开发、技能生成等规则模板，它们是扩展资产，不代表当前 runner 已实现对应执行链路。

## 核心能力

- **输入项目自动发现**：支持传入 C/C++ 项目本身，也支持传入其上层容器；根据 README 和实际翻译单元定位唯一项目根目录，不依赖固定的 `src/`、`source/`、`test/` 目录名。
- **README 驱动**：从源项目 README 获取项目名称、约束和验收上下文；支持 `README.md`、`README`、`READNE.md`、`readme.md`、`Readme.md`。
- **跨文件深度分析**：分析头文件、实现文件、宏与类型定义、模块依赖、函数调用、共享状态和测试引用，生成结构、数据模型、能力、状态转换与 API 行为映射。
- **渐进式重构上下文管理**：以源文件、API 和模块映射为迁移依据，尽量保持原工程的模块边界和调用关系，降低单点转换破坏全局行为的风险。
- **源码分析严格门禁**：代码生成前校验结构、数据模型、能力、状态、API 和测试覆盖证据；分析不完整时停止生成并输出阻塞原因。
- **Rust 工程生成**：在 `work/output/<项目名>_rust/` 下生成或刷新 Cargo 工程，不修改 `SOURCE_ROOT`。
- **测试迁移与主路径覆盖**：识别原 C/C++ 测试场景，并生成 Rust 测试或等价验证场景，通过测试映射追踪源测试与目标测试的覆盖关系。
- **迁移证据链**：输出源码清单、API 映射、迁移计划、测试映射、实现摘要及语义不变量，使生成结果能够回溯到原始实现。
- **编译—修复双向闭环**：默认执行 `cargo build`、`cargo test`，解析编译器和测试错误后进入有限轮次修复；可通过配置或环境变量接入外部修复程序。
- **语义等价性验证**：结合 API 行为、状态转换、语义不变量和测试结果审计迁移前后的行为一致性；语义门禁失败时可进入独立修复循环。
- **Rust 安全性约束**：统计生成代码中的 `unsafe` 使用比例，并根据 profile 中的阈值执行质量门禁，推动优先采用所有权、借用和安全抽象。
- **多维质量门禁**：综合判断源码分析、Cargo 工程结构、构建、测试、`unsafe` 比例、语义等价性、测试映射和修复循环结果。
- **失败可报告**：采用 fail-soft 策略。即使无法完成迁移，也会尽量生成结构化证据，并以 `BLOCKED_WITH_REPORT` 结束，而不是静默失败。
- **跨平台入口**：Linux 是正式评测环境，Windows PowerShell 用于本地开发和调试。

最终状态只有两种：

- `READY_FOR_EVALUATION`：所有必要门禁通过，可进入评测。
- `BLOCKED_WITH_REPORT`：存在阻塞项，详细原因和证据已写入报告。

## 设计理念

### 1. 输入最小化

运行时只要求提供 `SOURCE_ROOT`。任务信息尽量从源项目和 README 推导，不要求使用者在每次运行前修改框架配置。

### 2. 静态规则与动态任务分离

`work/rules/`、`work/skills/`、`work/profiles/` 定义稳定的执行约束；源代码路径、项目名称、API、测试和输出工程名由运行时分析得出。`work/loopforge.config.yaml` 是框架默认配置，不是逐任务填写的表单。

### 3. 先分析、后生成

源码分析必须经过独立校验门禁。只有输入布局可解析且分析证据完整时，才进入 Rust 工程生成，避免在错误理解源码的基础上继续迁移。

### 4. 语义保持高于语法翻译

迁移目标不是逐行翻译 C/C++ 语法，而是恢复数据模型、所有权关系、状态变化、错误处理和外部 API 契约，再以符合 Rust 习惯的方式实现等价能力。是否完成迁移由构建、测试和语义门禁共同决定。

### 5. 闭环自愈而非一次性生成

代码生成只是中间阶段。Harness 将编译器和测试反馈转化为修复输入，重新验证补丁结果，并限制修复轮次，确保过程可终止、可复盘。

### 6. 证据优先

每个关键阶段都写入 JSON 或 Markdown 证据。最终结论能够回溯到源码分析、生成结果、命令执行、修复轮次和各项门禁，而不是只给出一个成功或失败状态。

### 7. 源目录只读、产物隔离

生成代码写入 `work/output/`，面向评测的结果写入根目录 `result/`，运行轨迹写入根目录 `logs/`。源项目仅作为输入，不应被运行器修改。

## 项目架构

```text
SOURCE_ROOT + 源项目 README
          │
          ▼
  scripts/run.sh | run.ps1       平台入口、环境和路径准备
          │
          ▼
  runtime/loopforge_runner.py    生命周期编排、状态汇总、报告生成
          │
          ├── 项目根目录解析与源码分析
          ├── 分析证据严格校验
          ├── Rust Cargo 工程生成
          ├── build/test 与常规修复循环
          ├── 语义审计与语义修复循环
          └── unsafe/语义/测试映射等门禁
          │
          ├───────────────┬──────────────────┐
          ▼               ▼                  ▼
 work/output/          result/             logs/
 生成的 Rust 工程      评测入口报告         完整执行证据
```

主要目录如下：

```text
.
├── README.md                       # 项目总览（本文档）
├── INSTRUCTION.md                  # Linux 官方评测说明
├── INSTRUCTION.linux.md            # Linux 环境补充说明
├── work/
│   ├── loopforge.config.yaml       # 框架、修复轮次和验证命令配置
│   ├── runtime/                    # Python 编排器、分析器、生成器和门禁
│   ├── scripts/                    # Linux/Windows 入口及冒烟、E2E 脚本
│   ├── rules/loopforge/            # 核心契约、模式规则和语言适配规则
│   ├── profiles/                   # 当前迁移 profile、模板与示例
│   ├── skills/                     # 执行代理使用的迁移和编码规范
│   ├── subagent/                   # 分阶段任务说明资产
│   ├── code/                       # Windows 本地输入区（不是正式产物）
│   └── output/                     # 生成的 Rust Cargo 工程
├── result/                         # 本次运行的评测入口结果
│   ├── output.md
│   └── issues/00-summary.md
└── logs/                           # 本次运行日志和可审计证据
    ├── interaction.md
    └── trace/
```

核心运行模块：

| 模块 | 职责 |
|---|---|
| `loopforge_runner.py` | CLI 入口、阶段编排、门禁汇总和最终报告 |
| `c_project_root_resolver.py` | 从输入目录解析真实 C/C++ 项目根目录 |
| `c2rust_analysis.py` | 源码、API、测试和语义不变量分析 |
| `source_analysis_verify_gate.py` | 生成并校验分析阶段证据 |
| `c2rust_project_generator.py` | 创建 Rust Cargo 工程和迁移实现 |
| `c2rust_repair.py` | 编译/测试失败后的有限轮次修复 |
| `c2rust_semantic_audit.py` | 语义等价性审计 |
| `c2rust_semantic_repair.py` | 语义门禁失败后的有限轮次修复 |
| `check_unsafe_ratio.py` | Rust `unsafe` 使用比例检查 |

## 执行流程

一次完整 `--run` 依次执行：

1. 解析 `SOURCE_ROOT`，定位唯一 C/C++ 项目和 README。
2. 检查运行器、规则、profile 和适配器等必要资产。
3. 分析源项目，输出源码清单及结构、数据模型、能力、状态、API 和测试映射证据。
4. 对源码分析结果执行严格校验；失败时停止代码生成并输出阻塞报告。
5. 生成 Rust Cargo 工程、API 映射、迁移计划和测试映射。
6. 执行 `cargo build`、`cargo test`；失败时进入有限轮次修复。
7. 执行语义审计；失败时进入有限轮次语义修复。
8. 汇总源码分析、构建、测试、unsafe、语义、测试映射和修复循环门禁。
9. 写入最终状态、问题摘要和完整 trace。

## 环境要求

- Python 3（当前无第三方 Python 依赖）
- Rust 工具链：`cargo`、`rustc`
- Linux：Bash
- Windows：PowerShell

建议使用 Python 3.11；Rust 版本以待迁移项目和生成工程实际要求为准。

## 快速执行

### Linux：正式评测入口

在仓库根目录执行：

```bash
SOURCE_ROOT="/absolute/path/to/source-or-input-container" \
  bash work/scripts/run.sh --run
```

在竞赛 Linux 环境中未显式设置 `SOURCE_ROOT` 时，脚本会尝试使用：

```text
/__CONTEST_PLATFORM_SOURCE_ROOT__/source
/__CONTEST_PLATFORM_SOURCE_ROOT__
```

### Windows：本地运行

```powershell
powershell -ExecutionPolicy Bypass -File work\scripts\run.ps1 `
  -SourceRoot "C:\absolute\path\to\c-project"
```

也可以使用环境变量：

```powershell
$env:SOURCE_ROOT = "C:\absolute\path\to\c-project"
powershell -ExecutionPolicy Bypass -File work\scripts\run.ps1
```

PowerShell 入口要求明确提供 `-SourceRoot` 或 `SOURCE_ROOT`；不会自动把 `work/code/` 当成有效项目执行。

### Windows：完整 E2E 调试

仓库包含面向 Windows 的端到端脚本，它会运行驱动器并对生成的 Rust 工程执行额外检查：

```powershell
powershell -ExecutionPolicy Bypass -File work\scripts\run-e2e-win.ps1 `
  -SourceRoot "C:\absolute\path\to\c-project"
```

## 直接调用 Python 入口

脚本入口最终调用：

```bash
python work/runtime/loopforge_runner.py \
  --work-dir work \
  --source-root /absolute/path/to/source \
  --result-dir result \
  --log-dir logs \
  --run
```

可用动作：

| 参数 | 行为 |
|---|---|
| `--init` | 创建目录和未运行状态的结果模板 |
| `--self-check` | 校验输入布局及运行所需静态资产 |
| `--detect` | 只解析并分析源项目，不生成 Rust 工程 |
| `--run` | 执行完整迁移、修复、验证和报告流程 |
| `--verify` | 当前实现会重新执行完整流程并返回 verification 部分 |
| `--finalize` | 读取已有编排状态，返回最终报告状态；不会重新迁移 |

Linux 包装脚本可直接透传这些动作，例如：

```bash
SOURCE_ROOT="/path/to/source" bash work/scripts/run.sh --self-check
SOURCE_ROOT="/path/to/source" bash work/scripts/run.sh --detect
```

## 配置与修复程序

主配置位于 `work/loopforge.config.yaml`，常用项包括：

- `execution.max_repair_rounds`：常规修复最大轮次。
- `execution.max_semantic_repair_rounds`：语义修复最大轮次。
- `execution.repair_provider`：外部无人值守修复程序配置。
- `verification.timeout_seconds`：单轮验证超时。
- `verification.commands.default`：验证命令，默认使用 `cargo build` 和 `cargo test`。

可通过环境变量 `LOOPFORGE_REPAIR_COMMAND` 覆盖配置中的修复程序命令。外部程序会收到修复任务 JSON 路径参数，同时可从 `LOOPFORGE_REPAIR_TASK` 读取该路径。

## 输出与排障

执行完成后，优先查看：

1. `result/output.md`：最终状态、生成工程路径和各核心门禁结果。
2. `result/issues/00-summary.md`：阻塞原因、失败门禁和建议处理动作。
3. `logs/trace/final-report.md`：完整最终报告。
4. `logs/trace/c-to-rust/06-verification-report.md`：构建、测试、修复和语义验证详情。
5. `logs/trace/c-to-rust/semantic-audit-report.md`：语义审计结果。
6. `logs/trace/run-summary.json`：适合程序消费的完整运行摘要。

生成的 Rust 工程路径不是固定值，应以 `result/output.md` 中的 `rust_project` 为准。手动复核时进入该目录执行：

```bash
cargo build --locked
cargo test --locked -- --nocapture
```

## 开发验证

运行 Python 单元测试：

```bash
python -m unittest discover -s work/runtime/tests -p "test_*.py"
```

运行平台冒烟测试：

```bash
bash work/scripts/smoke-test.sh
```

Windows：

```powershell
powershell -ExecutionPolicy Bypass -File work\scripts\smoke-test.ps1
```

更多细节见 [官方评测说明](./INSTRUCTION.md)、[设计文档](./work/docs/DESIGN.md) 和 [适配指南](./work/docs/ADAPTATION_GUIDE.md)。
