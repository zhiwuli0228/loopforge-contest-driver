# loopforge-contest-driver 剩余框架修复指导文档

> 适用状态：已删除根目录 `SUBMISSION.md`，并已完成目录壳、`SOURCE_ROOT` 入口、源码 README 输入模型的主要修复。
>
> 本文档只指导剩余框架收口，不涉及 C2Rust/FlashDB 业务转换实现。

---

## 1. 修复目标

当前项目应收敛为：

```text
README.md          说明作品是什么、如何快速开始
INSTRUCTION.md     评委 / Agent / 人工复现者的运行入口
work/              可运行资产：脚本、runtime、skills、subagent、rules、profiles
result/            评委侧运行结果
logs/              推理日志、执行日志、人工交互记录
code/              本地 fallback 源码目录，不是固定业务目录
```

核心输入模型：

```text
SOURCE_ROOT + SOURCE_ROOT/README
```

含义：

1. 外部只需要提供源码路径 `SOURCE_ROOT`。
2. 需求、约束、验收信息从源码目录 README 读取。
3. 不再要求人工填写 `task.name`、`objective`、`language`、`verification.commands`。
4. `work/loopforge.config.yaml` 只保留框架默认值，不承载具体需求。
5. `result/output.md` 是评委侧主输出。
6. `SOURCE_ROOT/.loopforge/` 只能作为内部运行证据，不是评委主入口。

---

## 2. 本轮不修改内容

不要修改以下内容：

```text
C2Rust 业务转换策略
FlashDB 具体转换逻辑
Rust 项目生成逻辑
测试迁移业务规则
subagent 的业务职责拆分
profiles/rules 的核心业务能力
```

本轮只做框架收口：

```text
README.md
INSTRUCTION.md
work/README.md
work/skills/loopforge-driver/SKILL.md
work/scripts/smoke-test.sh
work/scripts/smoke-test.ps1
work/runtime/loopforge_runner.py 的输出文案
result/output.md / result/issues/00-summary.md 的自检状态
根目录过程文档清理
```

---

## 3. 根目录清理

### 3.1 已完成项

根目录 `SUBMISSION.md` 已删除，这是正确的。

比赛根目录不需要 `SUBMISSION.md`。提交根目录应保持干净，避免评委和 Agent 混淆入口。

### 3.2 继续清理过程文档

检查根目录是否还有以下过程文档：

```text
loopforge-contest-driver-current-check-and-codex-checklist.md
loopforge-contest-driver-framework-only-fix.md
loopforge-contest-driver-instruction-entrypoint-design.md
loopforge-contest-driver-source-readme-input-simplification-design.md
loopforge-contest-driver-self-check-and-repair-guide.md
```

处理方式二选一。

推荐方式：删除。

```bash
git rm loopforge-contest-driver-*.md
```

保守方式：移动到内部记录目录。

```bash
mkdir -p docs/internal-repair-notes
git mv loopforge-contest-driver-*.md docs/internal-repair-notes/
```

### 3.3 根目录最终建议

根目录建议保留：

```text
INSTRUCTION.md
README.md
work/
result/
logs/
code/
```

允许保留项目自身必要的配置文件，例如 `.gitignore`、LICENSE 等。

---

## 4. README.md 修复建议

### 4.1 README.md 应承担的职责

`README.md` 只说明：

```text
作品是什么
核心输入模型是什么
如何快速运行
结果在哪里查看
目录概览
```

不要承载：

```text
业务转换细节
复杂 Agent 编排规则
旧的 Mode + Profile 人工配置模型
code/.loopforge/reports/final-report.md 作为主结果
```

### 4.2 必须清理的旧内容

在 README.md 中搜索并清理：

```bash
grep -n "fill-by-human\|Human adaptation must provide\|E:/009workspace\|SOURCE_ROOT= bash\|code/.loopforge/reports/final-report.md" README.md
```

要求：

1. 不出现 `fill-by-human`。
2. 不出现 `Human adaptation must provide`。
3. 不出现本机绝对路径 `E:/009workspace`。
4. 不把 `SOURCE_ROOT= bash work/scripts/run.sh` 作为主示例。
5. 不把 `code/.loopforge/reports/final-report.md` 作为评委主输出。

### 4.3 推荐 README 快速开始片段

可以将 README 中的 Quick Start 收敛为：

```md
## Quick Start

Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r work/requirements.txt
SOURCE_ROOT="/path/to/FlashDB" bash work/scripts/run.sh
```

Linux fallback mode:

```bash
bash work/scripts/run.sh
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r work\requirements.txt
$env:SOURCE_ROOT = "C:\path\to\FlashDB"
powershell -ExecutionPolicy Bypass -File work\scripts\run.ps1
```

Results:

```text
result/output.md
result/issues/00-summary.md
logs/interaction.md
logs/trace/
```
```

注意：`SOURCE_ROOT="/path/to/FlashDB"` 是主示例，`bash work/scripts/run.sh` 是 fallback 示例。

---

## 5. INSTRUCTION.md 修复建议

### 5.1 INSTRUCTION.md 应承担的职责

`INSTRUCTION.md` 是评委、平台 Agent、人工复现者的执行手册。

它应该回答：

```text
需要什么环境
怎么安装 Python 依赖
怎么传入 SOURCE_ROOT
怎么运行工具
结果在哪里看
失败时查哪里
```

不要写：

```text
FlashDB 具体转换规则
C2Rust 业务策略
skill/profile/rules 全文
比赛目录规范长篇解释
```

### 5.2 必须修正的示例

如果存在：

```bash
SOURCE_ROOT= bash work/scripts/run.sh
```

改为：

```bash
SOURCE_ROOT="/path/to/FlashDB" bash work/scripts/run.sh
```

fallback 单独写：

```bash
bash work/scripts/run.sh
```

### 5.3 INSTRUCTION.md 推荐结构

建议保留以下章节：

```text
1. Purpose
2. Environment Requirements
3. Python Dependency Setup
4. Source Path Resolution
5. Run the Tool
6. Result Retrieval
7. Failure Handling
```

### 5.4 源码路径解析规则

INSTRUCTION.md 中应明确：

```text
优先级 1：平台显式传入的源码路径
优先级 2：自然语言中提到的源码路径
优先级 3：SOURCE_ROOT 环境变量
优先级 4：--source-root 参数
优先级 5：Linux 平台默认挂载路径 fallback
优先级 6：Windows / local 使用 code/
```

表达重点：

```text
源码 README 是需求与约束来源。
work/loopforge.config.yaml 不是人工需求填写入口。
```

---

## 6. work/README.md 修复建议

### 6.1 work/README.md 应承担的职责

`work/README.md` 只说明 work 目录里的可运行资产。

推荐表达：

```text
work/ contains runnable framework assets.
SOURCE_ROOT is the only external task input.
Task requirements are read from SOURCE_ROOT README.
work/loopforge.config.yaml provides framework defaults only.
```

### 6.2 必须删除的旧表达

搜索：

```bash
grep -n "Human adaptation must provide\|fill-by-human\|verification.commands\|code/.loopforge/reports/final-report.md" work/README.md
```

处理规则：

1. `verification.commands` 可以作为框架可选项存在，但不能写成“人工必须配置”。
2. `code/.loopforge/reports/final-report.md` 不得作为主结果路径。
3. `.loopforge` 只能描述为内部运行证据。

---

## 7. work/skills/loopforge-driver/SKILL.md 修复建议

### 7.1 当前 skill 的目标

该 skill 应指导 Agent 执行比赛入口，而不是恢复旧的通用 LoopForge 平台模型。

核心表述应是：

```text
SOURCE_ROOT + source README
```

### 7.2 必须清理的旧表达

搜索：

```bash
grep -n "fill-by-human\|Human adaptation must provide\|SOURCE_ROOT= bash\|code/.loopforge/reports/final-report.md\|--code-dir\|code/ project" work/skills/loopforge-driver/SKILL.md
```

处理规则：

1. 不要求人工填写 task/objective/language/verification commands。
2. 不把 `code/` 写成唯一目标项目。
3. 不把 `code/.loopforge/reports/final-report.md` 写成主输出。
4. 不使用 `SOURCE_ROOT= bash ...` 作为主示例。
5. 不继续引导 `--code-dir` 旧入口。

### 7.3 推荐核心片段

可以将 skill 中的核心模型收敛为：

```md
## Core Model

The contest driver uses:

```text
SOURCE_ROOT + source README
```

`SOURCE_ROOT` points to the source project.

Task requirements, constraints, and acceptance context must be read from the README file under `SOURCE_ROOT`.

Do not require humans to fill task name, objective, language, or verification commands in `work/loopforge.config.yaml`.

## Execution

Linux:

```bash
SOURCE_ROOT="/path/to/source" bash work/scripts/run.sh
```

Fallback:

```bash
bash work/scripts/run.sh
```

Windows:

```powershell
$env:SOURCE_ROOT = "C:\path\to\source"
powershell -ExecutionPolicy Bypass -File work\scripts\run.ps1
```

## Output Contract

Evaluator-facing outputs:

```text
result/output.md
result/issues/00-summary.md
logs/interaction.md
logs/trace/
```

Internal runtime evidence may be written under:

```text
SOURCE_ROOT/.loopforge/
```

Do not treat `.loopforge` as the evaluator-facing primary result.
```

---

## 8. smoke-test 修复建议

### 8.1 当前问题

当前 smoke-test 如果只验证 `BLOCKED_WITH_REPORT`，会形成错误信号：

```text
自检通过 = 工具能生成阻断报告
```

这个只能证明负向路径有效，不能证明存在源码 README 时能正向执行。

### 8.2 正确目标

smoke-test 应包含两个场景：

```text
negative smoke:
  源码目录没有 README 时，应生成 blocked report。

positive smoke:
  源码目录有 README 时，应成功识别 README，并写入 result/logs。
```

### 8.3 smoke-test.sh 推荐逻辑

建议 `work/scripts/smoke-test.sh` 至少具备以下逻辑：

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

NEG_SOURCE="$TMP_DIR/no-readme-source"
POS_SOURCE="$TMP_DIR/with-readme-source"

mkdir -p "$NEG_SOURCE"
mkdir -p "$POS_SOURCE"

cat > "$POS_SOURCE/README.md" <<'EOF'
# Fake Source Project

This README is used by smoke-test.

Task:
- Validate that the driver can read SOURCE_ROOT README.

Acceptance:
- source_readme_found should be true.
- selected_source_readme should point to this README.
EOF

echo "[smoke] negative case: source without README"
bash "$ROOT_DIR/work/scripts/run.sh" --source-root "$NEG_SOURCE"

test -f "$ROOT_DIR/result/output.md"
test -f "$ROOT_DIR/result/issues/00-summary.md"
test -f "$ROOT_DIR/logs/trace/run-summary.json"

grep -q "source_readme_found: false" "$ROOT_DIR/result/output.md" \
  || grep -q '"found": false' "$ROOT_DIR/logs/trace/run-summary.json" \
  || {
    echo "negative smoke failed: missing source_readme_found=false evidence" >&2
    exit 1
  }

echo "[smoke] positive case: source with README"
bash "$ROOT_DIR/work/scripts/run.sh" --source-root "$POS_SOURCE"

test -f "$ROOT_DIR/result/output.md"
test -f "$ROOT_DIR/logs/trace/run-summary.json"

grep -q "source_readme_found: true" "$ROOT_DIR/result/output.md" \
  || grep -q '"found": true' "$ROOT_DIR/logs/trace/run-summary.json" \
  || {
    echo "positive smoke failed: missing source_readme_found=true evidence" >&2
    exit 1
  }

grep -q "README.md" "$ROOT_DIR/result/output.md" \
  || grep -q "README.md" "$ROOT_DIR/logs/trace/run-summary.json" \
  || {
    echo "positive smoke failed: selected README evidence missing" >&2
    exit 1
  }

echo "smoke test passed"
```

### 8.4 smoke-test.ps1

PowerShell 版本同样应包含：

```text
negative source without README
positive source with README
检查 result/output.md
检查 logs/trace/run-summary.json
检查 found=false / found=true
```

如果暂时来不及完整实现 PowerShell 正向 smoke，至少不要让它只用 `BLOCKED_WITH_REPORT` 作为唯一成功条件。

---

## 9. loopforge_runner.py 文案修复

### 9.1 修复范围

只改输出文案，不改业务逻辑。

### 9.2 搜索旧文案

```bash
grep -n "Code changes are allowed only inside code/\|Runtime artifacts are written only under code/.loopforge\|code/.loopforge/reports/final-report.md" work/runtime/loopforge_runner.py
```

### 9.3 替换原则

旧表达：

```text
Code changes are allowed only inside code/.
Runtime artifacts are written only under code/.loopforge/.
```

替换为：

```text
Code changes are allowed only inside the resolved SOURCE_ROOT.
Runtime artifacts may be written under SOURCE_ROOT/.loopforge/.
Evaluator-facing outputs are written under result/ and logs/.
```

### 9.4 `.loopforge` 的允许范围

允许保留：

```text
SOURCE_ROOT/.loopforge/
```

不允许保留：

```text
code/.loopforge/reports/final-report.md as primary evaluator output
```

---

## 10. result 输出修复建议

### 10.1 当前问题

如果当前 `result/output.md` 只是本地 blocked 结果，会给评委造成“作品只能阻断”的观感。

### 10.2 推荐做法

在完成 positive smoke 后，重新生成一次结果。

执行：

```bash
bash work/scripts/smoke-test.sh
```

然后检查：

```bash
cat result/output.md
cat result/issues/00-summary.md
cat logs/trace/run-summary.json
```

期望至少看到：

```text
source_readme_found: true
selected_source_readme: .../README.md
```

如果不想提交 smoke 运行产物，则 `result/output.md` 应保持中性说明，不要显示“当前执行失败”作为唯一结果。

---

## 11. 最终自检命令

### 11.1 文件存在性

```bash
test -f INSTRUCTION.md
test -f README.md
test ! -f SUBMISSION.md
test -d work
test -d result
test -d logs
test -f result/output.md
test -f logs/interaction.md
test -d logs/trace
```

### 11.2 根目录噪声

```bash
find . -maxdepth 1 -type f -name "loopforge-contest-driver-*.md" -print
```

期望无输出。

### 11.3 旧模型残留

```bash
grep -R "fill-by-human\|Human adaptation must provide\|E:/009workspace\|SOURCE_ROOT= bash" -n . --exclude-dir=.git
```

期望无输出。

### 11.4 旧输出口径

```bash
grep -R "code/.loopforge/reports/final-report.md" -n . --exclude-dir=.git
```

允许出现条件：

```text
仅作为 historical note 或 internal runtime evidence。
```

不允许出现条件：

```text
作为 evaluator-facing primary output。
```

### 11.5 脚本语法

```bash
bash -n work/scripts/run.sh
bash -n work/scripts/bootstrap.sh
bash -n work/scripts/smoke-test.sh
```

### 11.6 smoke-test

```bash
bash work/scripts/smoke-test.sh
```

通过标准：

```text
negative case 通过
positive case 通过
result/output.md 存在
logs/trace/run-summary.json 存在
positive case 能识别 README
```

---

## 12. 最小修复顺序

建议按以下顺序手动修：

```text
1. 清理根目录过程文档
2. 修 README.md
3. 修 INSTRUCTION.md
4. 修 work/README.md
5. 修 work/skills/loopforge-driver/SKILL.md
6. 修 work/scripts/smoke-test.sh
7. 修 work/scripts/smoke-test.ps1
8. 修 work/runtime/loopforge_runner.py 输出文案
9. 跑 grep 自检
10. 跑 bash -n
11. 跑 smoke-test
12. 更新 result/output.md 与 result/issues/00-summary.md
```

---

## 13. 通过标准

完成后，项目应满足：

```text
根目录没有 SUBMISSION.md
根目录没有修复过程文档噪声
README.md 只做项目说明和快速开始
INSTRUCTION.md 能指导评委 / Agent / 人工复现者准备环境并运行
SOURCE_ROOT 是唯一外部输入
需求和约束从 SOURCE_ROOT README 读取
work/loopforge.config.yaml 不要求人工填写需求
smoke-test 同时覆盖无 README 和有 README 场景
result/output.md 是评委侧主结果
logs/trace/ 保留执行证据
```

完成这一轮后，框架层基本收口。下一阶段再进入 C2Rust/FlashDB 业务执行能力验证。
