## Context

当前 `work/runtime/` 下有 20+ Python 模块，各自有不同的接口形态：
- 部分有 CLI（`check_unsafe_ratio.py`、`loopforge_runner.py`）
- 部分是纯库（`source_analysis.py`、`c2rust_semantic_audit.py`）
- 部分混合了数据生产和判断逻辑（`source_analysis.py` 输出 verification report 做 pass/fail）

V2 架构要求 Python 退化为纯工具层，不做任何判断。Agent 通过 Bash 调用 `python tools.py <command>` 获取数据，自己做所有决策。

## Goals / Non-Goals

**Goals:**
- 统一 CLI 入口：`python tools.py <command> --<args>`
- 每个子命令只返回原始数据，不做 pass/fail 判断
- 所有结构化数据输出为 JSON（stdout 或文件）
- 退出码语义：0 = 工具执行成功（数据已产出），1 = 工具自身错误（参数错误、依赖缺失）
- 零项目定制，零硬编码路径

**Non-Goals:**
- 不重写现有模块的内部逻辑，只包装它们
- 不实现 Agent 编排逻辑（那是 SKILL.md 的职责）
- 不做跨平台兼容（仅 Linux/WSL）
- 不提供交互式输入模式

## Decisions

### D1: 使用 argparse 子命令模式

**选择**: `argparse` + `add_subparsers`

**理由**: 标准库无需额外依赖；子命令模式清晰分隔 6 个功能；与现有模块的 CLI 风格一致。

**替代方案**: `click` — 功能更强但引入额外依赖；`typer` — 同理。比赛要求最小依赖。

### D2: 包装现有模块而非重写

**选择**: `tools.py` 作为薄包装层，调用现有 `work/runtime/` 下的库函数。

**理由**: 现有模块（`source_analysis.py`、`check_unsafe_ratio.py` 等）已经实现了核心逻辑。重写增加风险和工作量。只需剥离判断逻辑，保留数据生产部分。

**具体映射**:
| 子命令 | 内部调用 | 改造点 |
|--------|---------|--------|
| `parse-source` | `source_analysis.py` | 移除 `analysis-verification.json` 的 pass/fail |
| `run-verification` | `subprocess.run` | 直接透传，无需现有模块 |
| `check-unsafe` | `check_unsafe_ratio.py` | 移除 `--max-ratio` 判断和 exit(1) |
| `fault-injection` | `test_migration_validation.py` | 移除 14 项复合判断，只返回原始 JSON |
| `neutrality-audit` | `linux_acceptance.py` 中的审计逻辑 | 提取扫描逻辑，移除 gate 判断 |
| `write-report` | 新实现 | 纯格式化写入 |

### D3: JSON 输出约定

**选择**: 所有子命令的结构化数据输出到 stdout 的 JSON；文件类输出通过 `--output` 指定路径。

**理由**: Agent 可以直接 `python tools.py <cmd> | jq` 获取数据。文件输出用于大型 artifact（如 source-inventory.json）。

**格式**:
```json
{
  "ok": true,
  "command": "parse-source",
  "data": { ... }
}
```
`ok` 只表示工具执行是否成功，不代表数据内容的判断。

### D4: 工作目录约定

**选择**: 所有子命令接受 `--work-dir` 参数，默认为 `work/`。

**理由**: 避免硬编码路径。Agent 在调用时指定工作目录。

## Risks / Trade-offs

- **[风险] 现有模块的判断逻辑剥离不完全** → 每个子命令实现后需人工审查，确保无 pass/fail 语义泄漏
- **[风险] 部分模块耦合较深**（如 `test_migration_validation.py` 内部调用 cargo）→ `run-verification` 子命令直接用 `subprocess` 绕过，不依赖现有模块
- **[权衡] 薄包装 vs 重写** — 包装更快但可能保留不必要的依赖；后续 Change 可以逐步精简
