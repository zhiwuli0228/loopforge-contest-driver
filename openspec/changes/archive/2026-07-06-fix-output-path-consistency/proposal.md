## Why

部分脚本和配置文件使用了 `work/logs`、`work/result` 作为输出路径前缀，而非项目标准 `logs`、`result`。这导致 smoke test 的输出写入错误位置，以及 Java profile 的 `final_report` 路径与约定不符。

## What Changes

- `work/scripts/smoke-test.sh`: `RESULT_DIR` 和 `LOG_DIR` 从 `${WORK_DIR}/result`、`${WORK_DIR}/logs` 改为 `${ROOT_DIR}/result`、`${ROOT_DIR}/logs`
- `work/profiles/examples/java-consistency-check.yaml`: `final_report` 从 `work/logs/trace/final-report.md` 改为 `logs/trace/final-report.md`
- `work/scripts/runner-negative-check.py`: 更新测试注入值和期望错误消息，与修正后的路径一致

## Capabilities

### New Capabilities

（无新增能力）

### Modified Capabilities

（无变更——`c2rust-migration-superspec` 已将 `work/`、`logs/trace/c-to-rust/`、`result/` 列为独立模式，本次仅修正实现层对标准的偏离）

## Impact

| 文件 | 影响 |
|------|------|
| `work/scripts/smoke-test.sh` | 输出位置从 `work/result/`、`work/logs/` 移至 `result/`、`logs/`（仓库根目录） |
| `work/profiles/examples/java-consistency-check.yaml` | `final_report` 路径修正 |
| `work/scripts/runner-negative-check.py` | 测试数据与期望值更新 |
