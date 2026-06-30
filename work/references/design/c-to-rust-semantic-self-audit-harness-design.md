# C-to-Rust 语义自查与回修 Harness 优化设计文档

> 版本：v1.0  
> 状态：待审核实施  
> 目标项目：`loopforge-contest-driver`  
> 阶段目标：将当前“流程型 harness”升级为“语义自查 + 失败回修 harness”，避免 `cargo test` 通过但语义不等价时误报 `READY_FOR_EVALUATION`。

---

## 1. 背景与结论

### 1.1 当前已具备能力

当前项目已经具备基本无人托管执行能力：

- 能通过 `INSTRUCTION.md` / 脚本入口启动执行。
- 能读取目标 C 项目源码路径。
- 能生成 Rust 项目。
- 能执行 `cargo build` / `cargo test`。
- 能生成 `result/output.md`、`result/issues/00-summary.md`、`logs/trace`。
- 能进行 unsafe 比例检查。
- 能输出基础 API mapping / test mapping / verification report。

这些能力说明项目已经具备 runner、generator、reporter、基础 verifier 的外壳。

### 1.2 暴露的问题

第三方端到端验收发现：

- 项目结构通过。
- `cargo build` 通过。
- `cargo test` 通过。
- unsafe 比例通过。
- 但存在可复现语义不等价缺陷。
- 当前 `result/output.md` 与 semantic gate 仍误报 `READY_FOR_EVALUATION`。

典型缺陷：

```rust
let mut db = FlashdbHandle::default();
flashdb_set(&mut db, "old", "value");
flashdb_new(&mut db);
flashdb_set(&mut db, "new", "value");
assert_eq!(flashdb_get(&db, "new"), Some("value".to_string()));
```

当前生成实现中，初始化函数只重置 `count`，但没有清空底层 `Vec`，导致后续 `push` 追加到旧记录之后；查询又只扫描 `take(count)` 范围，最终新记录不可查。

### 1.3 核心结论

当前项目不能只修生成的 Rust 代码，也不能只补一个测试用例。问题本质是：

> 当前 harness 是“流程型 harness”，不是“语义型 harness”。

需要新增：

1. 源码语义不变量提取。
2. 派生语义测试生成。
3. 严格 semantic gate。
4. verify 失败后的自动 repair loop。
5. 报告一致性约束，禁止 READY 误报。

---

## 2. 比赛约束与设计依据

### 2.1 题面硬约束

当前 C-to-Rust 题目要求包括：

- 从指定源码路径读取 FlashDB 源码。
- 重点处理 `FlashDB/src` 原始 C 代码。
- 迁移或等价覆盖 `FlashDB/tests` 原始 C 测试。
- 生成 Rust 项目 `flashDB_rust`。
- 项目包含 `Cargo.toml`、`src`、`tests`。
- 能执行 `cargo build` 和 `cargo test`。
- unsafe 使用比例低于 10%。
- 建议输出 `result/output.md` 和 `result/issues/00-summary.md`。

### 2.2 禁止项与风险点

自动评测失败风险包括：

- 缺少 `INSTRUCTION.md`。
- `INSTRUCTION.md` 无法指导自动执行。
- 执行过程需要人工交互。
- 无法判断是否执行完成。
- 找不到 `flashDB_rust` 或 `Cargo.toml`。
- Rust 项目无法构建。
- 测试缺失或与原始 C 测试语义不一致。
- 修改平台提供的原始测试材料。
- 只提交编译产物，不提供源码或执行流程。

### 2.3 设计原则

1. **不硬编码 FlashDB 业务逻辑**  
   具体 API 名称、容量、错误返回值、输出项目名应来自源码 README/READNE、任务要求和 C 源码分析。

2. **不把 cargo test 通过等同于语义等价**  
   `cargo test` 是必要条件，不是充分条件。

3. **测试不足必须阻断 READY**  
   如果关键路径没有迁移或派生覆盖，应输出 `BLOCKED_WITH_REPORT`，而不是 `READY_FOR_EVALUATION`。

4. **verify 不通过必须回到分析与实现**  
   编程 harness 应具备“失败 → 定位 → 修复 → 重试”的闭环。

5. **报告必须反映真实门禁状态**  
   `result/output.md`、`result/issues/00-summary.md`、`06-verification-report.md`、`repair-rounds.json` 必须一致。

---

## 3. 问题分类

### P0：语义门禁误报 READY

#### 现象

当前生成项目存在语义缺陷，但 `result/output.md` 报告：

```text
READY_FOR_EVALUATION
semantic_gate: True
```

第三方验收结论为不通过。

#### 根因

当前 semantic gate 主要验证：

- API 被测试调用。
- 测试中存在断言。
- `cargo test` 通过。
- API mapping 没有 unsupported。

但这些不能证明：

- 状态初始化语义正确。
- 容量边界正确。
- not-found 路径正确。
- 删除边界正确。
- 失败操作后状态保持正确。

#### 风险

这是最高风险问题，会导致：

- 三方验收不通过。
- 自动评测认为测试语义不一致。
- 作品报告可信度下降。

---

### P1：缺少源码语义不变量提取

#### 现象

当前分析侧能识别函数定义、API mapping、部分控制流模式，但没有形成可用于验证的语义不变量。

#### 根因

分析产物仍偏“结构映射”，缺少以下抽象：

- 初始化/重置行为。
- 逻辑计数与底层存储一致性。
- 固定容量上限。
- 已存在 key 的更新行为。
- not-found 返回值。
- 删除后的元素移动/顺序保持。
- 失败操作后状态保持。

#### 风险

生成器不知道哪些行为必须被测试，也不知道哪些实现模式存在不一致风险。

---

### P2：测试生成只覆盖显性源测试，缺少 adversarial self-check

#### 现象

当前 Rust 测试覆盖空库、新增、查询、覆盖、删除和计数，但缺少：

- 已有数据后重复初始化。
- 容量上限。
- 满容量失败。
- 查询不存在键。
- 删除不存在键。
- 删除首部、中部、尾部记录。

#### 根因

测试生成策略偏向“源测试镜像”，没有基于 C 源码行为推导边界测试和状态测试。

#### 风险

表面 `cargo test` 通过，但真实边界场景失败。

---

### P3：实现生成缺少状态一致性检查

#### 现象

C 中 `records[count] = ...; count++` 与 Rust 中 `Vec::push(...); count += 1` 在“重置 count 但不清空 Vec”的场景下语义不等价。

#### 根因

生成器将 C 的 fixed array + count 映射成 Rust `Vec` 后，没有维护逻辑索引与物理存储的一致性。

#### 风险

该类问题不仅出现在 FlashDB，也会出现在所有 `array + count` 风格 C 数据结构迁移中。

---

### P4：缺少 verify-repair loop

#### 现象

验证失败或外部发现缺陷后，只能人工分析修复。

#### 根因

当前 runner 的链路是：

```text
analyze -> generate -> verify -> report
```

而不是：

```text
analyze -> generate -> verify -> repair -> verify -> report
```

#### 风险

一旦生成实现存在小缺陷，harness 没有自动回修能力，无法体现优秀编程 agent/harness 的闭环能力。

---

### P5：报告一致性不足

#### 现象

外部验收不通过，但 `result/output.md`、`result/issues/00-summary.md` 和 `06-verification-report.md` 标记通过。

#### 根因

报告依赖浅层 gate 的布尔结果，没有把测试充分性、语义不变量覆盖率、repair 失败状态纳入 READY 判定。

#### 风险

评审看到 READY，但人工/三方复核发现不通过，报告可信度受损。

---

## 4. 总体设计方案

### 4.1 新增语义闭环架构

目标链路：

```text
SourceRoot
  -> Requirement Parse
  -> C Source Inventory
  -> API / Struct / Test Mapping
  -> Semantic Invariant Extraction
  -> Rust Implementation Generation
  -> Source Test Migration
  -> Invariant Test Generation
  -> cargo build
  -> cargo test
  -> Semantic Audit Gate
  -> Repair Loop if failed
  -> Final Report
```

### 4.2 新增产物

新增或增强以下 trace 文件：

```text
logs/trace/c-to-rust/semantic-invariants.json
logs/trace/c-to-rust/semantic-test-plan.json
logs/trace/c-to-rust/semantic-audit-report.md
logs/trace/c-to-rust/repair-rounds.json
logs/trace/c-to-rust/repair-round-01.md
logs/trace/c-to-rust/repair-round-02.md
logs/trace/c-to-rust/repair-round-03.md
```

生成 Rust 测试新增：

```text
<output_project>/tests/source_migration.rs
<output_project>/tests/semantic_invariants.rs
```

---

## 5. 分问题解决方案

## 5.1 解决 P0：semantic gate 误报 READY

### 方案

重定义 `semantic_gate`：

只有同时满足以下条件才能为 True：

1. API mapping 完整或未覆盖项有明确 blocking reason。
2. 原始 C 测试已迁移或等价覆盖。
3. 语义不变量已提取并生成测试计划。
4. 派生语义测试已生成。
5. `cargo test` 执行了 source migration tests 和 invariant tests。
6. 所有 invariant tests 通过。
7. repair loop 没有未解决失败。
8. 报告中没有 unresolved semantic warnings。

否则：

```text
status=BLOCKED_WITH_REPORT
semantic_gate=False
first_blocking_point=F_CARGO_TEST_OR_SEMANTIC
```

### 修改点

- `work/runtime/loopforge_runner.py`
- `work/runtime/c2rust_repair.py`
- `work/runtime/c2rust_project_generator.py`
- 可新增 `work/runtime/c2rust_semantic_audit.py`

### 验收标准

- 人为注入重复初始化缺陷时，`semantic_gate` 必须失败。
- 未生成 invariant tests 时，`semantic_gate` 必须失败。
- 仅 `cargo test` 通过但 invariant coverage 不足时，不允许 READY。
- `result/output.md` 与 `06-verification-report.md` 的 semantic 结果一致。

---

## 5.2 解决 P1：缺少语义不变量提取

### 方案

新增 `SemanticInvariantExtractor`，从 C 源码、头文件、源测试中抽取可测试行为。

### 需要识别的不变量类型

#### A. 初始化/重置不变量

识别模式：

```c
count = 0;
memset(...);
field = default;
```

输出语义：

```json
{
  "kind": "state_reset",
  "api": "<init_api>",
  "reset_fields": ["count"],
  "requires_logical_storage_reset": true
}
```

说明：如果 C 的 fixed array 不清空但 `count=0` 后下一次写入 `records[0]`，Rust 的 Vec 迁移必须保证逻辑视图一致：要么清空 Vec，要么用索引覆盖而不是 push 到末尾。

#### B. 容量边界不变量

识别模式：

```c
#define MAX_RECORDS 16
if (count >= MAX_RECORDS) return -1;
```

输出语义：

```json
{
  "kind": "capacity_limit",
  "capacity": 16,
  "overflow_return": -1,
  "state_preserved_on_overflow": true
}
```

#### C. 查询 not-found 不变量

识别模式：

```c
return NULL;
return 0;
return -1;
```

输出语义：

```json
{
  "kind": "lookup_not_found",
  "api": "<lookup_api>",
  "return_value": "None"
}
```

#### D. 更新/新增不变量

识别模式：

```c
if (strcmp(existing.key, key) == 0) { update; return 0; }
records[count] = ...;
count++;
```

输出语义：

```json
{
  "kind": "insert_or_update",
  "update_existing": true,
  "append_new": true,
  "duplicate_increments_count": false
}
```

#### E. 删除不变量

识别模式：

```c
for (j = i; j < count - 1; j++) records[j] = records[j + 1];
count--;
return 0;
```

输出语义：

```json
{
  "kind": "delete_shift",
  "delete_existing_return": 0,
  "delete_missing_return": -1,
  "remaining_items_queryable": true
}
```

### 修改点

- `work/runtime/c2rust_analysis.py`
- 新增 `work/runtime/c2rust_semantic_audit.py` 或 `work/runtime/c2rust_invariants.py`

### 输出文件

```text
logs/trace/c-to-rust/semantic-invariants.json
```

### 验收标准

当前 FlashDB 样例至少提取：

- `state_reset`
- `capacity_limit(capacity=16)`
- `insert_or_update`
- `lookup_not_found`
- `delete_shift`
- `delete_missing`
- `state_preserved_on_error`

注意：这些类型是通用抽象，API 名称和容量值必须来自源码分析。

---

## 5.3 解决 P2：测试生成不足

### 方案

新增 invariant-derived adversarial tests。

生成策略：

```text
源测试迁移 + 语义不变量派生测试
```

### 必须生成的测试类型

#### A. reset-after-mutation

适用条件：存在 `state_reset` + `insert_or_update` + `lookup`。

测试行为：

1. 插入旧数据。
2. 调用 reset/init API。
3. 插入新数据。
4. 查询新数据成功。
5. 查询旧数据失败或不可见。

#### B. capacity-boundary

适用条件：存在 `capacity_limit`。

测试行为：

1. 插入 capacity 条数据。
2. 全部可查询。
3. 第 capacity+1 条返回 overflow error。
4. 失败后已有数据仍可查询。
5. count 不超过 capacity。

#### C. lookup-not-found

适用条件：存在 lookup not-found return。

测试行为：

1. 空库查询不存在 key。
2. 插入其他 key 后查询不存在 key。
3. 返回值符合 C 语义映射。

#### D. delete-not-found

适用条件：存在 delete missing return。

测试行为：

1. 删除不存在 key。
2. 返回错误码。
3. 原有数据不变。

#### E. delete-head-middle-tail

适用条件：存在 delete shift。

测试行为：

1. 插入多条记录。
2. 删除首部，剩余可查。
3. 删除中部，剩余可查。
4. 删除尾部，剩余可查。
5. count 正确。

#### F. update-existing

适用条件：存在 update existing。

测试行为：

1. 插入 key=value1。
2. 再插入同 key=value2。
3. 查询返回 value2。
4. count 不增加。

### 修改点

- `work/runtime/c2rust_project_generator.py`
- 可新增 `work/runtime/c2rust_invariant_tests.py`

### 输出文件

```text
<output_project>/tests/semantic_invariants.rs
logs/trace/c-to-rust/semantic-test-plan.json
```

### 验收标准

当前样例生成的 Rust 测试中必须包含以下测试函数或等价函数：

- `test_reset_after_mutation`
- `test_capacity_boundary`
- `test_lookup_not_found`
- `test_delete_not_found_preserves_state`
- `test_delete_head_middle_tail`
- `test_update_existing_does_not_increment_count`

函数名不必完全一致，但 `semantic-test-plan.json` 必须标记这些场景为 covered。

---

## 5.4 解决 P3：实现生成缺少状态一致性

### 方案

增强 C fixed array + count 到 Rust Vec 的映射规则。

### 规则 1：reset count 需要同步逻辑存储

如果 C 中：

```c
db->count = 0;
```

且后续新增逻辑是：

```c
records[count] = item;
count++;
```

Rust 不能只做：

```rust
db.count = 0;
```

应该生成等价逻辑之一：

方案 A：重置时清空 Vec。

```rust
db.records.clear();
db.count = 0;
```

方案 B：新增时按逻辑索引覆盖。

```rust
if db.count < db.records.len() {
    db.records[db.count] = new_item;
} else {
    db.records.push(new_item);
}
db.count += 1;
```

优先建议方案 A，简单且符合“逻辑空库”语义。

### 规则 2：count 是逻辑长度，Vec len 不能作为唯一真相

如果生成结构同时保留 `count` 和 `Vec`，必须维护：

```text
0 <= count <= records.len() <= capacity
```

或者简化为：

```text
count == records.len()
```

若选择后者，应避免双状态源不一致。

### 规则 3：失败操作必须状态保持

如果 C 源码中满容量或 not-found 返回错误，Rust 实现不得修改 records/count。

### 修改点

- `work/runtime/c2rust_project_generator.py`
- 可在 `work/runtime/c2rust_semantic_audit.py` 中增加实现静态检查。

### 验收标准

- `flashdb_new` 等价 reset 场景通过。
- 满容量失败后 count 不变。
- 删除不存在 key 后 count 不变。
- 更新已有 key 后 count 不增加。

---

## 5.5 解决 P4：缺少 verify-repair loop

### 方案

在 runner 中引入 repair loop：

```text
max_repair_rounds = 3
```

每轮流程：

```text
1. generate implementation and tests
2. cargo build
3. cargo test
4. semantic audit
5. if failed: classify failure
6. repair implementation or tests
7. rerun from cargo build
```

### repair 输入

repair 模块需要读取：

- failing cargo test output。
- failing semantic invariant name。
- semantic-invariants.json。
- source inventory。
- generated Rust implementation。

### repair 输出

```text
logs/trace/c-to-rust/repair-rounds.json
logs/trace/c-to-rust/repair-round-01.md
logs/trace/c-to-rust/repair-round-02.md
logs/trace/c-to-rust/repair-round-03.md
```

示例：

```json
{
  "max_rounds": 3,
  "rounds": [
    {
      "round": 1,
      "failure_kind": "semantic_invariant_failed",
      "failed_test": "test_reset_after_mutation",
      "repair_action": "add storage clear on reset operation",
      "result": "passed_after_repair"
    }
  ],
  "unresolved_failures": []
}
```

### 修改点

- `work/runtime/loopforge_runner.py`
- `work/runtime/c2rust_repair.py`
- `work/runtime/c2rust_project_generator.py`

### 验收标准

- 若首次生成存在 reset/Vec 缺陷，`semantic_invariants.rs` 应失败。
- repair loop 应修复实现并重新执行 `cargo test`。
- 修复后 `repair-rounds.json` 记录修复动作。
- 如果三轮仍失败，输出 `BLOCKED_WITH_REPORT`，不允许 READY。

---

## 5.6 解决 P5：报告一致性不足

### 方案

统一 READY 判定源，禁止各报告单独计算状态。

新增统一结果对象：

```json
{
  "status": "READY_FOR_EVALUATION | BLOCKED_WITH_REPORT",
  "gates": {
    "cargo_build": true,
    "cargo_test": true,
    "unsafe": true,
    "api_mapping": true,
    "source_test_mapping": true,
    "semantic_invariant_extraction": true,
    "semantic_invariant_tests": true,
    "repair_loop": true,
    "semantic_gate": true
  },
  "first_blocking_point": null,
  "unresolved_failures": []
}
```

所有报告从该对象渲染：

- `result/output.md`
- `result/issues/00-summary.md`
- `logs/trace/c-to-rust/06-verification-report.md`
- `logs/trace/run-summary.json`

### READY 条件

只有全部 gate 通过，才输出：

```text
READY_FOR_EVALUATION
```

否则输出：

```text
BLOCKED_WITH_REPORT
```

并明确：

```text
first_blocking_point: F_CARGO_TEST_OR_SEMANTIC
```

### 验收标准

- 任一 invariant test 失败时，所有报告均为 BLOCKED。
- 任一 report 不允许单独显示 semantic passed。
- `result/issues/00-summary.md` 必须说明首个阻断点和失败测试。

---

## 6. Skill 强化设计

### 6.1 修改范围

建议修改：

```text
work/skills/c-to-rust-migration/SKILL.md
```

如果当前 skill 名称不同，修改实际 C-to-Rust migration skill。

### 6.2 新增约束内容

Skill 中新增以下行为约束：

```markdown
## Semantic Self-Audit Requirement

Do not claim semantic equivalence only because the generated Rust project builds and existing tests pass.

After implementation, derive semantic invariants from the C source code and source tests. At minimum, check for:

- initialization/reset behavior
- collection capacity behavior
- lookup not-found behavior
- mutation update/insert behavior
- delete behavior and state preservation
- error paths and state preservation after failed operations

Generated Rust tests must cover:

- normal paths
- boundary paths
- error paths
- state reset after mutation
- state preservation after failed operations
- deletion at head/middle/tail for ordered collections when applicable

If any semantic invariant test fails, repair the generated implementation and rerun verification.

Do not report READY_FOR_EVALUATION until:

- cargo build passes
- cargo test passes
- unsafe gate passes
- source tests are migrated or equivalently covered
- semantic invariant tests are generated and pass
- repair loop has no unresolved semantic failures
```

### 6.3 Skill 验收标准

- Skill 中不能硬编码 FlashDB API 名称。
- Skill 中可以写通用不变量类型。
- Skill 必须明确“测试不足不得 READY”。
- Skill 必须明确“verify 失败进入 repair loop”。

---

## 7. 文件级实施清单

### 7.1 必改文件

| 文件 | 修改目的 |
|---|---|
| `work/runtime/c2rust_analysis.py` | 提取 semantic invariants，增强源码行为建模 |
| `work/runtime/c2rust_project_generator.py` | 生成 invariant tests，修正 array+count 到 Vec 的状态一致性规则 |
| `work/runtime/c2rust_repair.py` | 支持 semantic test failure repair |
| `work/runtime/loopforge_runner.py` | 接入 semantic audit gate 和 repair loop |
| `work/skills/c-to-rust-migration/SKILL.md` | 强化实现后语义自查和失败回修要求 |

### 7.2 建议新增文件

| 文件 | 作用 |
|---|---|
| `work/runtime/c2rust_semantic_audit.py` | 语义不变量建模、gate 计算、audit report 生成 |
| `work/runtime/c2rust_invariant_tests.py` | 根据 invariants 生成 Rust adversarial tests |

### 7.3 不建议本轮修改

| 文件/目录 | 原因 |
|---|---|
| `INSTRUCTION.md` | 当前问题不是入口说明 |
| `work/scripts/run.ps1` | 当前问题不是 Windows 调用链 |
| `work/scripts/run.sh` | 当前问题不是 Linux 启动链 |
| `flashDB_rust/*` | 不应手工修生成结果，应修 harness |
| `result/*` | 应由无人托管执行重新生成 |
| `logs/*` | 应由新一轮 E2E 重新生成 |

---

## 8. 实施阶段划分

### Phase 1：不变量提取与测试生成

目标：能从源码分析出 semantic invariants，并生成 `semantic_invariants.rs`。

验收：

- `semantic-invariants.json` 存在。
- `semantic-test-plan.json` 存在。
- `tests/semantic_invariants.rs` 存在。
- 重复初始化测试存在。
- 容量边界测试存在。
- not-found 和 delete 边界测试存在。

### Phase 2：实现生成状态一致性修复

目标：修复 array+count 到 Vec 的通用状态一致性问题。

验收：

- reset 后旧记录不可见。
- 新记录可查。
- count 与 records 逻辑一致。
- 更新已有 key 不增加 count。
- 失败操作不破坏状态。

### Phase 3：semantic gate 严格化

目标：READY 判定不再依赖浅层测试。

验收：

- 删除 `semantic_invariants.rs` 时，semantic gate 失败。
- invariant test 失败时，semantic gate 失败。
- 只有所有 gate 通过才 READY。

### Phase 4：repair loop 接入

目标：测试失败后自动回修并复测。

验收：

- 人为注入 reset/Vec 缺陷后，第一次 test 失败。
- repair loop 生成 repair round 记录。
- 修复后 cargo test 通过。
- 若无法修复，输出 BLOCKED。

### Phase 5：无人托管 E2E 验收

目标：模拟评测 agent 只读 `INSTRUCTION.md` 执行。

验收：

- 无人工介入。
- 最终生成 Rust 项目。
- `cargo build` / `cargo test` 通过。
- semantic invariant tests 通过。
- `result/output.md` 为 READY。
- 第三方报告中的 P0 场景被自动测试覆盖。

---

## 9. 最终验收标准

### 9.1 文件产物验收

执行完成后必须存在：

```text
result/output.md
result/issues/00-summary.md
logs/interaction.md
logs/trace/c-to-rust/01-source-inventory.json
logs/trace/c-to-rust/02-api-mapping.json
logs/trace/c-to-rust/04-test-mapping.json
logs/trace/c-to-rust/semantic-invariants.json
logs/trace/c-to-rust/semantic-test-plan.json
logs/trace/c-to-rust/semantic-audit-report.md
logs/trace/c-to-rust/06-verification-report.md
logs/trace/c-to-rust/repair-rounds.json
```

Rust 项目必须存在：

```text
<output_project>/Cargo.toml
<output_project>/src/
<output_project>/tests/source_migration.rs
<output_project>/tests/semantic_invariants.rs
```

### 9.2 行为验收

必须通过：

```bash
cargo build --locked
cargo test --locked -- --nocapture
```

必须覆盖：

- reset after mutation。
- capacity boundary。
- overflow failure state preservation。
- lookup not found。
- delete not found state preservation。
- delete head/middle/tail。
- update existing without count increment。

### 9.3 报告验收

READY 条件：

```text
cargo_build: passed
cargo_test: passed
unsafe_gate: passed
source_test_mapping: passed
semantic_invariant_tests: passed
semantic_gate: passed
repair_loop: passed
status: READY_FOR_EVALUATION
```

BLOCKED 条件：

任一关键 gate 失败时：

```text
status: BLOCKED_WITH_REPORT
first_blocking_point: <A-G category>
```

如果是语义测试失败：

```text
first_blocking_point: F_CARGO_TEST_OR_SEMANTIC
```

### 9.4 反向验收

必须能抓住当前三方报告中的 P0：

```rust
let mut db = FlashdbHandle::default();
flashdb_set(&mut db, "old", "value");
flashdb_new(&mut db);
flashdb_set(&mut db, "new", "value");
assert_eq!(flashdb_get(&db, "new"), Some("value".to_string()));
```

验收方式：

- 若实现有缺陷，该测试必须失败。
- 若 repair loop 生效，最终实现应通过该测试。
- 若无法修复，最终状态必须是 BLOCKED，不允许 READY。

---

## 10. 风险与边界

### 10.1 不追求完整形式化验证

本设计不是要实现完整 C/Rust 形式化等价证明，而是提升到工程可接受的 semantic self-audit 水平。

### 10.2 不硬编码当前题目业务 API

可以针对通用 C 模式建模：

- fixed array + count。
- strcmp lookup。
- insert/update/delete。
- error return。
- reset/init。

不能在框架中写死：

- `flashdb_new`
- `flashdb_set`
- `flashdb_get`
- `flashdb_delete`
- `flashdb_count`

API 名称只能来自源码分析结果。

### 10.3 避免测试与实现互相造假

生成测试必须来自：

- C 源码行为。
- C 测试行为。
- README/READNE 要求。
- 通用语义不变量模式。

不能为了让测试通过而删除或弱化测试。

### 10.4 repair loop 必须可追踪

每次回修必须写入 trace，不能静默修改。

---

## 11. 建议提交策略

### Commit 1：Semantic invariant extraction

```text
Add semantic invariant extraction for C-to-Rust migration
```

包含：

- `c2rust_analysis.py`
- `c2rust_semantic_audit.py`
- trace 输出。

### Commit 2：Invariant test generation

```text
Generate invariant-derived semantic tests
```

包含：

- `c2rust_project_generator.py`
- `c2rust_invariant_tests.py`
- `semantic_invariants.rs` 生成。

### Commit 3：Strict semantic gate

```text
Tighten semantic gate to prevent READY false positives
```

包含：

- `loopforge_runner.py`
- report 统一 READY 判定。

### Commit 4：Verify repair loop

```text
Add verify-repair loop for semantic failures
```

包含：

- `c2rust_repair.py`
- repair trace。

### Commit 5：Skill reinforcement

```text
Document semantic self-audit requirements in C-to-Rust skill
```

包含：

- `work/skills/.../SKILL.md`

---

## 12. 审核结论

当前问题不是单个 Rust 实现 bug，而是 harness 的语义验证能力不足。优化后，项目应从：

```text
流程型 runner + generator + shallow verifier
```

升级为：

```text
语义不变量提取 + 派生测试 + 严格 gate + verify-repair loop 的 C-to-Rust semantic harness
```

只有完成该升级后，才能减少“本地 READY、三方验收不通过”的风险。
