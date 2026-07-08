# LoopForge Consistency Check Driver

这是一个面向设计与实现一致性校验与受限修复的无人值守驱动工程。它以**标准提交包**作为外部输入模型，要求目标项目按固定比赛格式接入，而不是让框架去适配任意仓库结构。默认运行在 `consistency-check` / `repair-and-verify` 基线上，优先对齐 `README.md + design-docs/` 验收基线、修复 `code/`，并用黑盒验证收敛最终结论。

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
                     Agent（做判断）
                          │
      ┌───────────────────┼───────────────────┐
      ▼                   ▼                   ▼
  OpenSpec            SuperPower          Work Assets
  产物框架             权限边界            contract / profiles / runtime
      │                   │                   │
      └───────────────────┼───────────────────┘
                          │
                          ▼
            ┌──────────────────────────┐
            │ tools.py（原始数据层）    │
            │ scan-design               │
            │ scan-code                 │
            │ extract-implementation    │
            │ build-traceability        │
            │ run-verification          │
            │ write-report              │
            └──────────────────────────┘
```

- **Agent** 负责理解、判断、分流、修复决策与验收。
- **tools.py** 只返回原始数据，不做 pass/fail；修复与 verdict 由 workflow 契约决定。
- **OpenSpec** 管理 proposal → design → specs → tasks 的变更工件。
- **SuperPower** 和 **profiles** 定义受限可写边界、分阶段执行和文件交接约束。

## 默认运行方式

```bash
SUBMISSION_ROOT="/path/to/submission" bash work/scripts/run.sh --run
```

默认配置会使用：

- `task.mode: consistency-check`
- `execution.strategy: repair-and-verify`
- 标准提交包作为任务输入
- `work/profiles/examples/default-java-consistency.yaml` 作为默认 profile

最小 runtime 闭环命令示例：

```bash
python work/runtime/tools.py scan-design \
  --design-root "$SUBMISSION_ROOT/design-docs" \
  --submission-readme "$SUBMISSION_ROOT/README.md" \
  --output logs/trace/consistency/01-acceptance-baseline.json

python work/runtime/tools.py scan-code \
  --source-root "$SUBMISSION_ROOT/code" \
  --output logs/trace/consistency/02-source-inventory.json \
  --selection-output logs/trace/consistency/02-adapter-selection.json

python work/runtime/tools.py run-verification \
  --project-dir "$SUBMISSION_ROOT" \
  --submission-root "$SUBMISSION_ROOT" \
  --profile work/profiles/examples/default-java-consistency.yaml \
  --output logs/trace/consistency/09-verification-results.json

python work/runtime/tools.py write-report \
  --result-dir result \
  --trace-root logs/trace/consistency \
  --trace-dir logs/trace \
  --payload-output logs/trace/consistency/09-final-report-input.json
```

## 默认工件

运行结束后，优先查看：

- `result/output.md`
- `result/issues/00-summary.md`
- `logs/trace/final-report.md`
- `logs/trace/consistency/`

## 工作原则

1. 输入标准化，只接受符合约定布局的 `SUBMISSION_ROOT`。
2. `README.md` 与 `design-docs/` 共同组成验收基线，其中 `README.md` 的冻结 API、错误码和验证命令是一等输入。
3. 默认受限修复，只允许修改 `code/` 和显式声明的验证支撑资产。
4. 阶段隔离，跨阶段只通过工件交接。
5. 最终结论以修复后验证结果收敛，而不是只输出分析报告。
