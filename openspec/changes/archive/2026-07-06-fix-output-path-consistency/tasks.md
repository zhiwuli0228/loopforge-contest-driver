## 1. smoke-test.sh 路径修正

- [x] 1.1 `work/scripts/smoke-test.sh`: `RESULT_DIR` 从 `${WORK_DIR}/result` 改为 `${ROOT_DIR}/result`
- [x] 1.2 `work/scripts/smoke-test.sh`: `LOG_DIR` 从 `${WORK_DIR}/logs` 改为 `${ROOT_DIR}/logs`

## 2. Java profile 路径修正

- [x] 2.1 `work/profiles/examples/java-consistency-check.yaml`: `final_report` 从 `work/logs/trace/final-report.md` 改为 `logs/trace/final-report.md`，对齐同级 `consistency-check.yaml`

## 3. runner-negative-check.py 测试数据修正

- [x] 3.1 `replace_once` 的 OLD_STRING（第93行）从 `final_report: "work/logs/trace/final-report.md"` 改为 `final_report: "logs/trace/final-report.md"`，与 `loopforge.config.yaml` 实际值一致
- [x] 3.2 期望错误消息（第131行）从 `outputs.final_report must resolve under work/logs/trace/` 改为 `outputs.final_report must resolve under logs/trace/`

## 4. 验证

- [x] 4.1 运行 `work/scripts/smoke-test.sh` — runner 正确写入 `result/` 和 `logs/`，但测试本身因 `run_summary.json` 在 blocked 场景下不生成而失败（已有问题）
- [x] 4.2 运行 `python work/scripts/runner-negative-check.py` — output-outside-source-root 的 mutation 步骤正确执行（replace_once 成功找到并替换），但 runner CLI 已变更为 `--self-check --run`，测试仍使用旧的 `--init --verify --finalize` 参数（已有问题）
