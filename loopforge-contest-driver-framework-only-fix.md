# loopforge-contest-driver 框架目录最小合规修复方案

> 修复边界：只修复比赛提交壳、目录归位、入口文件路径引用、占位结果/日志文件。  
> 不修复 C2Rust 业务策略，不改转换规则，不改 Rust 生成逻辑，不改验证语义。

## 1. 修复目标

当前目标不是把项目改成 FlashDB 专用业务实现，而是先让作品提交结构符合比赛平台的基础入口模型：

- 根目录保留 `INSTRUCTION.md`，作为唯一执行入口。
- 根目录新增并保留 `work/`，用于存放可运行交付件。
- 根目录新增并保留 `result/`，用于存放自验证输出。
- 根目录新增并保留 `logs/`，用于存放交互记录和推理日志。
- 原有框架资产归入 `work/`。
- 所有因目录移动导致的路径引用同步调整。
- 不新增业务规则，不重写 C2Rust 转换方案。

## 2. 目标目录结构

修复后根目录建议如下：

```text
.
├── INSTRUCTION.md
├── README.md
├── SUBMISSION.md
├── LoopForge_Contest_Driver_DESIGN.md
├── LoopForge_GitHub_Acceptance_Report.md
├── code/
├── work/
│   ├── HARNESS.md
│   ├── loopforge.config.yaml
│   ├── config-templates/
│   ├── docs/
│   ├── profiles/
│   ├── rules/
│   ├── runtime/
│   ├── scripts/
│   └── skills/
│       └── loopforge-driver/
│           └── SKILL.md
├── result/
│   ├── output.md
│   ├── issues/
│   │   └── 00-summary.md
│   └── screenshot/
│       └── .gitkeep
└── logs/
    ├── interaction.md
    └── trace/
        └── .gitkeep
```

说明：

- `code/` 暂时保留，作为本地默认源码/目标项目目录。
- `work/` 只承载框架可运行资产。
- `INSTRUCTION.md` 只做入口分发，不承载复杂业务内容。
- `result/`、`logs/` 先提供占位文件，避免提交结构缺失。
- `HARNESS.md` 是框架执行说明承接文件，避免把大量内容塞进 `INSTRUCTION.md`。

## 3. 目录移动清单

执行以下目录归位：

```bash
mkdir -p work

git mv skills work/skills
git mv runtime work/runtime
git mv scripts work/scripts
git mv rules work/rules
git mv profiles work/profiles
git mv config-templates work/config-templates
git mv docs work/docs
git mv loopforge.config.yaml work/loopforge.config.yaml
```

如果某个目录不存在，不要报错中断，可跳过。

新增目录：

```bash
mkdir -p result/issues result/screenshot logs/trace
touch result/screenshot/.gitkeep
touch logs/trace/.gitkeep
```

新增或覆盖：

```text
result/output.md
result/issues/00-summary.md
logs/interaction.md
work/HARNESS.md
```

## 4. 根目录 INSTRUCTION.md 最小改造

`INSTRUCTION.md` 应该改成“入口路由文件”，不要继续内嵌完整框架逻辑。

建议内容：

```markdown
# Contest Execution Instruction

This file is the root entrypoint for the contest evaluator and AI coding agent.

## 1. Read platform materials

Before making any change, read the runnable framework materials under:

- `work/HARNESS.md`
- `work/skills/loopforge-driver/SKILL.md`
- `work/loopforge.config.yaml`

Do not treat `INSTRUCTION.md` as the full workflow. It only routes the agent to the runnable materials in `work/`.

## 2. Resolve source path

Resolve the source project path in the following order:

1. Use the source path provided by the contest platform when invoking this instruction.
2. If no platform path is provided on Linux, try the configured absolute path in `work/loopforge.config.yaml`.
3. If still unresolved, use `code/` under this repository root as the local fallback path.

## 3. Execute framework

Follow `work/HARNESS.md`.

The framework assets are under `work/`. The source project is outside `work/`, or under `code/` only for local fallback.

## 4. Required output locations

When execution completes, ensure these paths exist:

- `result/output.md`
- `logs/interaction.md`
- `logs/trace/`

Do not require human interaction during automated execution.
```

注意：这里只修目录入口，不写 FlashDB 业务要求。

## 5. 新增 work/HARNESS.md

`work/HARNESS.md` 承接原 `INSTRUCTION.md` 中和框架执行有关的内容，但路径要改成 `work/` 内相对路径。

建议内容：

```markdown
# LoopForge Harness

## 1. Workspace layout

Repository root:

```text
.
├── INSTRUCTION.md
├── code/
├── work/
├── result/
└── logs/
```

Framework assets:

```text
work/
├── loopforge.config.yaml
├── runtime/
├── scripts/
├── rules/
├── profiles/
└── skills/
    └── loopforge-driver/
        └── SKILL.md
```

## 2. Agent entrypoint

Read and follow:

```text
work/skills/loopforge-driver/SKILL.md
```

## 3. Configuration

Read framework configuration from:

```text
work/loopforge.config.yaml
```

## 4. Bootstrap

Official Linux execution:

```bash
bash work/scripts/bootstrap.sh
```

Windows local smoke execution:

```powershell
powershell -ExecutionPolicy Bypass -File work/scripts/bootstrap.ps1
```

## 5. Source path resolution

The source project path must be resolved by the following priority:

1. Platform-provided source path.
2. Linux configured absolute fallback path.
3. Local repository fallback: `code/`.

## 6. Required root-level records

Keep these files or directories available:

```text
result/output.md
logs/interaction.md
logs/trace/
```

`logs/interaction.md` may be empty if execution is fully unattended.
```

## 6. 路径引用同步清单

只改路径，不改语义。

### 6.1 INSTRUCTION.md

替换：

```text
skills/loopforge-driver/SKILL.md
loopforge.config.yaml
scripts/bootstrap.sh
scripts/bootstrap.ps1
```

为：

```text
work/skills/loopforge-driver/SKILL.md
work/loopforge.config.yaml
work/scripts/bootstrap.sh
work/scripts/bootstrap.ps1
```

### 6.2 README.md / SUBMISSION.md / 设计文档

同步目录说明：

```text
skills/          -> work/skills/
runtime/         -> work/runtime/
scripts/         -> work/scripts/
rules/           -> work/rules/
profiles/        -> work/profiles/
config-templates/-> work/config-templates/
docs/            -> work/docs/
loopforge.config.yaml -> work/loopforge.config.yaml
```

### 6.3 work/scripts/bootstrap.sh

因为脚本从 `scripts/` 移到 `work/scripts/`，原来如果通过脚本目录推导项目根目录，通常要从：

```bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
```

改为：

```bash
WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT_DIR="$(cd "${WORK_DIR}/.." && pwd)"
```

脚本内部引用应变为：

```bash
python3 "${WORK_DIR}/runtime/loopforge_runner.py"
```

而不是：

```bash
python3 "${ROOT_DIR}/runtime/loopforge_runner.py"
```

### 6.4 work/scripts/bootstrap.ps1

同理，PowerShell 中应区分：

```powershell
$WorkDir = Split-Path -Parent $PSScriptRoot
$RootDir = Split-Path -Parent $WorkDir
```

运行 runner 时使用：

```powershell
python "$WorkDir/runtime/loopforge_runner.py"
```

### 6.5 work/runtime/loopforge_runner.py

只允许做目录相关改动：

- 配置路径默认从 `root/loopforge.config.yaml` 改为 `root/work/loopforge.config.yaml`。
- 框架资产目录从 `root/runtime`、`root/rules`、`root/profiles` 改为 `root/work/runtime`、`root/work/rules`、`root/work/profiles`。
- 本地默认源码目录仍可保留为 `root/code`。
- 不改任务模式、不改 profile 语义、不改验证命令语义。

## 7. 占位文件内容

### 7.1 result/output.md

```markdown
# Output

Framework directory structure has been prepared.

Actual execution output should be written here by the contest run.
```

### 7.2 result/issues/00-summary.md

```markdown
# Issues Summary

No execution issues recorded yet.
```

### 7.3 logs/interaction.md

```markdown
# Interaction Log

No manual interaction.
```

## 8. 本轮禁止修改

本轮修复不要做以下事情：

- 不新增 FlashDB/C2Rust 业务规则。
- 不改 `profiles` 中的迁移策略。
- 不生成 `flashDB_rust`。
- 不改 Rust 输出目录策略。
- 不补测试迁移说明。
- 不引入新的 agent 业务提示词。
- 不修改平台原始材料。
- 不把 `INSTRUCTION.md` 写成完整业务说明书。

## 9. 最小验收命令

完成目录修复后执行：

```bash
test -f INSTRUCTION.md
test -d work
test -f work/HARNESS.md
test -f work/skills/loopforge-driver/SKILL.md
test -f work/loopforge.config.yaml
test -d result
test -f result/output.md
test -d logs
test -f logs/interaction.md
test -d logs/trace
grep -R "skills/loopforge-driver" -n . --exclude-dir=.git || true
grep -R "scripts/bootstrap.sh" -n . --exclude-dir=.git || true
grep -R "loopforge.config.yaml" -n INSTRUCTION.md README.md SUBMISSION.md work 2>/dev/null || true
```

验收重点：

- 根目录存在 `INSTRUCTION.md`、`work/`、`result/`、`logs/`。
- skill 路径是 `work/skills/loopforge-driver/SKILL.md`。
- `INSTRUCTION.md` 不再指向根目录 `skills/`、`scripts/`、`runtime/`。
- `INSTRUCTION.md` 只作为入口，不承载完整业务逻辑。
- 框架资产全部在 `work/` 下。
