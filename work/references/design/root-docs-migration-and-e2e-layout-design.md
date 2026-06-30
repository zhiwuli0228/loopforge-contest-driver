# 根目录临时文档排查与迁移设计文档

> 适用范围：`loopforge-contest-driver` 当前 C-to-Rust 迁移作品  
> 目标：在不破坏无人托管执行链路的前提下，清理根目录临时设计/验收文档，避免评测 Agent 误判入口，同时保证历史设计证据可追溯。

---

## 1. 背景与问题

当前仓库根目录出现了以下非入口类 Markdown 文件：

```text
ACCEPTANCE_REPORT.md
c-to-rust-generic-harness-design.md
c-to-rust-generic-harness-self-checklist.md
c-to-rust-semantic-self-audit-harness-design.md
```

这些文件不是比赛明确要求的根目录交付件，但直接删除存在风险：

1. 某些脚本、README、Skill、Agent 或日志可能硬编码引用了这些路径。
2. `ACCEPTANCE_REPORT.md` 可能是三方验收证据，直接删除会丢失问题演进记录。
3. 设计文档可能被后续 Agent 用作参考，如果迁移后不更新引用，会导致文件找不到。
4. 根目录文档过多会干扰评测 Agent 判断真正入口，尤其是 `INSTRUCTION.md`。

因此本轮不能“直接删除”，应该按 **排查 → 分类 → 迁移 → 引用修正 → E2E 验证 → 提交** 的流程处理。

---

## 2. 目标

### 2.1 必须达成

- 根目录只保留正式入口和必要说明文件。
- 所有设计文档迁移到规范目录。
- 验收报告迁移到日志证据目录。
- 所有旧路径引用被修正。
- 无人托管执行链仍然可用。
- `INSTRUCTION.md` 仍然是唯一官方执行入口。
- `result/output.md` 能明确告诉评委生成 Rust 项目位置。
- 不影响 `work/output/<output_project_name>/` 的生成和验证。

### 2.2 不做事项

本轮不修改：

- C-to-Rust 翻译语义。
- semantic invariant 生成逻辑。
- repair loop。
- unsafe gate。
- skill 的语义规则。
- `work/output/flashDB_rust` 生成内容。
- `result/output.md` 的 READY/BLOCKED 判定逻辑，除非只是路径说明字段同步。

---

## 3. 比赛目录约束

比赛根目录关键交付件应聚焦在：

```text
/INSTRUCTION.md
/work
/result
/result/output.md
/logs
/logs/interaction.md
/logs/trace
```

根目录可以保留 `README.md`、`.gitignore`、`.gitattributes` 等普通工程文件，但不应堆放大量临时设计文档、旧验收报告或开发过程文档。

最终生成的 Rust 项目建议统一放在：

```text
work/output/<output_project_name>/
```

当前题面解析出的项目名为：

```text
work/output/flashDB_rust/
```

并应在以下位置明确说明：

```text
INSTRUCTION.md
INSTRUCTION.linux.md
result/output.md
logs/trace/run-summary.json
```

---

## 4. 问题分类

| 分类 | 问题 | 风险 | 处理方式 |
|---|---|---|---|
| P1 根目录污染 | 临时设计文档出现在根目录 | 干扰评测入口识别 | 迁移到 `work/references/design/` |
| P1 验收报告位置错误 | `ACCEPTANCE_REPORT.md` 出现在根目录 | 可能让评委误读旧失败结论 | 迁移到 `logs/trace/acceptance/` |
| P1 路径硬编码 | 旧文档路径被 README/脚本/Skill 引用 | 迁移后文件找不到 | 全仓扫描并修正引用 |
| P2 生成逻辑污染 | Agent 或脚本可能自动再生成 `SUBMISSION.md` / `ACCEPTANCE_REPORT.md` 到根目录 | 清理后再次出现 | 排查生成源，改到规范目录或禁止生成 |
| P2 状态目录污染 | 写入 `SOURCE_ROOT/.loopforge` | 污染输入源码目录 | 改为 `logs/trace/.loopforge` 或 `work/.loopforge` |
| P3 证据丢失 | 删除历史设计/验收文档 | 丢失排查依据 | 迁移而非删除 |
| P3 E2E 误判 | 清理后未重新跑无人托管测试 | 功能是否受影响未知 | 清理后必须跑一次 E2E |

---

## 5. 目标目录规范

### 5.1 设计文档归档目录

```text
work/references/design/
├── c-to-rust-generic-harness-design.md
├── c-to-rust-generic-harness-self-checklist.md
└── c-to-rust-semantic-self-audit-harness-design.md
```

说明：

- 这些文档是开发设计资产。
- 放在 `work/references/design/`，说明其为 harness 内部参考资料。
- 不作为评测入口。
- 不参与 `result` 判断。

### 5.2 三方验收报告归档目录

```text
logs/trace/acceptance/
├── ACCEPTANCE_REPORT.failed-20260630.md
└── ACCEPTANCE_REPORT.passed-<date>.md
```

说明：

- 验收报告属于执行证据和历史 trace。
- 如果是“不通过”的旧报告，不应放根目录。
- 通过版三方报告也应放在 `logs/trace/acceptance/`。
- `result/output.md` 可引用最新通过报告路径，但不要引用根目录路径。

### 5.3 正式输出目录

```text
work/output/
└── flashDB_rust/
    ├── Cargo.toml
    ├── src/
    └── tests/
```

说明：

- 生成的 Rust 项目统一落在 `work/output/`。
- 不输出到根目录 `./flashDB_rust`。
- 不输出到 `SOURCE_ROOT` 内部。
- 不输出到 `SOURCE_ROOT.parent`。
- `INSTRUCTION.md` 和 `result/output.md` 必须明确该路径。

---

## 6. 排查流程

### 6.1 查看根目录 Markdown 文件

Windows PowerShell：

```powershell
Get-ChildItem -File *.md | Select-Object Name,Length,LastWriteTime
```

Linux Bash：

```bash
find . -maxdepth 1 -type f -name "*.md" -printf "%f\n"
```

预期根目录最多保留：

```text
INSTRUCTION.md
INSTRUCTION.linux.md
README.md
```

如保留其他 Markdown，必须有明确理由。

---

### 6.2 检查这些文件是否被引用

Windows PowerShell：

```powershell
$targets = @(
  "ACCEPTANCE_REPORT.md",
  "c-to-rust-generic-harness-design.md",
  "c-to-rust-generic-harness-self-checklist.md",
  "c-to-rust-semantic-self-audit-harness-design.md",
  "SUBMISSION.md"
)

foreach ($t in $targets) {
  Write-Host "`n=== $t ==="
  Select-String -Path .\* -Pattern $t -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -notmatch "\\.git\\" }
}
```

Linux Bash：

```bash
grep -R \
  -e "ACCEPTANCE_REPORT.md" \
  -e "c-to-rust-generic-harness-design.md" \
  -e "c-to-rust-generic-harness-self-checklist.md" \
  -e "c-to-rust-semantic-self-audit-harness-design.md" \
  -e "SUBMISSION.md" \
  --exclude-dir=.git \
  .
```

处理规则：

- 如果无引用：直接迁移。
- 如果 `README.md`、`INSTRUCTION.md`、Skill 或脚本有引用：同步改成新路径。
- 如果 runtime 会自动生成这些文件到根目录：修改生成逻辑或禁止生成。
- 如果只在历史日志里出现：可以保留历史日志，不必强制改。

---

### 6.3 检查 `SOURCE_ROOT/.loopforge` 写入逻辑

Windows PowerShell：

```powershell
Select-String -Path work\**\* -Pattern "\.loopforge","SOURCE_ROOT","source_root" -Recurse -ErrorAction SilentlyContinue
```

Linux Bash：

```bash
grep -R "\.loopforge\|SOURCE_ROOT\|source_root" work --exclude-dir=.git
```

重点查找：

```text
SOURCE_ROOT/.loopforge
source_root / ".loopforge"
source_root.join(".loopforge")
Path(source_root) / ".loopforge"
```

处理规则：

- 禁止写入 `SOURCE_ROOT/.loopforge`。
- 如需 adapter 状态，写入：
  - `logs/trace/.loopforge/`
  - 或 `work/.loopforge/`
- `SOURCE_ROOT` 只能读取，不应写入框架状态。

---

### 6.4 检查输出目录硬编码

Windows PowerShell：

```powershell
Select-String -Path work\**\* -Pattern "flashDB_rust","work/output","work\\output","./flashDB_rust",".\\flashDB_rust" -Recurse -ErrorAction SilentlyContinue
```

Linux Bash：

```bash
grep -R "flashDB_rust\|work/output\|work\\\\output\|./flashDB_rust\|.\\\\flashDB_rust" work --exclude-dir=.git
```

处理规则：

- `work/output/<output_project_name>` 是允许的。
- `flashDB_rust` 作为当前题面解析结果可以出现在：
  - `work/code/README.md`
  - `result/output.md`
  - `logs/trace`
  - `work/output/flashDB_rust`
  - `INSTRUCTION.md` 的“当前题面示例”部分
- 不应作为 runtime 的固定默认逻辑。
- runtime 应基于 `output_project_name` 动态生成输出目录。

---

## 7. 迁移方案

### 7.1 新建归档目录

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force work\references\design | Out-Null
New-Item -ItemType Directory -Force logs\trace\acceptance | Out-Null
```

Linux Bash：

```bash
mkdir -p work/references/design
mkdir -p logs/trace/acceptance
```

---

### 7.2 迁移设计文档

如果文件已被 Git 跟踪，使用 `git mv`：

```powershell
git mv c-to-rust-generic-harness-design.md work\references\design\c-to-rust-generic-harness-design.md
git mv c-to-rust-generic-harness-self-checklist.md work\references\design\c-to-rust-generic-harness-self-checklist.md
git mv c-to-rust-semantic-self-audit-harness-design.md work\references\design\c-to-rust-semantic-self-audit-harness-design.md
```

如果未被 Git 跟踪，可以用：

```powershell
Move-Item c-to-rust-generic-harness-design.md work\references\design\ -Force
Move-Item c-to-rust-generic-harness-self-checklist.md work\references\design\ -Force
Move-Item c-to-rust-semantic-self-audit-harness-design.md work\references\design\ -Force
```

---

### 7.3 迁移验收报告

如果当前 `ACCEPTANCE_REPORT.md` 是旧失败报告：

```powershell
git mv ACCEPTANCE_REPORT.md logs\trace\acceptance\ACCEPTANCE_REPORT.failed-20260630.md
```

或：

```powershell
Move-Item ACCEPTANCE_REPORT.md logs\trace\acceptance\ACCEPTANCE_REPORT.failed-20260630.md -Force
```

如果是最新通过报告，命名为：

```text
logs/trace/acceptance/ACCEPTANCE_REPORT.passed-<date>.md
```

---

### 7.4 处理 `SUBMISSION.md`

`SUBMISSION.md` 不是比赛必选根目录文件。处理方式：

1. 检查是否存在：

```powershell
Test-Path SUBMISSION.md
```

2. 检查是否被生成或引用：

```powershell
Select-String -Path .\* -Pattern "SUBMISSION.md" -Recurse -ErrorAction SilentlyContinue |
  Where-Object { $_.Path -notmatch "\\.git\\" }
```

3. 如无必要，删除：

```powershell
Remove-Item SUBMISSION.md -Force -ErrorAction SilentlyContinue
```

4. 如需要保留内容，迁移到：

```text
work/references/design/SUBMISSION.note.md
```

但不建议保留为根目录文件。

---

## 8. 引用修正规则

迁移后必须将旧路径改为新路径：

| 旧路径 | 新路径 |
|---|---|
| `c-to-rust-generic-harness-design.md` | `work/references/design/c-to-rust-generic-harness-design.md` |
| `c-to-rust-generic-harness-self-checklist.md` | `work/references/design/c-to-rust-generic-harness-self-checklist.md` |
| `c-to-rust-semantic-self-audit-harness-design.md` | `work/references/design/c-to-rust-semantic-self-audit-harness-design.md` |
| `ACCEPTANCE_REPORT.md` | `logs/trace/acceptance/ACCEPTANCE_REPORT.failed-20260630.md` 或最新 passed 报告 |
| `SUBMISSION.md` | 删除，或迁移到 `work/references/design/SUBMISSION.note.md` |

检查命令：

```powershell
Select-String -Path .\* -Pattern "c-to-rust-generic-harness-design.md","c-to-rust-generic-harness-self-checklist.md","c-to-rust-semantic-self-audit-harness-design.md","ACCEPTANCE_REPORT.md","SUBMISSION.md" -Recurse -ErrorAction SilentlyContinue |
  Where-Object { $_.Path -notmatch "\\.git\\" }
```

预期：

- 不应命中旧根目录路径。
- 若命中新路径，是可接受的。
- 若在历史日志里命中旧路径，可保留，但不要作为当前入口引用。

---

## 9. `INSTRUCTION.md` 同步要求

`INSTRUCTION.md` 应保持简洁，不能写开发 Prompt。必须明确：

```text
1. 如何传入 SOURCE_ROOT
2. 如何执行官方命令
3. 生成 Rust 项目位置
4. 手工 cargo 验证命令
5. result/logs 位置
6. READY/BLOCKED 判断方式
```

建议关键内容：

```md
## Run

```bash
SOURCE_ROOT="/absolute/path/to/source/project" bash work/scripts/run.sh --run
```

## Generated Rust Project

The generated Rust project is written to:

```text
work/output/<output_project_name>/
```

For the current FlashDB task:

```text
work/output/flashDB_rust/
```

Manual verification:

```bash
cd work/output/flashDB_rust
cargo build --locked
cargo test --locked -- --nocapture
```

## Reports

```text
result/output.md
result/issues/00-summary.md
logs/interaction.md
logs/trace/
```
```

`INSTRUCTION.linux.md` 应与最终 `INSTRUCTION.md` 保持一致或作为备份，不要互相冲突。

---

## 10. `result/output.md` 同步要求

执行后 `result/output.md` 必须明确写：

```text
status: READY_FOR_EVALUATION
rust_project: work/output/flashDB_rust
cargo_toml: work/output/flashDB_rust/Cargo.toml
semantic_audit_report: logs/trace/c-to-rust/semantic-audit-report.md
```

如果失败：

```text
status: BLOCKED_WITH_REPORT
first_blocking_point: <A/B/C/D/E/F/G>
```

严禁在 `result/output.md` 中写旧位置：

```text
flashDB_rust/Cargo.toml
./flashDB_rust
.code/flashDB_rust
SOURCE_ROOT/flashDB_rust
```

除非是历史 trace，不作为当前结果。

---

## 11. E2E 清理与验证

### 11.1 清理命令

Windows PowerShell：

```powershell
Remove-Item -Recurse -Force result -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force logs\trace -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force work\output -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force flashDB_rust -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .code\flashDB_rust -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force code\flashDB_rust -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Force result\issues | Out-Null
New-Item -ItemType Directory -Force logs\trace | Out-Null
New-Item -ItemType Directory -Force work\output | Out-Null
```

Linux Bash：

```bash
rm -rf result
rm -rf logs/trace
rm -rf work/output
rm -rf flashDB_rust
rm -rf .code/flashDB_rust
rm -rf code/flashDB_rust

mkdir -p result/issues
mkdir -p logs/trace
mkdir -p work/output
```

---

### 11.2 无人托管执行

Windows：

```powershell
powershell -ExecutionPolicy Bypass -File work\scripts\run.ps1 -SourceRoot ".code\FlashDB"
```

Linux：

```bash
SOURCE_ROOT=".code/FlashDB" bash work/scripts/run.sh --run
```

---

### 11.3 验收检查

Windows PowerShell：

```powershell
Test-Path work\output\flashDB_rust\Cargo.toml
Test-Path work\output\flashDB_rust\src
Test-Path work\output\flashDB_rust\tests
Test-Path result\output.md
Test-Path result\issues\00-summary.md
Test-Path logs\interaction.md
Test-Path logs\trace\c-to-rust\semantic-audit-report.md

Push-Location work\output\flashDB_rust
cargo build --locked
cargo test --locked -- --nocapture
Pop-Location
```

Linux Bash：

```bash
test -f work/output/flashDB_rust/Cargo.toml
test -d work/output/flashDB_rust/src
test -d work/output/flashDB_rust/tests
test -f result/output.md
test -f result/issues/00-summary.md
test -f logs/interaction.md
test -f logs/trace/c-to-rust/semantic-audit-report.md

cd work/output/flashDB_rust
cargo build --locked
cargo test --locked -- --nocapture
```

---

## 12. Git 提交流程

### 12.1 迁移前检查

```powershell
git status --short
```

### 12.2 迁移并修正引用

执行第 7、8 节动作。

### 12.3 运行检查

```powershell
git diff --check
git status --short
```

### 12.4 端到端执行

执行第 11 节 E2E。

### 12.5 提交

建议拆分为两个提交：

#### Commit 1：目录归档与引用修正

```text
Normalize root documentation layout
```

包含：

```text
work/references/design/*
logs/trace/acceptance/*
删除或迁移 SUBMISSION.md
引用修正
```

#### Commit 2：输出目录与说明同步

```text
Align output project location and evaluator instructions
```

包含：

```text
INSTRUCTION.md
INSTRUCTION.linux.md
runtime 输出路径同步
result 输出字段同步
run-e2e-win.ps1 路径同步
```

如果本轮只做目录归档，不改输出目录，则只做 Commit 1。

---

## 13. 验收标准

### 13.1 根目录标准

根目录不应存在：

```text
ACCEPTANCE_REPORT.md
c-to-rust-generic-harness-design.md
c-to-rust-generic-harness-self-checklist.md
c-to-rust-semantic-self-audit-harness-design.md
SUBMISSION.md
```

根目录应保留：

```text
INSTRUCTION.md
INSTRUCTION.linux.md
README.md
work/
result/
logs/
```

### 13.2 引用标准

旧路径不能被当前执行文档引用：

```text
ACCEPTANCE_REPORT.md
SUBMISSION.md
c-to-rust-generic-harness-design.md
c-to-rust-generic-harness-self-checklist.md
c-to-rust-semantic-self-audit-harness-design.md
```

允许出现在历史 trace 中，但不能作为当前入口或当前结果引用。

### 13.3 输出标准

```text
work/output/flashDB_rust/Cargo.toml
work/output/flashDB_rust/src/
work/output/flashDB_rust/tests/
```

必须存在。

根目录旧输出：

```text
./flashDB_rust/
```

不应存在。

### 13.4 报告标准

`result/output.md` 必须包含：

```text
READY_FOR_EVALUATION
work/output/flashDB_rust
work/output/flashDB_rust/Cargo.toml
semantic-audit-report.md
```

### 13.5 执行标准

无人托管执行必须通过：

```text
cargo build --locked
cargo test --locked -- --nocapture
semantic gate
unsafe gate
```

### 13.6 输入源码保护

不得生成或修改：

```text
SOURCE_ROOT/.loopforge
SOURCE_ROOT/flashDB_rust
SOURCE_ROOT/tests/*
SOURCE_ROOT/src/*
```

---

## 14. 回滚策略

如果迁移后 E2E 失败：

1. 先看 `result/issues/00-summary.md`。
2. 再看 `logs/trace/c-to-rust/06-verification-report.md`。
3. 再看 `logs/trace/c-to-rust/semantic-audit-report.md`。
4. 如果失败原因是找不到迁移后的设计文档：
   - 搜索旧路径引用。
   - 改为新路径。
5. 如果失败原因是找不到 Rust 输出项目：
   - 检查 `output_project_dir` 是否统一为 `work/output/<output_project_name>`。
6. 不要直接回滚 semantic audit 和 repair loop。
7. 不要手工移动生成项目来掩盖失败。

---

## 15. 最终结论

本轮处理重点不是简单删除根目录文档，而是：

```text
排查引用 → 规范迁移 → 修正引用 → 保持入口清晰 → E2E 验证
```

完成后，根目录应只暴露正式入口和必要说明；设计资产进入 `work/references/design/`；验收证据进入 `logs/trace/acceptance/`；生成 Rust 项目进入 `work/output/<output_project_name>/`；最终由 `INSTRUCTION.md` 和 `result/output.md` 明确告诉评测 Agent 与评委去哪里找输出结果。
