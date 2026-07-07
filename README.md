# LoopForge Consistency Check Driver

这是一个面向设计与实现一致性校验的无人值守驱动工程。它以 `work/design/README.md` 作为唯一任务契约，以只读 `SOURCE_ROOT` 作为外部输入，默认运行在 `consistency-check` / `analyze-only` 基线下，优先产出证据、映射和漂移报告。

## 目标

- 对比设计文档与实现内容，识别偏差、遗漏和风险。
- 保持 `SOURCE_ROOT` 只读，不在源目录内写入任何文件。
- 将分析、映射、验证和报告分离为可追踪工件。
- 为后续受控修复或扩展阶段保留明确的文件交接。

## 架构概览

```
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
            │ parse-source (legacy)     │
            │ scan-code                 │
            │ extract-implementation    │
            │ build-traceability        │
            │ run-verification          │
            │ check-unsafe              │
            │ fault-injection            │
            │ neutrality-audit          │
            │ write-report              │
            └──────────────────────────┘
```

- **Agent** 负责理解、判断、分流和验收。
- **tools.py** 只返回原始数据，不做 pass/fail；一致性校验的权威命令面为 `scan-design`、`scan-code`、`extract-implementation`、`build-traceability`、`run-verification`、`write-report`。
- **OpenSpec** 管理 proposal → design → specs → tasks 的变更工件。
- **SuperPower** 和 **profiles** 定义默认只读、分阶段和文件交接约束。

## 默认运行方式

```bash
SOURCE_ROOT="/path/to/source" bash work/scripts/run.sh --run
```

默认配置会使用：

- `task.mode: consistency-check`
- `execution` 只读基线
- `work/design/README.md` 作为任务契约
- `work/profiles/examples/default-java-consistency.yaml` 作为默认 profile

最小 runtime 闭环命令示例：

```bash
python work/runtime/tools.py scan-design \
  --design-root work/design \
  --output logs/trace/consistency/01-design-inventory.json \
  --model-output logs/trace/consistency/03-design-model.json \
  --evidence-output logs/trace/consistency/03-design-model-evidence.json

python work/runtime/tools.py scan-code \
  --source-root "$SOURCE_ROOT" \
  --output logs/trace/consistency/02-source-inventory.json \
  --selection-output logs/trace/consistency/02-adapter-selection.json

python work/runtime/tools.py extract-implementation \
  --source-root "$SOURCE_ROOT" \
  --output logs/trace/consistency/04-implementation-model.json

python work/runtime/tools.py build-traceability \
  --design-model logs/trace/consistency/03-design-model.json \
  --implementation-model logs/trace/consistency/04-implementation-model.json \
  --output logs/trace/consistency/05-traceability-matrix.json
```

## 默认工件

运行结束后，优先查看：

- `result/output.md`
- `result/issues/00-summary.md`
- `logs/trace/final-report.md`
- `logs/trace/consistency/`

## 工作原则

1. 输入最小化，只接受 `SOURCE_ROOT`。
2. 证据优先，每个结论都应能追溯到文件。
3. 默认只读，修复或写入必须显式授权。
4. 阶段隔离，跨阶段只通过工件交接。
5. 语义优先于实现细节，先对齐契约再讨论变更。
