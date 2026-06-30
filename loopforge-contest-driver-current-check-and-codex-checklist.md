# LoopForge Contest Driver 当前检查结果与 Codex 自检修复 Checklist

> 目标：给 Codex 一份可执行的自检与修复清单。Codex 必须先读取当前远端/本地仓库真实状态，再按本清单完成最小闭环修复。不要机械套模板，不要扩展到业务转换逻辑。

---

## 1. 当前检查结论

当前 `master` 分支已经完成了一部分入口与目录修复，但仍未完成“源码 README 驱动的快速需求开发输入模型”简化。

综合判断：

| 模块 | 当前状态 | 结论 |
|---|---|---|
| 根目录 `INSTRUCTION.md` | 已从旧业务混合文档收敛为入口路由文档，但环境准备、依赖安装、调用命令说明不足 | 部分通过 |
| `work/` 目录 | 已存在，且包含 runtime、scripts、skills、subagent 等资产 | 通过 |
| `result/` 与 `logs/` | 已存在，满足基本输出目录形态 | 通过 |
| `work/scripts/run.sh` | 已成为较新的统一入口，但目前未显式完成 `SOURCE_ROOT` fallback 与 README 输入模型说明 | 部分通过 |
| `work/scripts/bootstrap.sh` | 仍保留旧 `CODE_DIR=code`、`--code-dir` 模型 | 不通过 |
| `work/loopforge.config.yaml` | 仍存在 `fill-by-human`、`human-configured`、人工 verification 命令模型 | 不通过 |
| README | 仍有本机绝对路径链接和复杂 LoopForge 平台模型描述 | 不通过 |
| `work/README.md` | 仍保留 `Human adaptation must provide verification.commands` | 不通过 |
| `work/skills/loopforge-driver/SKILL.md` | 仍以 `work/loopforge.config.yaml` 为需求输入源，输出仍偏向 `code/.loopforge/reports/final-report.md` | 不通过 |

当前主要问题不是目录，而是：

```text
需求输入模型仍然过重。
比赛环境中，需求与约束应从源码目录 README 读取；参赛包不应要求人工填写复杂配置。
```

---

## 2. 修复边界

### 2.1 本轮要修

只修以下内容：

1. README 与 INSTRUCTION 的复现入口说明；
2. 源码路径输入协议；
3. `SOURCE_ROOT` 与 `code` fallback；
4. 从源码 README 读取需求与约束的框架入口；
5. 去除阻断自动执行的人工配置占位；
6. 统一 `run.sh/run.ps1/bootstrap.sh/bootstrap.ps1` 的入口模型；
7. 同步 `work/skills/loopforge-driver/SKILL.md` 的任务输入源描述；
8. 保证结果仍落到 `result/output.md`、问题摘要落到 `result/issues/00-summary.md`、日志落到 `logs/trace/`。

### 2.2 本轮不要修

不要做以下事情：

1. 不实现具体 C2Rust 转换逻辑；
2. 不生成 `flashDB_rust`；
3. 不重写 Rust 业务策略；
4. 不修改平台提供的源码材料；
5. 不引入复杂交互式配置；
6. 不把 README 写成业务题解；
7. 不把 `INSTRUCTION.md` 写成业务规则全文；
8. 不让工具依赖人工填写 `fill-by-human`。

---

## 3. 目标输入模型

### 3.1 唯一外部输入

工具外部输入应收敛为：

```text
SOURCE_ROOT
```

也就是源码根路径。

### 3.2 需求与约束来源

需求、约束、验收信息应来自：

```text
${SOURCE_ROOT}/README.md
${SOURCE_ROOT}/README
${SOURCE_ROOT}/readme.md
${SOURCE_ROOT}/Readme.md
```

如果存在多个 README，优先读取最接近源码根目录的 README，并在日志中记录实际采用的 README 路径。

### 3.3 路径解析优先级

Codex 必须确保入口脚本和文档统一表达以下优先级：

```text
1. 平台调用时显式传入的源码路径；
2. 命令行参数 --source-root；
3. 环境变量 SOURCE_ROOT；
4. Agent 从自然语言中识别出的源码路径，并转为 SOURCE_ROOT；
5. Linux 环境默认绝对路径占位：/__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB；
6. Windows / 本地开发默认相对路径：code；
```

说明：Linux 绝对路径现在可以保留占位，不需要猜测真实平台路径。

---

## 4. Codex 自主读取要求

Codex 开始修复前，必须自主读取当前项目，而不是基于旧记忆改文件。

### 4.1 必须读取的文件

```bash
sed -n '1,220p' INSTRUCTION.md
sed -n '1,260p' README.md
sed -n '1,260p' work/README.md
sed -n '1,260p' work/HARNESS.md
sed -n '1,260p' work/loopforge.config.yaml
sed -n '1,260p' work/skills/loopforge-driver/SKILL.md
sed -n '1,220p' work/scripts/run.sh
sed -n '1,220p' work/scripts/run.ps1
sed -n '1,220p' work/scripts/bootstrap.sh
sed -n '1,220p' work/scripts/bootstrap.ps1
python work/runtime/loopforge_runner.py --help || true
```

### 4.2 必须搜索的旧模型残留

```bash
grep -R "fill-by-human\|human-configured\|Human adaptation\|verification.commands\|code/.loopforge/reports/final-report.md\|E:/\|--code-dir\|CODE_DIR" -n \
  INSTRUCTION.md README.md work result logs 2>/dev/null || true
```

Codex 必须根据搜索结果决定具体改动点。不要只改一个文件后停止。

---

## 5. 文件级修复 Checklist

### 5.1 根目录 `INSTRUCTION.md`

目标：作为评委、平台 Agent、人工复现者的执行入口。

必须包含：

- [ ] 说明运行环境要求：Linux bash / Windows PowerShell、Python、pip、Git、Rust/Cargo；
- [ ] 说明 Python venv 创建命令；
- [ ] 说明 `python -m pip install -r work/requirements.txt`；
- [ ] 说明如何传入 `SOURCE_ROOT` 或 `--source-root`；
- [ ] 说明平台自然语言路径需要 Agent 抽取成 `SOURCE_ROOT`；
- [ ] 说明 Linux fallback 使用 `/__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB`；
- [ ] 说明 Windows/local fallback 使用 `code`；
- [ ] 说明 Linux 调用命令：`SOURCE_ROOT=<path> bash work/scripts/run.sh`；
- [ ] 说明 Windows 调用命令：`$env:SOURCE_ROOT=<path>; powershell -File work/scripts/run.ps1`；
- [ ] 说明结果读取：`result/output.md`；
- [ ] 说明问题摘要：`result/issues/00-summary.md`；
- [ ] 说明日志目录：`logs/trace/`；
- [ ] 不承载业务转换规则；
- [ ] 不要求人工填写配置；
- [ ] 不指向 `code/.loopforge/reports/final-report.md` 作为评委主结果。

失败后修复动作：

- 如果 `INSTRUCTION.md` 仍像目录规范说明，重写为运行手册；
- 如果还出现 `skills/...` 旧路径，改为 `work/skills/...`；
- 如果还出现 `scripts/bootstrap.sh` 作为主入口，改为 `work/scripts/run.sh`；
- 如果还出现 `code/.loopforge/reports/final-report.md` 作为主输出，改为 `result/output.md`。

---

### 5.2 根目录 `README.md`

目标：给评委快速理解作品与复现入口。

必须满足：

- [ ] 所有链接使用相对路径，不允许 `E:/...`、`C:/...` 等本机绝对路径；
- [ ] 明确复现入口是根目录 `INSTRUCTION.md`；
- [ ] 明确执行结果看 `result/output.md`；
- [ ] 明确日志看 `logs/trace/`；
- [ ] 删除或弱化“Human adaptation must provide verification.commands”；
- [ ] 删除或弱化“Tasks are configured through Mode + Profile”作为比赛主流程的描述；
- [ ] 明确比赛输入模型是 `SOURCE_ROOT + 源码 README`。

失败后修复动作：

- 如果 README 仍以 LoopForge 通用平台为主，压缩为参赛包说明；
- 如果 README 仍保留本机绝对链接，全部改为 `[INSTRUCTION.md](./INSTRUCTION.md)` 形式；
- 如果 README 仍要求人工配置 verification，改成“框架可自动从源码 README 建立任务上下文，验证由任务/框架自动解析或降级报告”。

---

### 5.3 `work/loopforge.config.yaml`

目标：配置只承载框架默认参数，不承载具体需求。

必须满足：

- [ ] 不存在 `fill-by-human`；
- [ ] 不存在 `human-configured` 作为阻断执行的 verification source；
- [ ] 不要求人工填写 `task.name`、`language.primary`、`objective`；
- [ ] task 可以使用通用默认值，例如 `source-readme-driven-development`；
- [ ] verification 不能只有 `fill-by-human-before-execution`；
- [ ] 输出路径需要兼容根目录 `result/output.md`；
- [ ] 如需保留 `code/.loopforge` 作为内部运行缓存，必须明确它不是评委主结果。

建议方向：

```yaml
platform:
  layout: "contest-root"
  work_dir: "work"
  local_fallback_source_dir: "code"
  artifact_dir: ".loopforge"

task:
  name: "source-readme-driven-development"
  mode: "feature-development"
  source: "source-readme"
  readme_required: true

execution:
  unattended: true
  max_repair_rounds: 2
  fail_soft: true
  always_finalize: true

verification:
  source: "source-readme-or-framework-default"
  timeout_seconds: 300
  commands:
    default: []

outputs:
  result_report: "result/output.md"
  issue_summary: "result/issues/00-summary.md"
  trace_dir: "logs/trace"
```

Codex 可以根据 runner 实际参数调整字段名称，但语义必须满足：**不再依赖人工填写需求与验证命令**。

---

### 5.4 `work/scripts/run.sh`

目标：Linux 主入口。

必须满足：

- [ ] 支持 `--source-root <path>`；
- [ ] 支持环境变量 `SOURCE_ROOT`；
- [ ] 如果都没有，Linux fallback 为 `/__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB`；
- [ ] 如果 Linux fallback 不存在，允许 fallback 到 `code`，并在日志说明；
- [ ] 创建 `result/issues`、`logs/trace`；
- [ ] 调用 runner 时传入源码路径；
- [ ] 不依赖人工编辑 config；
- [ ] 不把 `code` 固定为唯一源码路径。

建议逻辑：

```bash
SOURCE_ROOT="${SOURCE_ROOT:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source-root)
      SOURCE_ROOT="$2"
      shift 2
      ;;
    *)
      EXTRA_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ -z "$SOURCE_ROOT" ]]; then
  if [[ "$(uname -s 2>/dev/null)" == "Linux" && -d "/__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB" ]]; then
    SOURCE_ROOT="/__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB"
  else
    SOURCE_ROOT="code"
  fi
fi

export SOURCE_ROOT
```

Codex 必须结合 `loopforge_runner.py --help` 确认实际参数名。如果 runner 不支持 `--source-root`，则以兼容方式映射到现有 `--code-dir`，但对外入口仍叫 `SOURCE_ROOT`。

---

### 5.5 `work/scripts/run.ps1`

目标：Windows 本地复现入口。

必须满足：

- [ ] 支持 `-SourceRoot` 参数；
- [ ] 支持 `$env:SOURCE_ROOT`；
- [ ] 默认使用 `code`；
- [ ] 调用 runner 时传入源码路径；
- [ ] 不要求人工编辑 config。

---

### 5.6 `work/scripts/bootstrap.sh` / `bootstrap.ps1`

目标：不再维护第二套旧入口。

允许两种方案：

#### 方案 A：废弃为兼容入口

bootstrap 内部直接转调 run：

```bash
exec "${ROOT_DIR}/work/scripts/run.sh" "$@"
```

#### 方案 B：保留但同步 SOURCE_ROOT 协议

如果保留 bootstrap，必须满足：

- [ ] 支持 `SOURCE_ROOT`；
- [ ] 支持 `--source-root`；
- [ ] 不再默认固定 `CODE_DIR=${ROOT_DIR}/code` 作为唯一模式；
- [ ] 不再输出旧模型自检报告误导评委。

推荐方案 A，减少入口分叉。

---

### 5.7 `work/README.md`

目标：作为 work 内部资产说明，不再要求人工配置新需求。

必须满足：

- [ ] 删除或重写 `Human adaptation must provide verification.commands`；
- [ ] 明确 `work/` 是运行资产区；
- [ ] 明确需求输入来自 `SOURCE_ROOT/README*`；
- [ ] 明确 `work/loopforge.config.yaml` 只保留框架默认参数；
- [ ] 不再把 `code/.loopforge/reports/final-report.md` 描述成最终评委主结果。

---

### 5.8 `work/skills/loopforge-driver/SKILL.md`

目标：让 Agent skill 与新输入模型一致。

必须满足：

- [ ] Required Inputs 中加入 `SOURCE_ROOT` 和 `${SOURCE_ROOT}/README*`；
- [ ] 不再把 `work/loopforge.config.yaml` 描述为需求、目标、语言、验证命令的唯一来源；
- [ ] 允许读取 config 作为框架默认参数；
- [ ] 明确第一步是解析源码 README，形成任务上下文；
- [ ] 输出期望中必须包含 `result/output.md`；
- [ ] 问题摘要必须包含 `result/issues/00-summary.md`；
- [ ] 运行日志必须包含 `logs/trace/`；
- [ ] 不要求人工补 verification commands；
- [ ] 不要求缺少 subagent 时直接阻断全部比赛执行，除非该任务模式确实强依赖 subagent。

---

### 5.9 Runtime / Runner

目标：只做必要适配，不大改业务。

Codex 必须先读取 `work/runtime/loopforge_runner.py`，确认当前参数。

必须满足：

- [ ] runner 能接收或等价接收源码路径；
- [ ] runner 能记录实际采用的源码路径；
- [ ] runner 能尝试读取源码 README；
- [ ] 如果源码 README 缺失，写入 `result/issues/00-summary.md`，而不是等待人工输入；
- [ ] runner 最终必须保证 `result/output.md` 存在；
- [ ] runner 失败时也必须写 `logs/trace/run-summary.json` 或等价日志。

如果 runner 改动风险较大，允许先在 `run.sh/run.ps1` 做兼容层，把 `SOURCE_ROOT` 映射到已有 `--code-dir`。

---

## 6. 全局禁止项 Checklist

修复完成后，以下命令应无危险结果：

```bash
grep -R "fill-by-human" -n INSTRUCTION.md README.md work result logs 2>/dev/null
```

应无结果。

```bash
grep -R "Human adaptation must provide" -n INSTRUCTION.md README.md work result logs 2>/dev/null
```

应无结果。

```bash
grep -R "E:/\|C:/Users\|D:/" -n INSTRUCTION.md README.md work result logs 2>/dev/null
```

应无结果。

```bash
grep -R "code/.loopforge/reports/final-report.md" -n INSTRUCTION.md README.md work result logs 2>/dev/null
```

允许在“内部缓存/兼容说明”中出现，但不得作为评委主结果路径。如果出现，Codex 必须人工判读上下文并修正误导性描述。

```bash
grep -R "verification.commands" -n INSTRUCTION.md README.md work result logs 2>/dev/null
```

允许在历史/兼容说明中出现，但不得表达为“人工必须填写后才能执行”。

---

## 7. 最终验收命令

Codex 修复后必须执行：

```bash
test -f INSTRUCTION.md
test -d work
test -f work/requirements.txt
test -f work/scripts/run.sh
test -f work/scripts/run.ps1
test -f work/skills/loopforge-driver/SKILL.md
test -d result
test -f result/output.md
test -d result/issues
test -f result/issues/00-summary.md
test -d logs
test -f logs/interaction.md
test -d logs/trace
```

入口自检：

```bash
bash work/scripts/run.sh --help || true
SOURCE_ROOT="code" bash work/scripts/run.sh || true
```

如果没有真实源码，允许失败，但必须满足：

- `result/output.md` 存在；
- `result/issues/00-summary.md` 存在；
- `logs/trace/` 有运行记录；
- 失败原因是“源码/README 缺失或业务未执行”，不是“人工配置缺失”。

残留检查：

```bash
grep -R "fill-by-human\|Human adaptation must provide\|E:/\|C:/Users" -n \
  INSTRUCTION.md README.md work result logs 2>/dev/null && exit 1 || true
```

路径检查：

```bash
grep -R "SOURCE_ROOT\|--source-root\|source-root" -n \
  INSTRUCTION.md README.md work/scripts work/skills work/README.md 2>/dev/null
```

必须能看到明确的 SOURCE_ROOT 协议。

README 输入模型检查：

```bash
grep -R "README" -n INSTRUCTION.md README.md work/README.md work/skills/loopforge-driver/SKILL.md
```

必须能看到需求/约束从源码 README 读取的说明。

---

## 8. Codex 修复完成后的报告要求

Codex 最后必须输出一份简短修复报告，包含：

```text
1. 修改了哪些文件；
2. 删除了哪些旧模型残留；
3. SOURCE_ROOT 协议如何落地；
4. 源码 README 输入模型如何落地；
5. 哪些命令已执行；
6. 哪些命令未执行以及原因；
7. 当前是否仍存在已知风险。
```

不要输出长篇业务解释。

---

## 9. 通过标准

本轮修复通过的标准不是业务转换成功，而是：

```text
评委或平台 Agent 只需要阅读 README + INSTRUCTION.md，
准备 Python 环境，传入 SOURCE_ROOT 或使用默认路径，
执行 work/scripts/run.sh 或 run.ps1，
即可让框架自动从源码 README 建立任务上下文并产出 result/logs。
```

如果仍然需要人工填写 `work/loopforge.config.yaml` 中的新需求、目标、语言、验证命令，则本轮修复不通过。
