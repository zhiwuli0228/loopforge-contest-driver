## Why

V1 的 Python 编排器通过子进程调用 coding tool，破坏了 Agent 工具链集成。V2 要求 Agent 做所有判断，Python 退化为纯数据工具。当前 `work/runtime/` 下有 20+ 散落的 Python 模块，各自有独立入口和参数格式，无法被 Agent 通过统一 Bash 接口调用。需要一个零判断、零定制的 CLI 入口，让 Agent 能通过单条命令获取任何需要的数据。

## What Changes

- 新建 `work/runtime/tools.py` 作为唯一 CLI 入口，所有子命令通过 `python tools.py <command>` 调用
- 6 个子命令，每个只返回原始数据/pass-through 结果，不做任何 pass/fail 判断：
  - `parse-source` — 解析 C 源码目录，输出 `source-inventory.json`
  - `run-verification` — 执行 cargo build/test 等命令，透传返回码和 stdout/stderr
  - `check-unsafe` — 统计 Rust 项目中 unsafe 代码比例，返回数值
  - `fault-injection` — 运行故障注入测试，返回原始测试结果
  - `neutrality-audit` — 扫描文件中的禁用术语，返回命中列表
  - `write-report` — 格式化写入结果报告文件
- 现有散落模块的功能被整合或作为内部实现被 tools.py 调用
- **BREAKING**: V1 的编排逻辑（`loopforge_runner.py`、`self_healing_loop.py` 等）不再由 Python 驱动，由 Agent SKILL.md 接管

## Capabilities

### New Capabilities
- `source-parsing`: 解析 C/C++ 源码目录，生成结构化的源码清单（函数、类型、依赖关系）
- `verification-execution`: 透传执行构建/测试命令，返回原始结果（返回码、stdout、stderr）
- `unsafe-ratio-check`: 统计 Rust 项目中 unsafe 代码行数比例
- `fault-injection`: 运行故障注入测试并返回原始结果
- `neutrality-audit`: 扫描文件中是否存在禁用术语或项目特定硬编码
- `report-writing`: 将结构化数据格式化写入报告文件

### Modified Capabilities

（无现有 spec 需要修改）

## Impact

- **代码**: `work/runtime/tools.py` 新建，现有模块可逐步内化为 tools.py 的内部实现
- **依赖**: 仅使用 Python 标准库 + 已有的项目依赖（如 `tree-sitter`）
- **API**: Agent 通过 `python tools.py <command> --<args>` 调用，参数格式统一为 `--key value`
- **系统**: 仅 Linux/WSL，不考虑 Windows 兼容
