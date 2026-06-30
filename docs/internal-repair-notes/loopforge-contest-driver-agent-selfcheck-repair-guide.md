# LoopForge Contest Driver 通用框架 Agent 自检与修复指导

> 适用对象：Codex / opencode / Claude Code 等执行型 Agent  
> 适用阶段：当前仍处于 **通用比赛执行框架修复阶段**，不是 Rust/C2Rust/FlashDB 业务定制阶段。

---

## 0. 当前修复目标

本轮目标不是实现某一道题的业务逻辑，而是修复 `loopforge-contest-driver` 的通用比赛执行框架，使其满足：

```text
评委 / 平台 Agent / 人工复现者
能够通过 README + INSTRUCTION.md
完成环境准备、源码路径传入、工具执行、结果查看和失败排查。
```

通用框架必须支持任意比赛题目：

```text
SOURCE_ROOT + 源码 README 驱动
```

含义：

1. 外部只需要提供源码路径 `SOURCE_ROOT`。
2. 需求、约束、验收信息从 `SOURCE_ROOT` 下的 README 文件读取。
3. `work/` 中的规则、mode、skill、subagent 只能提供通用执行框架能力。
4. 不允许把某一道题、某种语言、某个历史项目写死到框架中。

---

## 1. Agent 执行前强制要求

Agent 必须先读取当前仓库真实文件，不得基于历史记忆修改。

### 1.1 必须读取的文件

```text
README.md
INSTRUCTION.md
work/README.md
work/HARNESS.md
work/loopforge.config.yaml
work/skills/loopforge-driver/SKILL.md
work/scripts/run.sh
work/scripts/run.ps1
work/scripts/bootstrap.sh
work/scripts/bootstrap.ps1
work/scripts/smoke-test.sh
work/scripts/smoke-test.ps1
work/runtime/loopforge_runner.py
result/output.md
result/issues/00-summary.md
logs/interaction.md
```

### 1.2 必须扫描的目录

```text
work/rules/
work/rules/loopforge/
work/rules/loopforge/common/          # 如果存在
work/rules/loopforge/modes/           # 如果存在
work/skills/
work/agents/                          # 如果存在
work/subagent/                        # 如果存在
logs/trace/
result/
```

### 1.3 禁止基于猜测修复

如果文件内容与本指导文档描述不一致，以当前仓库真实文件为准。  
Agent 应先读文件、grep、确认引用关系，再执行修复。

---

## 2. 修复边界

### 2.1 本轮允许修改

允许修改以下类型文件：

```text
README.md
INSTRUCTION.md
work/README.md
work/HARNESS.md
work/loopforge.config.yaml
work/skills/**/SKILL.md
work/agents/*.md
work/subagent/*.md
work/rules/**/*.md
work/scripts/*.sh
work/scripts/*.ps1
work/runtime/loopforge_runner.py
result/output.md
result/issues/00-summary.md
logs/interaction.md
logs/trace/*.json
```

允许删除或移动以下类型文件：

```text
SUBMISSION.md
config-templates/
根目录 loopforge-contest-driver-*.md 修复过程文档
明显历史项目模板
明显业务残留模板
```

### 2.2 本轮禁止修改

禁止做以下事情：

```text
不要实现 Rust/C2Rust/FlashDB 业务转换能力
不要新增某一道题专用规则
不要把 Java/Gulimall/Maven/FlashDB/Rust 写入通用框架规则
不要把 work/loopforge.config.yaml 重新设计成人工填写需求配置
不要让执行流程依赖人工确认
不要把 code/ 作为唯一源码目录
不要把 code/.loopforge/reports/final-report.md 作为评委主输出
不要删除通用框架能力后只保留某一道题能力
```

---

## 3. 目录与入口自检

### 3.1 根目录必须存在

执行：

```bash
test -f INSTRUCTION.md
test -f README.md
test -d work
test -d result
test -d logs
```

### 3.2 根目录不应保留非必要提交噪声

执行：

```bash
test ! -f SUBMISSION.md
find . -maxdepth 1 -type f -name "loopforge-contest-driver-*.md" -print
find . -maxdepth 1 -type d -name "config-templates" -print
```

通过标准：

```text
SUBMISSION.md 不存在。
根目录不存在 loopforge-contest-driver-*.md 修复过程文档。
config-templates/ 不在根目录。
```

### 3.3 不通过时修复

如果 `SUBMISSION.md` 存在：

```bash
git rm SUBMISSION.md
```

如果根目录存在 `loopforge-contest-driver-*.md`：

```bash
mkdir -p docs/internal-repair-notes
git mv loopforge-contest-driver-*.md docs/internal-repair-notes/ 2>/dev/null || true
```

如果根目录存在 `config-templates/` 且只是历史业务模板：

```bash
git rm -r config-templates
```

如果需要保留历史参考：

```bash
mkdir -p docs/internal-repair-notes/legacy-config-templates
git mv config-templates/* docs/internal-repair-notes/legacy-config-templates/
git rm -r config-templates
```

---

## 4. README.md 自检

### 4.1 README.md 应承担的职责

`README.md` 只负责：

```text
说明作品是什么
说明通用输入模型
说明快速运行入口
说明主要结果位置
指向 INSTRUCTION.md
```

### 4.2 README.md 不应包含

执行：

```bash
grep -n "fill-by-human\|Human adaptation must provide\|E:/\|code/.loopforge/reports/final-report.md\|SOURCE_ROOT= bash\|Gulimall\|gulimall" README.md || true
```

不应出现：

```text
fill-by-human
Human adaptation must provide
E:/ 本机路径
SOURCE_ROOT= bash 作为主示例
code/.loopforge/reports/final-report.md 作为评委主输出
Gulimall / 旧 Java 项目痕迹
```

### 4.3 README.md 应包含

执行：

```bash
grep -n "SOURCE_ROOT\|source README\|INSTRUCTION.md\|result/output.md\|logs/trace" README.md
```

应体现：

```text
SOURCE_ROOT 是外部源码路径输入。
需求与约束从 SOURCE_ROOT README 读取。
评委运行参考 INSTRUCTION.md。
主结果是 result/output.md。
日志在 logs/trace/。
```

### 4.4 不通过时修复

将 README.md 收敛为以下结构：

```md
# LoopForge Contest Driver

This project is a generic contest execution driver.

It uses one external input:

```text
SOURCE_ROOT
```

`SOURCE_ROOT` points to the source project provided by the contest platform or local evaluator.
Task requirements, constraints, and acceptance information are read from the README file under `SOURCE_ROOT`.

## Quick Start

Read `INSTRUCTION.md` for full environment setup and execution instructions.

Linux:

```bash
SOURCE_ROOT="/path/to/source" bash work/scripts/run.sh
```

Local fallback:

```bash
bash work/scripts/run.sh
```

## Results

Evaluator-facing outputs are written to:

```text
result/output.md
result/issues/00-summary.md
logs/interaction.md
logs/trace/
```
```

---

## 5. INSTRUCTION.md 自检

### 5.1 INSTRUCTION.md 应承担的职责

`INSTRUCTION.md` 是运行入口说明，不是业务规则文档。它必须说明：

```text
环境要求
Python 依赖安装
源码路径传入协议
Linux / Windows 调用命令
结果获取路径
失败排查路径
```

### 5.2 必须存在的内容

执行：

```bash
grep -n "Python\|pip\|requirements.txt\|SOURCE_ROOT\|--source-root\|result/output.md\|logs/trace" INSTRUCTION.md
```

### 5.3 不应出现的内容

执行：

```bash
grep -n "fill-by-human\|Human adaptation\|SOURCE_ROOT= bash\|code/.loopforge/reports/final-report.md\|Gulimall\|FlashDB\|Rust conversion" INSTRUCTION.md || true
```

注意：

- `FlashDB` 或 `Rust` 只有在举例说明“路径示例”时才可出现，但不应作为通用框架规则。
- 不应出现 `SOURCE_ROOT= bash work/scripts/run.sh` 作为主示例。

### 5.4 不通过时修复

主运行示例必须使用显式路径：

```bash
SOURCE_ROOT="/path/to/source" bash work/scripts/run.sh
```

fallback 示例单独写：

```bash
bash work/scripts/run.sh
```

Windows 示例：

```powershell
$env:SOURCE_ROOT = "C:\path\to\source"
powershell -ExecutionPolicy Bypass -File work\scripts\run.ps1
```

---

## 6. work/loopforge.config.yaml 自检

### 6.1 配置文件职责

`work/loopforge.config.yaml` 只能承载通用框架默认值，不承载具体题目需求。

它可以包含：

```text
framework name
input model
source README candidates
default mode
output contract
log contract
unattended execution flag
mode selection fallback
```

它不应包含：

```text
具体题目名称
具体业务 objective
人工填写字段
人工 verification.commands
具体语言绑定
具体项目绑定
```

### 6.2 自检命令

```bash
grep -n "fill-by-human\|human-configured\|Human adaptation\|Gulimall\|gulimall\|FlashDB\|Rust\|Java\|Maven\|mvn\|code/.loopforge/reports/final-report.md" work/loopforge.config.yaml || true
```

通过标准：无高风险业务残留。

### 6.3 推荐配置模型

如果当前配置仍然复杂，收敛为类似结构：

```yaml
framework:
  name: loopforge-contest-driver
  input_model: source-readme
  default_mode: feature-development

source:
  root_env: SOURCE_ROOT
  readme_candidates:
    - README.md
    - README
    - readme.md
    - Readme.md

execution:
  unattended: true
  allow_manual_interaction: false

mode_selection:
  source: source-readme
  fallback: feature-development

output:
  result_file: result/output.md
  issue_summary: result/issues/00-summary.md
  log_dir: logs/trace
  interaction_log: logs/interaction.md
```

---

## 7. work/rules/loopforge/modes 自检

### 7.1 正确定位

`work/rules/loopforge/modes` 可以保留。它是通用任务模式规则库，不是某一道题规则库。

允许存在的模式示例：

```text
feature-development
defect-repair
migration
consistency-check
test-completion
```

可以暂时保留但不应默认触发的模式：

```text
skill-generation
```

### 7.2 modes 文件只能描述通用流程

每个 mode 只能回答：

```text
这个任务类型如何推进
有哪些阶段
每阶段产出什么
禁止什么
最终如何记录结果
```

不能回答：

```text
某道题怎么做
某个语言怎么实现
某个业务系统怎么验证
某个固定源码目录在哪里
```

### 7.3 高风险残留扫描

执行：

```bash
grep -R "code/\.loopforge\|code/\|fill-by-human\|Human adaptation\|verification.commands\|gulimall\|Gulimall\|maven\|Maven\|mvn\|FlashDB\|Rust\|C2Rust\|Java" -n work/rules/loopforge/modes || true
```

### 7.4 判断规则

| 扫描结果 | 处理方式 |
|---|---|
| `code/` 固定路径 | 改为 `SOURCE_ROOT` |
| `code/.loopforge` | 改为 `SOURCE_ROOT/.loopforge`，且标注为内部证据 |
| `verification.commands` 人工配置 | 改为从源码 README 推断或框架默认验证 |
| Java/Maven/Gulimall | 删除，不能出现在通用 mode 中 |
| FlashDB/Rust/C2Rust | 删除，不能出现在通用 mode 中 |
| `fill-by-human` | 删除 |
| 人工确认流程 | 删除或改为无人值守执行记录 |

### 7.5 不通过时修复原则

不要删除整个 `modes` 目录，除非它完全未被引用且没有通用价值。

优先做：

```text
保留 mode 抽象
删除业务痕迹
删除语言绑定
删除 code/ 固定路径
删除人工配置依赖
把输出统一到 result/ 和 logs/
```

如果某个 mode 完全是历史业务模式，移动到：

```text
docs/internal-repair-notes/legacy-modes/
```

---

## 8. work/rules/loopforge/common 自检

如果当前没有 `work/rules/loopforge/common/`，建议新增，用于沉淀通用规则。

推荐结构：

```text
work/rules/loopforge/common/
├── source-root.md
├── source-readme.md
├── result-contract.md
├── log-contract.md
└── forbidden-actions.md
```

### 8.1 source-root.md 应说明

```text
SOURCE_ROOT 是唯一外部源码输入。
平台显式路径优先。
自然语言路径可被 Agent 提取。
Linux 可使用平台绝对路径 fallback。
Windows/local fallback 到 code/。
```

### 8.2 source-readme.md 应说明

```text
需求、约束、验收从 SOURCE_ROOT README 读取。
支持 README.md / README / readme.md / Readme.md。
没有 README 时生成 blocked report，不等待人工填写配置。
```

### 8.3 result-contract.md 应说明

```text
result/output.md 是评委主输出。
result/issues/00-summary.md 是问题摘要。
SOURCE_ROOT/.loopforge/ 只是内部证据，不是主输出。
```

### 8.4 log-contract.md 应说明

```text
logs/interaction.md 记录人工交互。
无人值守时可以为空。
logs/trace/ 存放执行跟踪。
```

### 8.5 forbidden-actions.md 应说明

```text
不得等待人工填写业务配置。
不得修改平台原始测试材料。
不得把某个历史项目路径写死。
不得把 result/logs 之外的路径作为评委唯一输出。
```

---

## 9. work/skills/loopforge-driver/SKILL.md 自检

### 9.1 Skill 应承担的职责

Skill 是 Agent 执行规则，不是业务题解。它应该告诉 Agent：

```text
读取 INSTRUCTION.md
读取 work/HARNESS.md
解析 SOURCE_ROOT
读取 SOURCE_ROOT README
选择通用 mode
执行工具
输出 result/logs
```

### 9.2 Skill 不应包含

执行：

```bash
grep -n "fill-by-human\|Human adaptation\|SOURCE_ROOT= bash\|code/.loopforge/reports/final-report.md\|Gulimall\|gulimall\|FlashDB\|C2Rust\|Rust conversion\|mvn\|Maven" work/skills/loopforge-driver/SKILL.md || true
```

### 9.3 不通过时修复

将 Skill 收敛为：

```text
Core model: SOURCE_ROOT + source README
Do not require manual task/objective/verification config
Read common rules and selected mode rules
Run work/scripts/run.sh or run.ps1
Evaluator-facing output is result/ and logs/
```

---

## 10. work/scripts 自检

### 10.1 run.sh / run.ps1 必须支持

```text
SOURCE_ROOT 环境变量
--source-root 参数
Linux fallback
Windows/local fallback 到 code/
创建 result/issues 和 logs/trace
调用 runtime runner
```

### 10.2 bootstrap 必须转调 run

`bootstrap.sh` 和 `bootstrap.ps1` 不应维护另一套 `--code-dir` 旧入口。

检查：

```bash
grep -n "run.sh\|run.ps1" work/scripts/bootstrap.sh work/scripts/bootstrap.ps1 || true
```

### 10.3 禁止旧模型

```bash
grep -R "fill-by-human\|Human adaptation\|code/.loopforge/reports/final-report.md\|--code-dir" -n work/scripts || true
```

说明：

- `--code-dir` 如果只是向后兼容且内部转成 `SOURCE_ROOT`，可以保留。
- 如果它成为主入口或唯一入口，应修复。

### 10.4 语法检查

```bash
bash -n work/scripts/run.sh
bash -n work/scripts/bootstrap.sh
bash -n work/scripts/smoke-test.sh
```

---

## 11. smoke-test 自检

### 11.1 smoke-test 必须有正向和负向场景

负向场景：

```text
临时 SOURCE_ROOT 没有 README
运行后必须生成 blocked report
必须能说明 source README not found
```

正向场景：

```text
临时 SOURCE_ROOT 有 README.md
运行后必须识别 README
必须生成 result/output.md
必须生成 logs/trace/run-summary.json
必须记录 source_readme_found=true 或等价字段
```

### 11.2 自检命令

```bash
grep -n "BLOCKED_WITH_REPORT\|source_readme_found\|README.md\|mktemp\|fake" work/scripts/smoke-test.sh || true
```

### 11.3 不通过时修复

如果 smoke-test 只检查 `BLOCKED_WITH_REPORT`，必须新增正向场景。

示例逻辑：

```bash
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

NEG_SOURCE="$TMP_DIR/no-readme-source"
POS_SOURCE="$TMP_DIR/with-readme-source"
mkdir -p "$NEG_SOURCE" "$POS_SOURCE"

cat > "$POS_SOURCE/README.md" <<'README'
# Fake Source Project

Task: validate source README driven execution.
Acceptance: the driver must detect this README.
README

bash work/scripts/run.sh --source-root "$NEG_SOURCE"
# assert source_readme_found=false or blocked evidence

bash work/scripts/run.sh --source-root "$POS_SOURCE"
# assert source_readme_found=true and selected README evidence
```

PowerShell smoke-test 应保持等价。

---

## 12. runtime 输出文案自检

### 12.1 搜索旧输出口径

```bash
grep -n "Code changes are allowed only inside code\|Runtime artifacts are written only under code/.loopforge\|code/.loopforge/reports/final-report.md" work/runtime/loopforge_runner.py || true
```

### 12.2 不通过时修复

将旧文案：

```text
Code changes are allowed only inside code/.
Runtime artifacts are written only under code/.loopforge/.
```

改为：

```text
Code changes are allowed only inside the resolved SOURCE_ROOT.
Runtime artifacts may be written under SOURCE_ROOT/.loopforge/.
Evaluator-facing outputs are written under result/ and logs/.
```

`SOURCE_ROOT/.loopforge/` 可以作为内部 evidence，但不得作为评委主输出。

---

## 13. result/logs 自检

### 13.1 必须存在

```bash
test -f result/output.md
test -d result/issues
test -f result/issues/00-summary.md
test -f logs/interaction.md
test -d logs/trace
```

### 13.2 result/output.md 应表达当前状态

允许状态：

```text
COMPLETED
BLOCKED_WITH_REPORT
PARTIAL_WITH_REPORT
```

但如果只是本地 fallback 缺少 README 的 blocked 结果，应明确说明：

```text
This is a framework self-check degraded result, not a business task completion result.
```

### 13.3 最终建议

完成 smoke-test 正向场景后，建议让 `result/output.md` 体现至少一次 README 被识别的正向结果。

---

## 14. 全局旧模型残留检查

执行：

```bash
grep -R "fill-by-human\|Human adaptation must provide\|E:/009workspace\|SOURCE_ROOT= bash\|code/.loopforge/reports/final-report.md\|gulimall\|Gulimall" -n . --exclude-dir=.git || true
```

处理规则：

| 命中项 | 是否允许 |
|---|---|
| `fill-by-human` | 不允许 |
| `Human adaptation must provide` | 不允许 |
| `E:/009workspace` | 不允许 |
| `SOURCE_ROOT= bash` | 不允许 |
| `code/.loopforge/reports/final-report.md` | 仅允许作为历史兼容或内部 evidence，不能作为主输出 |
| `Gulimall/gulimall` | 不允许出现在通用框架路径 |

再执行：

```bash
grep -R "FlashDB\|C2Rust\|Rust conversion" -n work README.md INSTRUCTION.md --exclude-dir=.git || true
```

处理规则：

```text
当前通用框架阶段不应出现 Rust/C2Rust/FlashDB 业务规则。
如果只是示例路径，应改成 /path/to/source。
```

---

## 15. Agent 修复流程

Agent 必须按以下顺序执行：

```text
1. 读取文件和目录，建立当前状态
2. 执行 grep 自检，列出不通过项
3. 只修通用框架，不修业务题目
4. 优先清理根目录噪声和旧业务模板
5. 修 README / INSTRUCTION 的入口口径
6. 修 work/loopforge.config.yaml 的框架默认配置
7. 修 work/rules/loopforge/common 和 modes 的通用化问题
8. 修 skill/subagent 的执行口径
9. 修脚本 SOURCE_ROOT 协议和 smoke-test 正负向场景
10. 修 runtime 输出文案
11. 运行最终自检命令
12. 输出修复报告
```

---

## 16. Agent 最终回复要求

Agent 完成后必须输出：

```text
1. 修改了哪些文件
2. 删除或移动了哪些文件/目录
3. 哪些旧模型残留已清理
4. README / INSTRUCTION 当前入口模型
5. SOURCE_ROOT 路径协议是否通过
6. smoke-test 是否包含正向和负向场景
7. 全局 grep 是否仍有残留，若有，说明为什么保留
8. 是否触碰业务转换逻辑，预期答案应为否
```

---

## 17. 最终通过标准

全部满足以下条件，才算本轮通用框架修复通过：

```text
- 根目录只保留必要入口和运行交付件。
- INSTRUCTION.md 能指导环境准备、依赖安装、源码路径传入、执行和结果获取。
- README.md 不承载复杂业务配置，只说明项目和快速入口。
- SOURCE_ROOT 是唯一外部源码输入。
- 源码 README 是需求、约束、验收上下文来源。
- work/loopforge.config.yaml 只承载框架默认值。
- work/rules/loopforge/modes 保持通用，不绑定语言/业务/历史项目。
- skill/subagent 不要求人工填写业务配置。
- scripts 支持 SOURCE_ROOT 和 fallback。
- smoke-test 同时验证无 README 阻断和有 README 正向执行。
- result/output.md 和 logs/trace/ 是评委可见输出。
- 没有 fill-by-human、Human adaptation、E:/ 本机路径、Gulimall 等旧模型残留。
- 没有 Rust/C2Rust/FlashDB 等题目定制规则混入通用框架。
```

---

## 18. 推荐交给 Agent 的完整指令

```md
你现在修复 loopforge-contest-driver 的通用比赛执行框架。

当前阶段不是 Rust/C2Rust/FlashDB 业务定制，不要实现任何题目业务能力。

请先读取当前仓库真实文件和目录，不要基于历史记忆修改。

目标模型：
- SOURCE_ROOT 是唯一外部源码路径输入；
- 需求、约束、验收信息从 SOURCE_ROOT README 读取；
- README.md 负责作品说明；
- INSTRUCTION.md 负责环境准备、依赖安装、运行命令和结果获取；
- work/ 承载通用可运行框架；
- work/loopforge.config.yaml 只保存框架默认值；
- work/rules/loopforge/modes 可以保留，但必须是通用任务模式规则，不得绑定语言、历史项目、具体题目；
- result/ 和 logs/ 是评委可见输出；
- SOURCE_ROOT/.loopforge/ 只能作为内部 evidence，不是评委主输出。

请执行以下自检：
1. 根目录噪声检查：删除 SUBMISSION.md、config-templates、根目录修复过程文档。
2. README.md 和 INSTRUCTION.md 入口口径检查。
3. work/loopforge.config.yaml 框架默认配置检查。
4. work/rules/loopforge/modes 通用化检查。
5. work/skills 和 work/subagent 执行口径检查。
6. scripts SOURCE_ROOT 协议检查。
7. smoke-test 正向和负向场景检查。
8. runtime 输出文案检查。
9. result/logs 输出合同检查。
10. 全局旧模型 grep 检查。

如果自检不通过，请按本文档中的“不通过时修复”策略修复。

禁止：
- 不要写 Rust/C2Rust/FlashDB 业务规则；
- 不要把某个历史项目写入通用框架；
- 不要要求人工填写配置后才能运行；
- 不要把 code/ 作为唯一源码目录；
- 不要把 code/.loopforge/reports/final-report.md 作为主输出。

修复后请运行：

```bash
bash -n work/scripts/run.sh
bash -n work/scripts/bootstrap.sh
bash -n work/scripts/smoke-test.sh
bash work/scripts/smoke-test.sh
grep -R "fill-by-human\|Human adaptation must provide\|E:/009workspace\|SOURCE_ROOT= bash\|gulimall\|Gulimall" -n . --exclude-dir=.git || true
grep -R "FlashDB\|C2Rust\|Rust conversion" -n work README.md INSTRUCTION.md --exclude-dir=.git || true
```

最后输出修复报告，说明修改文件、删除文件、仍保留的 grep 命中项和原因。
```
