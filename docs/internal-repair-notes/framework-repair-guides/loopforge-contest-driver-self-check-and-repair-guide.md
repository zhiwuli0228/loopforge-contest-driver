# loopforge-contest-driver 自检与不通过后修复指南

> 适用对象：Codex / opencode / 维护者  
> 适用阶段：完成一轮规则自检修复后，用于再次自检；若自检不通过，则按本文定向修复。  
> 修复边界：本轮只修框架入口、需求输入模型、脚本调用、结果日志、自检闭环与文档一致性；不扩展 C2Rust 业务转换能力，不重写 FlashDB 转换策略。

---

## 1. 目标结论

当前项目应收敛为：

```text
SOURCE_ROOT + 源码 README 驱动的快速需求开发执行器
```

而不是：

```text
人工填写 loopforge.config.yaml 的通用配置驱动平台
```

最终评委、平台 Agent 或人工复现者应能完成：

```text
阅读 README.md
-> 按 INSTRUCTION.md 准备环境
-> 传入 SOURCE_ROOT 或让工具使用默认路径
-> 执行 work/scripts/run.sh 或 work/scripts/run.ps1
-> 查看 result/output.md、result/issues/00-summary.md、logs/trace/
```

---

## 2. 本轮修复边界

### 2.1 必须修复

1. 根目录 `README.md`、`INSTRUCTION.md`、`SUBMISSION.md` 与当前模型一致。
2. `SOURCE_ROOT` 是唯一外部源码输入。
3. 需求、约束、验收信息默认从 `SOURCE_ROOT/README*` 读取。
4. `work/loopforge.config.yaml` 不得要求人工填写任务名、目标、语言、验证命令。
5. Linux / Windows 入口脚本统一调用 `work/scripts/run.*`。
6. `bootstrap.*` 只能转调 `run.*`，不能保留另一套 `--code-dir` 旧入口。
7. smoke-test 必须包含：
   - negative smoke：无 README 时能生成明确 blocked 报告；
   - positive smoke：有最小 README 时能识别 README 并生成正常结果。
8. 主输出统一为：
   - `result/output.md`
   - `result/issues/00-summary.md`
   - `logs/interaction.md`
   - `logs/trace/`

### 2.2 禁止越界

不得在本轮做以下事项：

1. 不实现或重写 C 到 Rust 业务转换算法。
2. 不新增复杂任务配置模型。
3. 不要求人工编辑 `work/loopforge.config.yaml` 才能运行。
4. 不把 `code/.loopforge/reports/final-report.md` 作为评委主输出。
5. 不修改平台提供的源码材料。
6. 不把修复设计文档继续堆在根目录。
