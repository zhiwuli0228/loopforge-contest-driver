## Why

当前 C-to-Rust 流程依赖简单模式匹配，无法证明任意输入 C 项目的跨文件源码、公开 API、数据类型、共享状态与测试已被完整识别。代码生成前需要一个与项目身份无关、可独立验证、遇到核心解析缺口即阻塞的源码分析门禁。

## What Changes

- 分析当前解析输入的头文件、实现文件、宏、条件编译、`typedef`、结构体、枚举和函数指针，范围完全来自布局解析结果。
- 禁止内置项目名、仓库、提交、符号前缀、宏组合、目录白名单/黑名单或固定验收计数。
- 建立声明/定义关系、include 图、调用图、类型依赖图和共享状态图，并为公开 API、核心类型和符号保留源码证据位置。
- 增加独立源码扫描器，与主分析器交叉验证核心文件、公开 API 和源测试集合。
- 生成标准化分析证据：源码清单、独立扫描、公开 API、类型、调用图、全局状态、预处理变体和验证结论。
- 引入 fail-closed 分析门禁：零计数、未解释悬空符号、核心解析失败或双扫描集合不一致时阻止进入代码生成。

## Capabilities

### New Capabilities

- `c-source-analysis`: 对任意解析后的 C 工程执行完整的跨文件源码建模并输出可追溯证据。
- `source-analysis-verification`: 通过独立扫描和非真空、完整性检查验证主分析结果，并以阻塞状态拒绝不完整分析。

### Modified Capabilities

无。

## Impact

- 主要影响 `work/runtime/c2rust_analysis.py`、`work/runtime/source_analysis_verify_gate.py`、`work/runtime/loopforge_runner.py` 及相应测试。
- 扩展 `logs/trace/c-to-rust/` 的机器可读证据契约，并影响从源码分析进入迁移规划或代码生成的门禁条件。
- 可能需要引入或封装能够可靠处理 C 预处理和 AST 的解析依赖；所有输入工程保持只读。
