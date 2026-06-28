# LoopForge Contest Driver 设计文档

## 1. 项目名称

**LoopForge Contest Driver**

副标题：

> Skill / Rule / Runner 驱动的无人值守 AI 编程闭环底座

---

## 2. 项目背景

当前 AI 编程比赛要求参赛方提供可被 OpenCode 使用的能力资产，用于在无人干预条件下完成如下任务之一或多个：

1. 根据需求实现简单功能；
2. 根据代码或需求生成测试；
3. 检测设计与实现之间的不一致；
4. 对现有代码进行有限质量修复；
5. 输出测试结果、验证报告或最终交付说明。

比赛环境存在几个关键限制：

1. 项目组明确提供 **skill 存放目录** 和 **rule 存放目录**；
2. 项目组会自动拷贝 skill/rule；
3. 工具目录是否会被拷贝不明确；
4. hook 明确不能使用；
5. 不应假设目标项目已经存在 `.opencode/`、`.loopforge/`、`harness/`、`runtime/` 等目录；
6. 目标项目大概率是存量项目；
7. 比赛强调无人值守执行，中间不能依赖人工确认；
8. 最终目标不是为某一道题写死一个 Skill，而是做一个可复用的底层驱动框架。

因此，本项目采用：

```text
Skill 作为入口
Rule 作为协议和约束
Runner Script 作为确定性驱动
.loopforge 作为状态与证据目录
OpenCode Agent 作为代码理解和修改执行者
```

---

## 3. 项目目标

### 3.1 总目标

构建一个可被 OpenCode Skill 触发的无人值守 AI 编程闭环驱动框架，使其能够在未知目标项目中自举运行目录，按阶段推进任务，执行验证，触发修复或降级，并最终输出统一报告。

项目不是单点能力，而是底层驱动：

```text
同一个 Driver
+ 不同 Mode Rule
+ 不同 Language Rule
+ 不同 Gate Profile
= 支撑多道比赛题
```

---

### 3.2 具体目标

第一版 MVD 必须实现以下能力：

1. 通过 `skills/loopforge-driver/SKILL.md` 触发；
2. 读取 `rules/loopforge/*` 规则；
3. 在目标项目中自举 `.loopforge/` 状态目录；
4. 从规则中生成或引导生成 `.loopforge/runtime/loopforge_runner.py`；
5. Runner 使用 Python 标准库实现，不依赖第三方包；
6. Runner 支持基础命令：
   - `--init`
   - `--self-check`
   - `--detect`
   - `--snapshot`
   - `--verify`
   - `--finalize`
7. 支持 Java Maven 项目识别；
8. 支持基础验证命令：
   - `./mvnw test`
   - `mvn test`
   - `mvn -q -DskipTests package`
9. 支持 fail-soft、block-late 门禁策略；
10. 无论成功、失败、降级，都尽量生成最终报告；
11. 通过 Mode 规则支持至少三种任务：
    - `spec-implementation`
    - `test-generation`
    - `spec-code-drift`

---

## 4. 非目标

第一版不实现以下能力：

1. 不依赖 Hook；
2. 不强依赖 OpenCode Custom Tool；
3. 不实现 MCP Server；
4. 不实现复杂多 Agent 并行调度；
5. 不自动创建多个 PR；
6. 不做复杂 AST 分析；
7. 不做复杂 Spec 图谱；
8. 不要求全语言覆盖；
9. 不实现企业级权限系统；
10. 不强制全量生产级门禁。

这些能力可以作为后续增强，不进入第一版 MVD。

---

## 5. 核心设计原则

### 5.1 Single Main Loop

整个任务只能有一条主工作流。

禁止：

```text
多个 Agent 各自启动独立工作流
多个 Agent 各自创建 PR
多个 Agent 各自做最终判断
多个 Agent 各自输出最终报告
```

允许：

```text
主 Loop 分配子任务
Subagent 在当前 work tree 中编码
主 Loop 统一集成
主 Loop 统一验证
主 Loop 统一 final-report
```

---

### 5.2 Single Work Tree

所有修改都发生在当前目标项目的 work tree 中。

不允许 Subagent 单独创建独立仓库、独立 PR、独立交付分支。

---

### 5.3 Controlled Coding Subagents

Subagent 可以编码，但必须受主 Loop 控制。

Subagent 必须遵守：

```text
必须有 Write Lease
只能修改 Lease 允许的文件
不能修改 forbidden files
不能独立创建 PR
不能独立进入完整 repair loop
必须输出 subagent report
```

---

### 5.4 Fail Soft, Block Late

门禁不是为了提前杀死任务，而是为了纠偏。

默认策略：

```text
普通失败 → retry / repair / degrade
严重破坏性风险 → block
最终尽量输出 final-report
```

比赛版不应因为普通测试失败直接终止。

---

### 5.5 Evidence First

任何成功结论必须有证据。

最终报告必须包含：

1. 任务模式；
2. 修改文件；
3. 验证命令；
4. 验证结果；
5. 门禁事件；
6. 降级原因；
7. Spec / Test / Implementation 追踪关系。

---

## 6. 总体架构

```text
OpenCode
  ↓
loopforge-driver Skill
  ↓
LoopForge Rules
  ↓
Bootstrap .loopforge/
  ↓
Self-Bootstrap Runner
  ↓
Runner phase command
  ↓
Agent reads phase outputs
  ↓
Agent applies code changes
  ↓
Runner verify / finalize
  ↓
Final report
```

---

## 7. 提交物目录结构

建议项目目录：

```text
loopforge-contest-driver/
├── README.md
├── RUNNING.md
├── skills/
│   └── loopforge-driver/
│       └── SKILL.md
├── rules/
│   └── loopforge/
│       ├── 00-core.md
│       ├── 01-bootstrap-runner.md
│       ├── 02-mode-selection.md
│       ├── 03-spec-normalization.md
│       ├── 04-brainstorm.md
│       ├── 05-subagent-lease.md
│       ├── 06-gate-policy-contest.md
│       ├── 07-verification-policy.md
│       ├── 08-repair-policy.md
│       ├── 09-final-report.md
│       ├── 10-java-maven.md
│       ├── 11-python-pytest.md
│       ├── 12-test-generation.md
│       ├── 13-spec-code-drift.md
│       ├── 20-runner-source-python.md
│       └── 21-tool-wrapper-optional.md
└── optional-opencode/
    └── tools/
        └── loopforge.ts
```

说明：

1. `skills/` 和 `rules/` 是比赛主提交物；
2. `optional-opencode/tools/` 是可选增强；
3. 第一版主路径不依赖 `optional-opencode/tools/`；
4. Runner 源码放在 `rules/loopforge/20-runner-source-python.md` 中，由 Skill 指挥 Agent 在目标项目中写入 `.loopforge/runtime/loopforge_runner.py`。

---

## 8. 目标项目自举目录结构

运行时在目标项目中生成：

```text
.loopforge/
├── runtime/
│   └── loopforge_runner.py
├── task/
│   └── task.md
├── spec/
│   └── normalized-spec.md
├── brainstorm/
│   └── brainstorm.md
├── plan/
│   └── execution-plan.md
├── leases/
│   └── lease-001.md
├── snapshots/
│   ├── before-apply.diff
│   ├── after-apply.diff
│   ├── before-verify.diff
│   └── after-repair.diff
├── subagents/
│   └── lease-001-report.md
├── gates/
│   └── gate-events.md
├── state/
│   └── loop-state.json
└── reports/
    └── final-report.md
```

---

## 9. 主流程状态机

LoopForge MVD 使用以下状态机：

```text
BOOTSTRAP
  ↓
MODE_SELECT
  ↓
SPEC_NORMALIZE
  ↓
BRAINSTORM
  ↓
PLAN
  ↓
LEASE_ASSIGN
  ↓
APPLY
  ↓
INTEGRATE_REVIEW
  ↓
VERIFY
  ↓
REPAIR
  ↓
FINALIZE
```

### 9.1 BOOTSTRAP

目标：

1. 创建 `.loopforge/` 目录；
2. 创建子目录；
3. 从 `20-runner-source-python.md` 提取 Runner 源码；
4. 写入 `.loopforge/runtime/loopforge_runner.py`；
5. 执行 Runner self-check；
6. 初始化 `loop-state.json`。

失败策略：

```text
如果 .loopforge 无法创建：
  尝试在项目根目录生成 LOOPFORGE_FINAL_REPORT.md

如果 Python 不可用：
  降级为 Skill/Rule-only 模式

如果 Runner 写入失败：
  降级为 Skill/Rule-only 模式
```

---

### 9.2 MODE_SELECT

根据用户任务或比赛题目选择模式。

支持模式：

```text
spec-implementation
test-generation
spec-code-drift
clean-code-repair
```

初版必须实现：

```text
spec-implementation
test-generation
spec-code-drift
```

模式选择规则：

```text
如果任务要求“实现功能” → spec-implementation
如果任务要求“生成测试” → test-generation
如果任务要求“检测设计与实现不一致” → spec-code-drift
如果任务要求“修复代码质量” → clean-code-repair
否则默认 spec-implementation
```

输出：

```text
.loopforge/task/task.md
.loopforge/state/loop-state.json
```

---

### 9.3 SPEC_NORMALIZE

目标：

把自然语言需求转换为轻量 Spec。

输出文件：

```text
.loopforge/spec/normalized-spec.md
```

格式：

```markdown
# Normalized Spec

## Mode

spec-implementation

## Requirements

- REQ-001:
- REQ-002:

## Acceptance Criteria

- AC-001:
- AC-002:

## Constraints

- C-001:

## Unknowns

- U-001:

## Confidence

HIGH / MEDIUM / LOW
```

如果无法提取结构化 Spec：

```text
使用原始任务作为 raw spec
生成最小 requirements
标记 Confidence = LOW
继续执行
```

---

### 9.4 BRAINSTORM

目标：

无人参与的需求理解和风险识别。

输出文件：

```text
.loopforge/brainstorm/brainstorm.md
```

内容：

```markdown
# Brainstorm

## Task Understanding

## Key Assumptions

## Risk Areas

## Candidate Target Files

## Candidate Test Files

## Questions Resolved by Assumption

## Suggested Execution Scope
```

Brainstorm 阶段不能修改业务代码。

---

### 9.5 PLAN

目标：

生成最小可执行计划。

输出文件：

```text
.loopforge/plan/execution-plan.md
```

内容：

```markdown
# Execution Plan

## Objective

## Selected Mode

## Project Type

## Target Files

## Test Files

## Steps

1.
2.
3.

## Verification Plan

## Rollback / Degrade Plan
```

要求：

1. 计划必须小；
2. 优先修改最少文件；
3. 不做顺手重构；
4. 不引入新依赖；
5. 不修改构建文件，除非任务明确要求；
6. 无法确定文件时，先探索，不直接大范围修改。

---

### 9.6 LEASE_ASSIGN

目标：

给 coding subagent 或主 Agent 分配写权限范围。

输出文件：

```text
.loopforge/leases/lease-001.md
```

格式：

```markdown
# Write Lease

## Lease ID

lease-001

## Assigned Task

## Allowed Files

- 

## Forbidden Files

- pom.xml
- build.gradle
- package-lock.json
- yarn.lock
- src/main/resources/**
- .github/**
- .git/**

## Max Changed Files

3

## Max Diff Lines

250

## Allowed Commands

- mvn test
- ./mvnw test
- mvn -q -DskipTests package

## Required Report

.loopforge/subagents/lease-001-report.md
```

注意：

1. Subagent 可以编码；
2. Subagent 只能在当前 work tree；
3. Subagent 不能单独创建 PR；
4. Subagent 不能独立完成最终验收；
5. Subagent 完成后必须输出 report。

---

### 9.7 APPLY

目标：

根据 Lease 完成编码、测试生成或 drift 检测。

执行前必须记录：

```bash
git diff > .loopforge/snapshots/before-apply.diff
```

执行后必须记录：

```bash
git diff > .loopforge/snapshots/after-apply.diff
```

Subagent 报告：

```text
.loopforge/subagents/lease-001-report.md
```

报告格式：

```markdown
# Subagent Report

## Lease ID

## Assigned Task

## Changed Files

## Summary

## Verification Performed

## Known Risks

## Deviations From Lease

None / List
```

---

### 9.8 INTEGRATE_REVIEW

目标：

主 Loop 统一检查所有修改。

检查项：

1. 是否修改 forbidden files；
2. 是否超过 max changed files；
3. 是否超过 max diff lines；
4. 是否存在无关修改；
5. 是否存在明显大规模重构；
6. 是否存在删除核心文件；
7. 是否存在无法归因的修改；
8. 是否与 normalized spec 对齐；
9. 是否生成了测试或测试说明；
10. 是否生成 subagent report。

失败处理：

```text
轻微超出 → WARN
修改 forbidden file → 尝试回滚
无关修改 → 尝试移除
无法回滚 → BLOCK 或 DEGRADED_DONE，视风险而定
```

---

### 9.9 VERIFY

目标：

执行项目验证。

Runner 负责执行验证命令。

Java Maven 验证顺序：

```text
1. ./mvnw test
2. mvn test
3. mvn -q -DskipTests package
```

Python Pytest 验证顺序：

```text
1. pytest
2. python -m pytest
3. python3 -m pytest
4. python -m compileall .
5. python3 -m compileall .
```

Node 验证顺序：

```text
1. npm test
2. npm run test
3. npm run build
```

Go 验证顺序：

```text
1. go test ./...
```

第一版必须实现 Java Maven，其他语言可以先保留规则说明。

验证失败不能直接 BLOCK，必须先进入 REPAIR 或 DEGRADED_DONE。

---

### 9.10 REPAIR

目标：

针对验证失败进行有限修复。

规则：

1. 最大 repair 轮数：2；
2. Repair 不能扩大需求范围；
3. Repair 不能修改 forbidden files；
4. Repair 不能引入新依赖；
5. Repair 只能针对明确失败原因；
6. Repair 后必须重新 VERIFY；
7. 超过 repair 次数后进入 `DEGRADED_DONE`。

---

### 9.11 FINALIZE

目标：

无论成功、失败、降级，都生成最终报告。

输出：

```text
.loopforge/reports/final-report.md
```

如果 `.loopforge/` 不可写，则输出：

```text
LOOPFORGE_FINAL_REPORT.md
```

最终状态：

```text
DONE
DEGRADED_DONE
PARTIAL_DONE
BLOCKED
```

---

## 10. Runner 设计

### 10.1 Runner 文件位置

目标项目运行时位置：

```text
.loopforge/runtime/loopforge_runner.py
```

源码模板位置：

```text
rules/loopforge/20-runner-source-python.md
```

`20-runner-source-python.md` 内必须包含完整 Python 源码，Agent 在 BOOTSTRAP 阶段复制出来。

---

### 10.2 Runner 技术要求

1. 使用 Python 标准库；
2. 兼容 `python` 和 `python3`；
3. 不依赖网络；
4. 不依赖第三方包；
5. 不删除业务文件；
6. 不自动提交 git；
7. 不创建 PR；
8. 只负责确定性操作；
9. 不负责复杂代码生成；
10. 不负责业务理解。

---

### 10.3 Runner 命令

Runner 至少支持：

```bash
python .loopforge/runtime/loopforge_runner.py --init
python .loopforge/runtime/loopforge_runner.py --self-check
python .loopforge/runtime/loopforge_runner.py --detect
python .loopforge/runtime/loopforge_runner.py --snapshot before-apply
python .loopforge/runtime/loopforge_runner.py --snapshot after-apply
python .loopforge/runtime/loopforge_runner.py --verify
python .loopforge/runtime/loopforge_runner.py --finalize
```

---

### 10.4 Runner 模块职责

虽然第一版可以写成单文件，但内部应按函数组织：

```python
main()
ensure_workspace()
self_check()
load_state()
save_state()
detect_project()
record_gate_event()
run_command()
snapshot_diff()
verify_project()
collect_changed_files()
generate_final_report()
```

---

### 10.5 Runner 状态文件

文件：

```text
.loopforge/state/loop-state.json
```

示例：

```json
{
  "loop_id": "loopforge-default",
  "version": "0.1.0",
  "mode": "spec-implementation",
  "project_type": "java-maven",
  "phase": "VERIFY",
  "repair_round": 0,
  "result": "RUNNING",
  "created_at": "auto",
  "updated_at": "auto"
}
```

---

### 10.6 Gate 事件文件

文件：

```text
.loopforge/gates/gate-events.md
```

格式：

```markdown
# Gate Events

| Phase | Gate | Status | Action | Reason |
|---|---|---|---|---|
| VERIFY | test | REPAIR | enter repair round 1 | mvn test failed |
```

Runner 也可以额外写：

```text
.loopforge/state/gate-events.jsonl
```

但第一版用 Markdown 即可。

---

## 11. Skill 设计

### 11.1 Skill 文件

位置：

```text
skills/loopforge-driver/SKILL.md
```

### 11.2 Skill 核心职责

Skill 是唯一入口，负责告诉 Agent：

1. 必须使用 LoopForge；
2. 必须加载核心规则；
3. 必须自举 Runner；
4. 必须按阶段执行；
5. 不允许中途询问用户；
6. 不允许使用 Hook；
7. 不允许单独创建多个 PR；
8. 必须输出 final-report。

### 11.3 Skill 必须包含的强约束

```text
Do not ask for human confirmation.
Do not use hooks.
Do not create multiple workflows.
Do not create multiple PRs.
Do not skip final report.
Do not claim success without verification evidence.
Bootstrap runner first.
Use fail-soft, block-late gate policy.
```

---

## 12. Rule Pack 设计

### 12.1 `00-core.md`

定义全局原则：

```text
Single Main Loop
Single Work Tree
Controlled Coding Subagents
Single Final Review
Single Final Report
Fail Soft, Block Late
Evidence First
```

---

### 12.2 `01-bootstrap-runner.md`

定义自举 Runner 过程：

1. 创建 `.loopforge/`；
2. 创建子目录；
3. 复制 Runner 源码；
4. 执行 self-check；
5. 初始化 state；
6. 失败时降级。

---

### 12.3 `02-mode-selection.md`

定义任务模式选择规则。

---

### 12.4 `03-spec-normalization.md`

定义 normalized spec 格式。

---

### 12.5 `04-brainstorm.md`

定义无人参与 brainstorm 输出格式。

---

### 12.6 `05-subagent-lease.md`

定义 coding subagent 的写权限租约。

---

### 12.7 `06-gate-policy-contest.md`

定义比赛版宽门禁策略：

```text
默认不提前终止
普通失败进入 retry / repair / degrade
只有不可恢复破坏性风险 BLOCK
finalize 必须执行
```

---

### 12.8 `07-verification-policy.md`

定义验证命令选择和失败处理。

---

### 12.9 `08-repair-policy.md`

定义最多 2 轮 repair。

---

### 12.10 `09-final-report.md`

定义最终报告模板。

---

### 12.11 `10-java-maven.md`

定义 Java Maven 项目识别和执行约束。

---

### 12.12 `11-python-pytest.md`

第二阶段实现，第一版可以先写规则，不必完全支持。

---

### 12.13 `12-test-generation.md`

定义测试生成模式。

---

### 12.14 `13-spec-code-drift.md`

定义设计与实现不一致检测模式。

---

### 12.15 `20-runner-source-python.md`

包含完整 Runner 源码模板。

---

### 12.16 `21-tool-wrapper-optional.md`

说明可选 OpenCode Custom Tool Wrapper 的使用方式。第一版不作为主路径。

---

## 13. 门禁设计

### 13.1 门禁状态

支持：

```text
PASS
WARN
RETRY
REPAIR
DEGRADE
BLOCK
```

### 13.2 最终状态

支持：

```text
DONE
DEGRADED_DONE
PARTIAL_DONE
BLOCKED
```

### 13.3 允许 BLOCK 的情况

比赛版只允许以下情况硬阻断：

1. 目标项目不可读；
2. 目标项目不可写且任务必须修改文件；
3. Git/work tree 状态不可恢复；
4. 出现危险命令或破坏性操作；
5. 关键文件被删除且无法恢复；
6. Runner 和 Skill-only 模式均无法生成任何报告。

其他情况都应尽量进入：

```text
RETRY
REPAIR
DEGRADE
FINALIZE
```

---

## 14. 多题目复用设计

### 14.1 spec-implementation

用于根据需求实现功能。

流程：

```text
task
→ normalized spec
→ brainstorm
→ execution plan
→ write lease
→ apply implementation
→ generate/update tests
→ verify
→ final report
```

---

### 14.2 test-generation

用于输出相关测试。

流程：

```text
task/code
→ identify target behavior
→ find existing test style
→ generate test plan
→ apply tests
→ verify
→ final report
```

---

### 14.3 spec-code-drift

用于检测设计与实现不一致。

流程：

```text
spec
→ normalize requirements
→ inspect implementation
→ build traceability matrix
→ identify missing behavior / test gap
→ optional test generation
→ final report
```

---

## 15. Optional OpenCode Custom Tool

如果比赛方允许提交 `.opencode/tools/`，可以增加：

```text
optional-opencode/tools/loopforge.ts
```

职责：

1. 调用 `.loopforge/runtime/loopforge_runner.py`；
2. 返回 Runner 输出；
3. 不承载核心逻辑；
4. 不替代 Runner；
5. 不作为第一版主路径。

设计原则：

```text
Runner 是核心
Custom Tool 是 Wrapper
Skill 是入口
Rule 是协议
```

---

## 16. README.md 内容要求

README 必须说明：

1. 项目名称；
2. 背景；
3. 为什么不用 Hook；
4. 为什么 Runner-first；
5. 目录结构；
6. 支持的任务模式；
7. 执行流程；
8. 比赛运行方式；
9. 失败和降级策略；
10. 最终报告位置；
11. 已知限制。

---

## 17. RUNNING.md 内容要求

RUNNING 必须给比赛方说明：

```markdown
# Running LoopForge

## Required Copy

Copy:

- skills/loopforge-driver/
- rules/loopforge/

## Start

Start OpenCode in the target project root.

Ask OpenCode to use loopforge-driver skill for the contest task.

## Expected Runtime Artifacts

.loopforge/
.loopforge/reports/final-report.md

## No Hook Required

LoopForge does not require hooks.

## Optional Tool Mode

If project-local OpenCode tools are supported, optional-opencode/tools/loopforge.ts may be copied to .opencode/tools/loopforge.ts.
```

---

## 18. 实现里程碑

### V0.1：目录骨架与文档

交付：

```text
README.md
RUNNING.md
skills/loopforge-driver/SKILL.md
rules/loopforge/*.md 初版
```

验收：

1. 目录结构正确；
2. Skill 入口清晰；
3. Rule 分层清晰；
4. 不依赖 Tool；
5. 不依赖 Hook。

---

### V0.2：Runner 自举

交付：

```text
rules/loopforge/20-runner-source-python.md
```

Runner 支持：

```text
--init
--self-check
```

验收：

1. Agent 能将 Runner 复制到 `.loopforge/runtime/loopforge_runner.py`；
2. Runner 能创建 `.loopforge` 子目录；
3. self-check 通过；
4. 失败时能写 final report 或降级说明。

---

### V0.3：项目识别与快照

Runner 支持：

```text
--detect
--snapshot <name>
```

验收：

1. 能识别 Java Maven；
2. 能识别 Python 项目；
3. 能保存 git diff；
4. 无 git 时不崩溃，记录 warning。

---

### V0.4：Java Maven 验证

Runner 支持：

```text
--verify
```

验收：

1. 优先执行 `./mvnw test`；
2. 其次执行 `mvn test`；
3. 再执行 `mvn -q -DskipTests package`；
4. 命令失败不直接中断；
5. 写入 gate events；
6. 能生成验证摘要。

---

### V0.5：Final Report

Runner 支持：

```text
--finalize
```

验收：

1. 生成 `.loopforge/reports/final-report.md`；
2. 包含 result；
3. 包含 mode；
4. 包含 project type；
5. 包含 changed files；
6. 包含 verification；
7. 包含 gate events；
8. 包含 risks / degradation。

---

### V0.6：spec-implementation 跑通

验收：

1. 能根据任务生成 normalized spec；
2. 能生成 brainstorm；
3. 能生成 execution plan；
4. 能生成 write lease；
5. Agent 能按 lease 修改代码；
6. Runner 能 verify；
7. Runner 能 finalize；
8. 最终报告可读。

---

### V0.7：test-generation 模式

验收：

1. 同一个 Skill；
2. 同一个 Runner；
3. 只切换 Rule Mode；
4. 能生成测试；
5. 能 verify；
6. 能 final-report。

---

### V0.8：spec-code-drift 模式

验收：

1. 能读取 spec；
2. 能输出 traceability matrix；
3. 能识别至少一种缺失实现或缺失测试；
4. 能生成 drift section；
5. 能 final-report。

---

## 19. 验收标准

最终项目至少满足：

1. 不依赖 Hook；
2. 不强依赖 Custom Tool；
3. 能通过 Skill/Rule 自举 Runner；
4. Runner 使用 Python 标准库；
5. 能在目标项目生成 `.loopforge/`；
6. 能生成 final-report；
7. 能识别 Java Maven；
8. 能执行 Maven 验证；
9. 验证失败不直接终止；
10. Repair 失败后能 DEGRADED_DONE；
11. 支持至少两个任务模式；
12. README 和 RUNNING 可让比赛方理解如何运行。

---

## 20. Codex 实现要求

实现时请遵守：

1. 先实现 MVD，不要一次性做大；
2. 优先保证目录和文件稳定；
3. Runner 必须单文件、标准库、可移植；
4. Skill 不要写得过长；
5. Rule 文件职责要清晰；
6. 不要引入第三方依赖；
7. 不要依赖网络；
8. 不要自动 git commit；
9. 不要自动 PR；
10. 不要使用 Hook；
11. 不要把 Custom Tool 作为主路径；
12. 每个版本完成后，输出变更说明和本地验证命令。

---

## 21. 推荐第一步实现任务

请 Codex 先完成以下任务：

```text
实现 LoopForge Contest Driver V0.1-V0.3：
1. 创建完整目录结构；
2. 编写 README.md；
3. 编写 RUNNING.md；
4. 编写 skills/loopforge-driver/SKILL.md；
5. 编写 rules/loopforge/00-core.md 到 09-final-report.md；
6. 编写 rules/loopforge/20-runner-source-python.md；
7. Runner 支持 --init、--self-check、--detect、--snapshot；
8. Runner 使用 Python 标准库；
9. 不实现复杂业务逻辑；
10. 输出本地验证步骤。
```

第一阶段完成后，再进入 Java Maven verify 和 final-report 实现。

---

## 22. 项目最终定位

LoopForge Contest Driver 不是单个题目的 Skill，而是一个底层协议驱动框架：

```text
Skill 负责触发
Rule 负责约束
Runner 负责确定性推进
Agent 负责理解和修改代码
Gate 负责纠偏
Report 负责交付证据
```

最终目标：

> 在比赛限制下，通过 Skill / Rule / Runner 的组合，构建一个可自举、可复用、可降级、可验证的无人值守 AI 编程闭环底座。
