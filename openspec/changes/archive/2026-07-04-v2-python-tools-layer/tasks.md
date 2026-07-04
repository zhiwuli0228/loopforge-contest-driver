## 1. CLI 骨架

- [x] 1.1 创建 `work/runtime/tools.py`，实现 argparse 主框架 + 6 个子命令注册（parse-source, run-verification, check-unsafe, fault-injection, neutrality-audit, write-report），统一 JSON 输出格式 `{"ok": bool, "command": str, "data": {...}}`
- [x] 1.2 实现统一错误处理：参数校验失败 → `{"ok": false, "error": "..."}` + exit 1；内部异常捕获 → 同格式

## 2. parse-source 子命令

- [x] 2.1 包装 `source_analysis.py` 的解析逻辑，接受 `--source-root` 和 `--work-dir`，输出 source-inventory JSON
- [x] 2.2 移除 `analysis-verification.json` 的 pass/fail 判断逻辑，只返回原始数据
- [x] 2.3 支持 `--output` 参数将结果写入文件

## 3. run-verification 子命令

- [x] 3.1 实现 `subprocess.run` 包装，接受 `--project-dir`、`--commands`（JSON 数组）、`--timeout`
- [x] 3.2 返回每个命令的 `exit_code`、`stdout`、`stderr`、`timed_out` 字段；不解释 exit code 含义

## 4. check-unsafe 子命令

- [x] 4.1 包装 `check_unsafe_ratio.py` 的扫描逻辑，接受 `--project-dir`，返回 `ratio`、`unsafe_lines`、`total_code_lines`、`per_file`
- [x] 4.2 移除 `--max-ratio` 阈值判断和 exit(1) 语义，只返回数值
- [x] 4.3 支持 `--output` 参数

## 5. fault-injection 子命令

- [x] 5.1 包装 `test_migration_validation.py` 的故障注入逻辑，接受 `--project-dir`、`--trace-dir`、`--mutations`
- [x] 5.2 移除 14 项复合 pass/fail 判断，只返回原始 test_results 和 mutations 数据

## 6. neutrality-audit 子命令

- [x] 6.1 提取 `linux_acceptance.py` 中的审计扫描逻辑，接受 `--paths`（JSON 数组，支持 glob）、`--forbidden-terms`（JSON 数组）
- [x] 6.2 返回 hits 列表（file, line, term, context），不做 gate 判断

## 7. write-report 子命令

- [x] 7.1 实现 `--result-dir`、`--data`（JSON 字符串）或 stdin 输入，格式化写入 markdown 报告
- [x] 7.2 支持 `--template` 自定义模板；无参数时使用内置默认模板

## 8. 集成验证

- [x] 8.1 对每个子命令运行 smoke test，验证 JSON 输出格式和退出码
- [x] 8.2 验证 `tools.py --help` 输出完整命令列表
