## Context

项目标准（`loopforge.config.yaml`、`DESIGN.md`、`HARNESS.md`、`INSTRUCTION.md`）明确规定输出路径使用仓库根目录的 `result/` 和 `logs/`。`c2rust-migration-superspec` 将 `work/`、`logs/trace/c-to-rust/`、`result/` 列为独立通用模式——`work/` 指框架工作目录（skills、profiles、runtime），而 `logs/` 和 `result/` 是输出目标。

两个文件错误地将 `logs/` 和 `result/` 嵌套在 `work/` 之下：
- `smoke-test.sh` 将输出写入 `work/result/`、`work/logs/`
- `java-consistency-check.yaml` 使用 `work/logs/trace/final-report.md`

## Goals / Non-Goals

**Goals:**
- 统一所有输出路径为 `result/` 和 `logs/`（仓库根目录）
- 确保 smoke test 输出与实际运行行为一致

**Non-Goals:**
- 不修改目录结构或创建目录的代码
- 不影响 `run.sh`、`loopforge_runner.py`、`linux_acceptance_cli.py`（已正确）
- 不修改 `test01.md`、`test02.md`（测试输出记录，非源代码）

## Decisions

### Decision 1: smoke-test.sh 路径改为 ROOT_DIR 基准

`RESULT_DIR` 和 `LOG_DIR` 直接使用 `${ROOT_DIR}/result` 和 `${ROOT_DIR}/logs`，去掉 `WORK_DIR` 中间变量。`run.sh` 已采用此模式（`${ROOT_DIR}/result`），保持一致。

### Decision 2: runner-negative-check.py 同步更新

负向测试的注入值和期望错误消息需与修正后的路径匹配。但需确认校验逻辑本身不硬编码 `work/` 前缀——先检查 `loopforge_runner.py` 中的校验逻辑再决定具体改动。

### Decision 3: java-consistency-check.yaml 对齐同级文件

`consistency-check.yaml`（非 Java 版）已正确使用 `logs/trace/final-report.md`，Java 版直接对齐即可。

## Risks / Trade-offs

- [Risk] smoke-test.sh 使用者可能依赖旧的 `work/result/` 路径 → 该脚本仅为开发阶段使用，非对外接口
- [Risk] runner-negative-check.py 改动后可能影响校验逻辑 → 先阅读完整校验逻辑上下文再实施
