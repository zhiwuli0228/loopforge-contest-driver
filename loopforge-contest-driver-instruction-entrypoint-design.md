# loopforge-contest-driver：INSTRUCTION.md 与入口框架修正设计文档

版本：v1.0  
范围：仅修正入口文档、环境准备、源码路径传入、工具调用与结果获取协议。  
不包含：C2Rust 业务策略、FlashDB 转换规则、Rust 代码生成策略、测试迁移策略、profile/rules/skill 业务内容重写。

---

## 1. 背景与问题判断

当前项目需要优先修复的不是业务能力，而是“评委 / 平台 Agent / 人工复现者如何依据 README + INSTRUCTION.md 完成环境准备、调用工具并获取结果”的入口框架问题。

原先对 `INSTRUCTION.md` 的设计存在偏差：

1. 过多承载目录规范解释；
2. 混入业务规则、转换策略、Agent 内部执行逻辑；
3. 没有清晰说明运行环境、Python 依赖安装方式、工具调用方式；
4. 源码路径传入协议不稳定；
5. 结果与日志读取方式不够直观；
6. 部分脚本存在源码路径硬编码或占位不统一问题。

修正后的方向是：

```text
README.md        ：告诉评委这个作品是什么、怎么快速开始、从哪里进入执行。
INSTRUCTION.md   ：告诉评委 / 平台 Agent / 人工复现者如何准备环境、安装依赖、传入源码路径、调用工具、查看结果。
work/            ：存放实际可执行资产，包括脚本、runtime、skills、agents、rules、profiles 等。
result/          ：存放工具执行后的结果、自验证记录、问题摘要。
logs/            ：存放执行日志、推理过程日志、人工交互记录。
```

`INSTRUCTION.md` 不是业务说明书，也不是 skill/profile 的替代品。它是执行入口手册。

---

## 2. 设计目标

本次修正目标如下：

### 2.1 入口可复现

评委或人工复现者只需要阅读 README + INSTRUCTION.md，即可完成：

```text
准备环境 -> 安装依赖 -> 指定源码路径 -> 调用工具 -> 查看结果 -> 查看日志
```

### 2.2 Agent 可自动执行

平台 Agent 或 opencode 读取 `INSTRUCTION.md` 后，应能自动识别：

1. 需要哪些环境；
2. 使用什么命令安装 Python 依赖；
3. 源码路径应如何传入；
4. 如果用户用自然语言提供源码路径，应如何抽取；
5. 应调用哪个命令触发工具；
6. 执行完成后从哪里读取结果；
7. 失败时从哪里读取日志。

### 2.3 不承载业务数据

`INSTRUCTION.md` 中不得出现：

1. FlashDB 的业务转换细节；
2. C 到 Rust 的具体实现策略；
3. 测试迁移策略；
4. profile/rules/skill 的全文；
5. 针对某一次任务的业务输入内容；
6. 对业务源码的分析结论。

### 2.4 路径协议统一

所有脚本统一通过 `SOURCE_ROOT` 或 `--source-root` 接收源码路径。禁止在多个脚本中分散硬编码源码位置。

---

## 3. README 与 INSTRUCTION.md 的职责划分

### 3.1 README.md 职责

README 面向评委快速理解作品，应包含：

1. 项目简介；
2. 作品目标；
3. 能力概览；
4. 提交包目录概览；
5. 快速执行入口；
6. 指向 `INSTRUCTION.md` 的说明；
7. 指向 `result/output.md` 的结果说明。

README 不需要重复完整执行手册，只需要告诉评委：

```text
如需复现，请按照 INSTRUCTION.md 执行。
```

### 3.2 INSTRUCTION.md 职责

`INSTRUCTION.md` 是执行手册，应包含：

1. 运行环境要求；
2. Python 虚拟环境准备；
3. Python 依赖安装命令；
4. Rust/Cargo 等外部工具检查命令；
5. 源码路径输入规则；
6. opencode / 平台 Agent 自然语言路径抽取要求；
7. Linux 调用命令；
8. Windows 调用命令；
9. 结果文件读取位置；
10. 日志文件读取位置；
11. 失败排查信息收集方式。

### 3.3 work/ 职责

`work/` 承载可执行资产，应包含：

```text
work/
├── requirements.txt
├── scripts/
│   ├── run.sh
│   └── run.ps1
├── runtime/
│   └── ...
├── skills/
│   └── loopforge-driver/
│       └── SKILL.md
├── agents/
│   └── ...
├── subagent/
│   └── ...
├── profiles/
│   └── ...
└── rules/
    └── ...
```

本次只要求入口相关文件存在和路径引用正确，不要求重写业务内容。

---

## 4. 源码路径输入协议

源码路径是外部输入，不应写死在业务逻辑中。

### 4.1 路径输入优先级

`SOURCE_ROOT` 的解析优先级如下：

```text
优先级 1：平台调用 INSTRUCTION.md 时显式传入的源码路径
优先级 2：opencode / Agent 从自然语言输入中识别出的源码路径
优先级 3：命令行参数 --source-root 指定的路径
优先级 4：环境变量 SOURCE_ROOT 指定的路径
优先级 5：Linux 环境默认占位绝对路径
优先级 6：Windows / 本地开发默认 code 相对路径
```

说明：

- `INSTRUCTION.md` 负责告诉 Agent 如何抽取自然语言路径；
- 脚本本身不需要实现复杂 NLP；
- Agent 抽取到路径后，应通过 `SOURCE_ROOT` 或 `--source-root` 传给脚本；
- 脚本只负责处理结构化输入和默认 fallback。

### 4.2 自然语言源码路径示例

Agent 读取 `INSTRUCTION.md` 后，应能识别如下自然语言：

```text
源码在 /workspace/input/FlashDB。
请使用 /mnt/data/FlashDB 作为源码路径。
The source project is located at /contest/source/FlashDB.
源码路径是 D:\contest\FlashDB。
本地测试时源码放在 ./code。
```

识别后，Agent 应转换为：

```bash
SOURCE_ROOT="/workspace/input/FlashDB" bash work/scripts/run.sh
```

或：

```powershell
$env:SOURCE_ROOT = "D:\contest\FlashDB"
powershell -ExecutionPolicy Bypass -File work\scripts\run.ps1
```

### 4.3 Linux 默认路径

Linux 环境下如果没有任何源码路径输入，使用占位绝对路径：

```text
/__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB
```

该路径当前仅作为占位，不代表真实平台路径。后续在正式比赛环境中，可根据平台实际路径替换。

### 4.4 Windows / 本地默认路径

Windows 或本地开发环境下，如果没有任何源码路径输入，默认使用：

```text
code
```

即：

```text
<submission-root>/code
```

---

## 5. INSTRUCTION.md 推荐内容结构

`INSTRUCTION.md` 应按以下结构重写。

```md
# INSTRUCTION.md

This file is the execution guide for judges, platform Agents, opencode, and human reproducers.

It explains how to prepare the environment, install dependencies, provide the source path, run the tool, and collect results.

It does not contain business-specific task data or implementation strategy.

## 1. Runtime Requirements

Required:

- Linux with bash, or Windows with PowerShell for local development
- Python 3.11+
- pip
- Git
- Rust toolchain when the downstream workflow needs Rust build/test validation

Check commands:

```bash
python3 --version
python3 -m pip --version
bash --version
```

For Rust-related validation:

```bash
cargo --version
rustc --version
```

## 2. Python Environment Setup

Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r work/requirements.txt
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r work\requirements.txt
```

If `work/requirements.txt` is empty, no third-party Python dependency is required.

## 3. Source Path Input

The tool requires a source project path.

The Agent should resolve the source path in this order:

1. Use the source path explicitly provided by the contest platform.
2. If the user instruction contains a natural-language source path, extract that path.
3. If `--source-root` is provided, use it.
4. If `SOURCE_ROOT` is set, use it.
5. On Linux, fallback to `/__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB`.
6. On Windows or local development, fallback to `code`.

When the source path is resolved, pass it to the tool as `SOURCE_ROOT`.

## 4. Run the Tool

Linux:

```bash
SOURCE_ROOT="<resolved-source-path>" bash work/scripts/run.sh
```

Example:

```bash
SOURCE_ROOT="/workspace/input/FlashDB" bash work/scripts/run.sh
```

Windows PowerShell:

```powershell
$env:SOURCE_ROOT = "<resolved-source-path>"
powershell -ExecutionPolicy Bypass -File work\scripts\run.ps1
```

Example:

```powershell
$env:SOURCE_ROOT = "code"
powershell -ExecutionPolicy Bypass -File work\scripts\run.ps1
```

## 5. Result Retrieval

After execution, read:

```text
result/output.md
```

If issues are produced, read:

```text
result/issues/00-summary.md
```

Logs are stored in:

```text
logs/trace/
```

Human interaction records are stored in:

```text
logs/interaction.md
```

If the execution is fully unattended, `logs/interaction.md` may be empty.

## 6. Failure Handling

If execution fails, collect and report:

- dependency installation result
- resolved `SOURCE_ROOT`
- executed command
- failed stage
- relevant log file path
- whether partial result exists

Do not modify platform-provided source materials during failure handling.
```

---

## 6. 入口脚本设计

### 6.1 Linux 入口：work/scripts/run.sh

职责：

1. 确定提交包根目录；
2. 解析 `SOURCE_ROOT`；
3. 在 Linux 下使用占位绝对路径 fallback；
4. 创建结果和日志目录；
5. 调用真实 runtime；
6. 不写业务规则。

推荐实现骨架：

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

SOURCE_ROOT_ARG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --source-root)
      SOURCE_ROOT_ARG="${2:-}"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

if [[ -n "$SOURCE_ROOT_ARG" ]]; then
  SOURCE_ROOT="$SOURCE_ROOT_ARG"
elif [[ -z "${SOURCE_ROOT:-}" ]]; then
  case "$(uname -s 2>/dev/null || echo unknown)" in
    Linux*)
      SOURCE_ROOT="/__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB"
      ;;
    *)
      SOURCE_ROOT="code"
      ;;
  esac
fi

export SOURCE_ROOT

mkdir -p "$ROOT_DIR/result/issues"
mkdir -p "$ROOT_DIR/logs/trace"
touch "$ROOT_DIR/logs/interaction.md"

python "$ROOT_DIR/work/runtime/loopforge_runner.py" \
  --source-root "$SOURCE_ROOT" \
  --result-dir "$ROOT_DIR/result" \
  --log-dir "$ROOT_DIR/logs"
```

### 6.2 Windows 入口：work/scripts/run.ps1

职责：

1. 确定提交包根目录；
2. 解析 `SOURCE_ROOT`；
3. Windows 下使用 `code` fallback；
4. 创建结果和日志目录；
5. 调用真实 runtime；
6. 不写业务规则。

推荐实现骨架：

```powershell
param(
    [string]$SourceRoot = ""
)

$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")

if ($SourceRoot -and $SourceRoot.Trim() -ne "") {
    $env:SOURCE_ROOT = $SourceRoot
}
elseif (-not $env:SOURCE_ROOT -or $env:SOURCE_ROOT.Trim() -eq "") {
    $env:SOURCE_ROOT = "code"
}

New-Item -ItemType Directory -Force -Path (Join-Path $RootDir "result\issues") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RootDir "logs\trace") | Out-Null
New-Item -ItemType File -Force -Path (Join-Path $RootDir "logs\interaction.md") | Out-Null

python (Join-Path $RootDir "work\runtime\loopforge_runner.py") `
  --source-root $env:SOURCE_ROOT `
  --result-dir (Join-Path $RootDir "result") `
  --log-dir (Join-Path $RootDir "logs")
```

---

## 7. Python 依赖文件设计

新增或修正：

```text
work/requirements.txt
```

要求：

1. 如果当前 runtime 只使用标准库，则文件可以为空，但建议写注释：

```text
# No third-party Python dependencies are required currently.
```

2. 如果实际用到第三方库，应显式声明，例如：

```text
PyYAML>=6.0.1,<7.0
rich>=13.0,<14.0
typer>=0.12,<1.0
```

3. 不允许让评委猜测依赖；
4. 不允许依赖全局 Python 环境中偶然存在的包。

---

## 8. 需要检查和修正的路径硬编码

本次修复需要扫描以下位置：

```text
INSTRUCTION.md
README.md
work/scripts/
work/runtime/
scripts/
runtime/
config-templates/
```

重点检查：

```text
fill-by-human
/tmp/FlashDB
./FlashDB
code/FlashDB
/path/to/source
/path/to/FlashDB
```

修正原则：

1. 业务脚本不得分散硬编码源码路径；
2. 统一使用 `SOURCE_ROOT`；
3. 只有入口解析层允许出现：

```text
/__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB
code
```

4. 如果某些配置模板必须保留占位，应使用统一占位：

```text
${SOURCE_ROOT}
```

---

## 9. Codex / opencode 执行任务说明

可直接交给 Codex 或 opencode 执行以下任务：

```md
你现在只修复 loopforge-contest-driver 的 INSTRUCTION.md 和入口调用框架，不修改任何 C2Rust 业务策略、转换规则、profile 内容、skill 内容或测试迁移逻辑。

目标：

1. 重写根目录 INSTRUCTION.md，使其成为评委 / 平台 Agent / opencode / 人工复现者可执行的运行手册。

2. INSTRUCTION.md 只包含：
   - 运行环境要求；
   - Python 虚拟环境创建；
   - Python 依赖安装命令；
   - Rust/Cargo 检查命令；
   - 源码路径传入规则；
   - 自然语言源码路径抽取说明；
   - Linux 调用命令；
   - Windows PowerShell 调用命令；
   - 结果读取位置；
   - 日志读取位置；
   - 失败排查信息。

3. INSTRUCTION.md 不得包含：
   - FlashDB 业务细节；
   - C2Rust 转换策略；
   - 测试迁移策略；
   - skill/profile/rules 全文；
   - 比赛目录规范解释；
   - 某次业务输入数据。

4. 新增或修正 work/requirements.txt：
   - 明确列出 Python 依赖；
   - 如果没有第三方依赖，则保留空文件或注释说明。

5. 修正 Linux 入口脚本 work/scripts/run.sh：
   - 支持 SOURCE_ROOT 环境变量；
   - 支持 --source-root 参数；
   - SOURCE_ROOT 为空时，Linux fallback 到 /__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB；
   - 创建 result/issues、logs/trace、logs/interaction.md；
   - 调用实际 runtime；
   - 不写业务逻辑。

6. 修正 Windows 入口脚本 work/scripts/run.ps1：
   - 支持 $env:SOURCE_ROOT；
   - 支持 -SourceRoot 参数；
   - SOURCE_ROOT 为空时 fallback 到 code；
   - 创建 result/issues、logs/trace、logs/interaction.md；
   - 调用实际 runtime；
   - 不写业务逻辑。

7. 扫描并修正源码路径硬编码：
   - 禁止在业务脚本中出现 fill-by-human、/tmp/FlashDB、./FlashDB、code/FlashDB、/path/to/source；
   - 统一改为 SOURCE_ROOT 或 ${SOURCE_ROOT}。

8. 不生成 flashDB_rust，不实现业务转换，不修改业务规则。本轮只保证评委或 Agent 能完成环境准备、工具调用和结果获取。
```

---

## 10. 验收标准

### 10.1 文件存在性

```bash
test -f INSTRUCTION.md
test -f work/requirements.txt
test -f work/scripts/run.sh
test -f result/output.md || true
test -d logs/trace || true
test -f logs/interaction.md || true
```

说明：

- `result/output.md` 可以在运行后生成；
- `logs/interaction.md` 可以在运行前为空；
- 本轮重点是入口手册和调用路径可用。

### 10.2 INSTRUCTION.md 内容检查

应包含：

```text
Runtime Requirements
Python Environment Setup
Source Path Input
Run the Tool
Result Retrieval
Failure Handling
```

不应包含：

```text
FlashDB/src 具体转换策略
FlashDB/tests 具体迁移策略
unsafe 比例控制策略细节
业务 profile 全文
skill 全文
```

### 10.3 路径硬编码检查

```bash
grep -R "fill-by-human\|/tmp/FlashDB\|./FlashDB\|code/FlashDB\|/path/to/source" -n \
  INSTRUCTION.md README.md work scripts runtime config-templates 2>/dev/null
```

预期：

1. 不应在业务脚本中命中；
2. 如果命中 `INSTRUCTION.md`，只能出现在“禁止示例”或说明段落中；
3. Linux fallback 只允许是：

```text
/__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB
```

4. Windows fallback 只允许是：

```text
code
```

### 10.4 调用命令检查

Linux：

```bash
SOURCE_ROOT="code" bash work/scripts/run.sh
```

Windows：

```powershell
$env:SOURCE_ROOT = "code"
powershell -ExecutionPolicy Bypass -File work\scripts\run.ps1
```

执行失败时也应能生成或保留日志目录，方便评委定位失败原因。

---

## 11. 本轮不做事项

本轮明确不做：

1. 不实现 C2Rust 转换；
2. 不生成 `flashDB_rust`；
3. 不修改业务 profile；
4. 不修改 skill 的转换策略；
5. 不重写测试迁移逻辑；
6. 不分析 FlashDB 源码；
7. 不把题目要求复制进 `INSTRUCTION.md`；
8. 不把比赛目录规范大段复制进 `INSTRUCTION.md`。

---

## 12. 最终判断

本次修正的本质是：

```text
把 INSTRUCTION.md 从“业务说明 + 目录说明 + Agent 规则混合文档”
修正为“评委 / 平台 Agent / opencode / 人工复现者都能执行的运行手册”。
```

修正完成后，评委应能通过 README 找到 `INSTRUCTION.md`，并依据 `INSTRUCTION.md` 完成环境准备、依赖安装、源码路径传入、工具执行、结果查看和失败排查。

这一步完成后，才进入下一阶段：业务执行链路、C2Rust 转换能力、FlashDB 输出项目和测试验证的修复。
