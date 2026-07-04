# 通用代理自验证清单与验收标准

## 1. 命名通用化检查

### 1.1 禁止旧专用路径残留

```bash
grep -R "c2r-migration\|c2r_migration" -n work INSTRUCTION.md README.md || true
```

验收：无命中。

### 1.2 禁止框架层出现题目专用名称

```bash
grep -R "<source_project>\|<output_project>\|fdb_\|kvdb\|tsdb" -n \
  work/runtime work/skills work/profiles work/rules work/subagent INSTRUCTION.md README.md || true
```

验收：无命中。

说明：`work/code/README.md`、`SOURCE_ROOT/README*`、`result/`、`logs/`、生成的输出目录不在该检查范围内。

## 2. 文件路径检查

```bash
test -f work/skills/c-to-rust-migration/SKILL.md
test ! -d work/skills/c2r-migration-migration

test -f work/profiles/examples/c-to-rust-migration.yaml
test ! -f work/profiles/examples/c2r-migration-migration.yaml

test -d work/rules/loopforge/adapters/c-to-rust
test ! -d work/rules/loopforge/adapters/c2r-migration

test -f work/subagent/c-to-rust-source-inventory-subagent.md
test -f work/subagent/c-to-rust-api-mapping-subagent.md
test -f work/subagent/c-to-rust-implementation-subagent.md
test -f work/subagent/c-to-rust-test-migration-subagent.md
test -f work/subagent/c-to-rust-verification-subagent.md
test -f work/subagent/c-to-rust-final-report-subagent.md
! ls work/subagent/c2rust-*.md >/dev/null 2>&1
```

验收：所有命令返回 0。

## 3. 配置检查

```bash
grep -n "profiles/examples/c-to-rust-migration.yaml" work/loopforge.config.yaml
grep -n "skills/c-to-rust-migration/SKILL.md" work/loopforge.config.yaml
grep -n "logs/trace/c-to-rust" work/loopforge.config.yaml
grep -n "SOURCE_README_DERIVED_OUTPUT_PROJECT" work/loopforge.config.yaml
```

验收：全部命中。

```bash
grep -n "c2r-migration\|c2rust/\|<output_project>\|<source_project>" work/loopforge.config.yaml || true
```

验收：无命中。

## 4. Runtime 去硬编码检查

```bash
# 替换下方 <source_project_terms> 为当前题目特有的 API 名称、类型名、变量名
grep -R "<source_project_terms>" -n work/runtime || true
grep -R "<project_specific_types>\|<project_specific_patterns>" -n work/runtime || true
grep -R "<project_prefix_>\|<project_module_>\|<source_project>\|<output_project>" -n work/runtime || true
```

验收：无命中。

## 5. 主执行链检查

```bash
grep -n "analyze_source" work/runtime/loopforge_runner.py
grep -n "generate_project" work/runtime/loopforge_runner.py
grep -n "run_repair_loop" work/runtime/loopforge_runner.py
grep -n "evaluate_semantic_equivalence" work/runtime/loopforge_runner.py
grep -n "verify_generated" work/runtime/loopforge_runner.py
```

验收：全部命中。

```bash
grep -n "detect_project().*verify\|verify().*finalize" work/runtime/loopforge_runner.py || true
```

验收：不能命中旧主链。

## 6. 语法检查

```bash
bash -n work/scripts/run.sh
python -m py_compile work/runtime/loopforge_runner.py
python -m py_compile work/runtime/agent_task_packet.py
python -m py_compile work/runtime/c2rust_analysis.py
python -m py_compile work/runtime/c2rust_project_generator.py
python -m py_compile work/runtime/c2rust_repair.py
python -m py_compile work/runtime/check_unsafe_ratio.py
```

验收：全部通过。

## 7. Source-root 解析检查

```bash
grep -n "SOURCE_ROOT" work/scripts/run.sh
grep -n ".code" work/scripts/run.sh
grep -n "code" work/scripts/run.sh
```

验收：支持显式 `SOURCE_ROOT`，也支持本地 `.code` / `code` fallback。不得要求人工交互。

## 8. 运行前清理

```bash
rm -rf rust_migration_output <output_project>
rm -rf logs/trace/c-to-rust
mkdir -p logs/trace
```

验收：命令成功。

## 9. 真实运行检查

使用当前比赛题面本地输入时执行：

```bash
SOURCE_ROOT="work/code/<source_project>" bash work/scripts/run.sh --run
```

验收：

```bash
test -f result/output.md
test -f result/issues/00-summary.md
test -d logs/trace/c-to-rust
test -f logs/trace/c-to-rust/01-source-inventory.json
test -f logs/trace/c-to-rust/02-api-mapping.json
test -f logs/trace/c-to-rust/04-test-mapping.json
```

若题面要求输出项目名为 `<output_project>`，则运行结果允许生成：

```bash
test -f <output_project>/Cargo.toml
test -d <output_project>/src
test -d <output_project>/tests
```

注意：这是运行时从题面推导出的结果，不是框架硬编码。

## 10. Rust 验证检查

如果已生成 Rust 输出项目：

```bash
cd <output_project>
cargo build
cargo test
cd -
```

验收：

- `cargo build` 通过，或 result/issues 明确记录 build 阻塞原因。
- `cargo test` 通过，或 result/issues 明确记录测试阻塞原因。
- 不允许在没有真实通过的情况下写 `READY_FOR_EVALUATION`。

## 11. Unsafe 检查

```bash
python work/runtime/check_unsafe_ratio.py <output_project> --max-ratio 0.10
```

验收：

- unsafe ratio 小于等于题面/README/profile 推导出的阈值；
- 若失败，`result/issues/00-summary.md` 必须记录 unsafe gate failure。

## 12. 语义门禁检查

```bash
grep -n "semantic_gate" result/output.md
grep -n "semantic" result/issues/00-summary.md logs/trace/c-to-rust/* || true
```

验收：

- semantic gate 必须基于 test mapping / API mapping / unsupported behavior list；
- 不能只因为 `cargo test` 通过就声明语义等价；
- 如果仅生成 source-driven scaffold，必须写 `semantic_equivalence_claim: not_claimed` 或等价说明。

## 13. 输出污染检查

```bash
grep -R "[A-Z]:\\\\\|/Users/\|/home/[^/]*/\|009workspace" -n result logs work || true
```

验收：无本地绝对路径污染。

```bash
grep -R "SOURCE_ROOT/.loopforge\|\.code/.loopforge" -n work result logs || true
```

验收：无命中。过程产物必须在 `logs/trace`，结论产物必须在 `result`。

## 14. 最终状态判定

### READY_FOR_EVALUATION 条件

只有同时满足以下条件，`result/output.md` 才能写：

```text
READY_FOR_EVALUATION
```

条件：

1. 成功解析 source README/READNE 或 task README。
2. 成功推导 source dirs、test dirs、output project、build commands、unsafe threshold。
3. 成功生成 Rust 输出项目。
4. Rust 输出项目包含 `Cargo.toml`、`src/`、`tests/`。
5. `cargo build` 通过。
6. `cargo test` 通过。
7. unsafe ratio 通过。
8. semantic gate 通过，且不是仅凭 cargo test。
9. `logs/trace/c-to-rust` 包含 source inventory、API mapping、test mapping、repair/verification evidence。
10. `result/issues/00-summary.md` 无 blocking issue。

### BLOCKED_WITH_REPORT 条件

如果任一关键 gate 失败，必须写：

```text
BLOCKED_WITH_REPORT
```

并在 `result/issues/00-summary.md` 中列出：

```text
failed_gate
root_cause
evidence_file
repair_attempted
remaining_action
```

禁止把失败包装成 READY。
