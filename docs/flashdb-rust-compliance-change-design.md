# FlashDB Rust 重写完整合规优化设计

## 1. 文档目的

本文档用于指导后续 OpenSpec change 的拆分、实现和验收。目标不是证明当前项目已经满足 `work/design/README.md`，而是定义达到完整验收所需的改造范围、证明义务和不可降级的验收标准。

当前基线存在以下实质缺口：

- 当前最终状态为 `BLOCKED_WITH_REPORT`。
- 现有迁移证据主要来自简单 `demo` fixture，而不是真实 FlashDB 完整迁移。
- API 映射和测试映射不能证明真实 FlashDB 覆盖完整。
- 现有生成测试包含恒真或自比较断言，不能证明语义等价。
- 语义审计缺少正向等价声明、语义不变量及对应测试。
- 正式 Linux 环境尚缺少从空输出目录开始的完整成功证据。

因此，后续工作必须以真实 FlashDB 为验收对象，并通过独立、可重复、不可真空通过的证据链判定完成。

## 2. 总体完成定义

只有以下条件全部成立，系统才可以输出 `READY_FOR_EVALUATION`：

```text
READY =
    source_complete
 && api_complete
 && module_relation_complete
 && rust_implementation_complete
 && source_tests_migrated
 && differential_tests_passed
 && cargo_build_passed
 && cargo_test_passed
 && repair_fault_injection_passed
 && unsafe_ratio < 0.10
 && source_tree_unchanged
 && clean_linux_e2e_passed
```

任何空集合、缺失证据、未支持核心函数、未执行测试或报告间状态不一致，都必须得到 `BLOCKED_WITH_REPORT`。

## 3. Change 拆分与依赖

```text
Change 1：真实源码分析能力
        ↓
Change 2：语义模型与迁移规划
        ↓
Change 3：完整 Rust 工程生成
        ↓
Change 4：测试迁移与差分验证
        ↓
Change 5：编译和语义自愈闭环
        ↓
Change 6：正式 Linux E2E 验收
```

`preload-design-readme` 作为输入契约前置能力保留，但不替代以上六个核心 change。

## 4. Change 1：真实 FlashDB 源码分析能力

### 4.1 目标

从真实 FlashDB 工程提取完整的跨文件结构、API、类型、状态和测试信息，禁止依赖简单正则模式产生不完整但表面成功的分析结果。

### 4.2 范围

- 解析 C 头文件、实现文件、宏、条件编译、`typedef`、结构体、枚举和函数指针。
- 建立声明与定义关系、include 图、调用图、类型依赖图和共享状态图。
- 覆盖真实项目的 `src`、`inc` 和 `tests`，并支持实际等价布局。
- 对无法解析的核心函数和类型给出明确阻塞原因。
- 增加独立源码扫描器，与主分析器的结果交叉验证。

### 4.3 必须生成的证据

```text
source-inventory.json
independent-source-scan.json
public-api-map.json
type-map.json
call-graph.json
global-state-map.json
preprocessor-variants.json
analysis-verification.json
```

### 4.4 验收标准

- 核心源文件覆盖率为 100%。
- 公开 API 声明、定义和证据位置覆盖率为 100%。
- 所有核心结构体字段、枚举成员和函数指针均被建模。
- 不存在未解释的悬空符号。
- 主分析结果与独立扫描结果集合一致。
- `source_file_count`、`public_api_count`、`source_test_count` 任一为零时不得通过。
- 任一核心函数或类型解析失败时不得进入代码生成。

## 5. Change 2：FlashDB 语义模型与迁移规划

### 5.1 目标

将源码结构转换为可验证的行为契约和状态模型，使 Rust 迁移以业务语义为依据，而不是逐行或少量函数体模式翻译。

### 5.2 范围

- 建模 KVDB、TSDB、分区、扇区、遍历、删除、GC 和恢复行为。
- 建模初始化、读写、更新、删除、重新打开等状态转换。
- 定义 C 数据布局到 Rust 类型、所有权和生命周期的映射。
- 定义存储 I/O、Flash 操作和并发锁的抽象边界。
- 为每个公开 API 描述输入、输出、错误码、副作用和失败保持行为。

### 5.3 行为契约最低结构

```json
{
  "api": "fdb_kv_set",
  "inputs": [],
  "preconditions": [],
  "return_codes": [],
  "state_mutations": [],
  "persistence_effects": [],
  "failure_behavior": [],
  "source_evidence": []
}
```

### 5.4 验收标准

- 公开 API 行为契约覆盖率为 100%。
- 所有状态修改 API 均有前置状态、成功后置状态和失败后置状态。
- 所有原始错误码都有明确的 Rust 对应行为。
- 每项核心能力均包含正常、边界、失败和持久化重开路径。
- `semantic_invariant_count > 0`。
- 空语义不变量、空状态转换或无证据契约不得通过。

## 6. Change 3：完整 Rust 工程生成器

### 6.1 目标

生成真实可用的 `flashDB_rust` Cargo 工程，完整映射核心逻辑，并支持受控的单点渐进式重新生成。

### 6.2 范围

- 按真实模块关系生成 Rust 模块。
- 实现 KVDB、TSDB、公共 API 和存储后端抽象。
- 使用安全 Rust 的所有权、借用和生命周期表达存储状态。
- 对不可迁移函数立即阻塞，禁止使用占位实现代替。
- 建立 C 函数、模块、调用边到 Rust 实现的映射。
- 支持只重新生成目标模块及其直接依赖范围。

### 6.3 必须生成的证据

```text
implementation-map.json
unsupported-functions.json
module-edge-map.json
incremental-regeneration-report.json
```

### 6.4 验收标准

- 核心函数实现映射率为 100%。
- 公开 API 映射率为 100%。
- `unsupported-functions.json` 为空。
- 不得出现 `todo!()`、`unimplemented!()`、恒定返回值伪实现或用空函数替代有状态逻辑。
- `cargo build --locked` 返回 0。
- `unsafe` 比例低于 10%，并对每一处 `unsafe` 提供必要性说明。
- 单点重新生成时，无依赖模块的文件哈希保持不变。

## 7. Change 4：原始测试迁移与 C/Rust 差分验证

### 7.1 目标

将原始测试场景迁移为有效 Rust 测试，并使用 C 原实现作为行为 Oracle，对同一输入进行差分验证。

### 7.2 差分验证模型

```text
               同一输入与初始存储状态
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
      C FlashDB 原实现          Rust 重写实现
             │                       │
             └───────────┬───────────┘
                         ▼
       比较返回值、状态、错误、顺序和持久化结果
```

### 7.3 比较范围

- 返回值和错误码。
- KV 写入、读取、更新和删除结果。
- TSDB 追加、查询和遍历顺序。
- 容量和边界行为。
- 关闭并重新打开后的持久化状态。
- 中断、损坏或失败后的恢复行为。
- GC 前后的可见数据和状态。

### 7.4 必须生成的证据

```text
source-test-map.json
differential-test-vectors.json
differential-test-report.json
semantic-invariant-test-map.json
mutation-test-report.json
cargo-test.log
```

### 7.5 验收标准

- 原始 C 测试场景迁移或等价覆盖率为 100%。
- 每个源断言都对应至少一个有效 Rust 断言。
- 每个语义不变量至少由一个实际执行的测试覆盖。
- 所有确定性差分测试结果一致。
- 固定随机种子的状态机测试结果一致。
- mutation testing 注入关键语义错误后，测试必须失败。
- 禁止恒真、自比较和全匹配断言，例如：

```rust
assert!(true);
assert_eq!(x, x);
assert!(matches!(x, _));
```

- `cargo test --locked -- --nocapture` 返回 0，且报告记录实际执行的测试数量和名称。

## 8. Change 5：编译与语义自愈闭环

### 8.1 目标

根据 Rust 编译器、测试和差分验证错误生成最小修复，并证明修复没有删除测试、弱化断言或绕过门禁。

### 8.2 固定故障注入集

| 注入缺陷 | 预期检测 | 合法修复方向 |
|---|---|---|
| 错误 Rust 类型 | 编译失败 | 局部类型修复 |
| 借用冲突 | borrow checker 失败 | 修复所有权或借用关系 |
| API 名称错误 | unresolved symbol | 修复关联调用点 |
| 错误返回码 | 差分失败 | 修复业务逻辑 |
| 删除行为错误 | 语义测试失败 | 修复状态转换 |
| 容量边界 off-by-one | 边界测试失败 | 修复边界判断 |

### 8.3 每轮必须生成的证据

```text
injected-defect.patch
compiler-or-test-error.log
repair-task.json
generated-repair.patch
changed-lines.json
targeted-test.log
full-regression.log
```

### 8.4 验收标准

- 固定故障类型全部能够被检测。
- 每种故障至少重复验证三次。
- 修复只能修改生成的 Rust 工程。
- 补丁范围必须与错误位置或直接依赖范围相关。
- 修复后目标测试和完整回归测试均通过。
- 测试数量不得减少，断言不得被删除或弱化。
- 修复不得增加未经说明的 `unsafe`。
- 达到最大修复轮次后必须输出阻塞报告。

## 9. Change 6：正式 Linux E2E 与提交验收

### 9.1 目标

在干净 Linux 环境中，从空输出目录和只读真实 FlashDB 输入开始，证明整个提交包能够无人值守完成迁移与验证。

### 9.2 验收场景

- `SOURCE_ROOT` 直接指向 FlashDB 项目。
- `SOURCE_ROOT` 指向包含 FlashDB 的上层目录。
- 源项目不存在 README。
- 输出、结果和日志目录初始为空。
- 连续执行两次，结果保持一致。

### 9.3 必须生成的证据

```text
linux-environment.json
source-before.sha256
source-after.sha256
cargo-build.log
cargo-test.log
unsafe-ratio.json
final-verification.json
result/output.md
result/issues/00-summary.md
```

### 9.4 验收标准

- 从空输出目录生成完整 `work/output/flashDB_rust`。
- 不使用仓库中预生成或陈旧的 Rust 文件。
- `cargo build --locked` 和 `cargo test --locked -- --nocapture` 均返回 0。
- 源文件集合、内容哈希和权限在运行前后保持不变。
- 两种 `SOURCE_ROOT` 布局均能定位唯一项目根目录。
- 所有报告路径真实存在且状态一致。
- 连续两次完整运行均得到 `READY_FOR_EVALUATION`。

## 10. 题目要求追踪矩阵

| 题目要求 | 对应 Change | 核心证明 | 硬性标准 |
|---|---|---|---|
| 跨文件深度关联 | 1、2 | 源清单、调用图、类型图 | 核心文件和公开 API 100% 覆盖 |
| 保持模块调用关系 | 2、3 | 模块及调用边映射 | 核心调用边全部保留或有等价设计证据 |
| 单点渐进式重构 | 3 | 增量生成哈希报告 | 无依赖模块内容不变 |
| 编译自愈 | 5 | 故障注入和修复补丁 | 固定缺陷全部正确修复 |
| 语义等价 | 2、4 | 行为契约和差分测试 | 全部差分场景一致 |
| 主要路径单元测试 | 4 | 测试映射和 mutation testing | 源测试 100% 映射且能识别错误 |
| 核心逻辑完整迁移 | 1 至 4 | 实现映射 | 核心函数 100%，不支持项为 0 |
| Cargo 构建和测试 | 3、4、6 | 原始命令日志 | 两条命令退出码为 0 |
| `unsafe` 低于 10% | 3、6 | 逐文件统计 | 比例严格小于 0.10 |
| `SOURCE_ROOT` 只读 | 6 | 前后哈希和权限记录 | 输入完全不变 |
| 无人值守 Linux | 6 | 干净环境 E2E | 连续两次成功 |

## 11. 防止伪通过的统一门禁

以下条件必须由最终验证器强制执行：

```text
source_file_count > 0
public_api_count > 0
source_test_count > 0
mapped_api_count == public_api_count
unsupported_api_count == 0
mapped_source_test_count == source_test_count
semantic_invariant_count > 0
differential_scenario_count > 0
executed_rust_test_count > 0
```

此外必须检查：

- 不允许将缺失项从分母中排除后声称 100% 覆盖。
- 不允许用生成成功代替语义成功。
- 不允许用 Cargo 命令退出码代替测试有效性证明。
- 不允许删除失败测试或降低断言强度实现自愈。
- 不允许报告引用陈旧运行产物。
- 根目录与 `work/` 下若存在重复报告，状态和路径必须一致，否则阻塞。

## 12. 最终证据包

最终运行至少应生成：

```text
logs/trace/
├── source-inventory.json
├── independent-source-scan.json
├── public-api-map.json
├── call-graph.json
├── behavior-contracts.json
├── implementation-map.json
├── unsupported-functions.json
├── source-test-map.json
├── differential-test-report.json
├── mutation-test-report.json
├── repair-fault-injection-report.json
├── cargo-build.log
├── cargo-test.log
├── unsafe-ratio.json
├── source-before.sha256
├── source-after.sha256
└── final-verification.json
```

## 13. 证明边界

上述证据能够形成强工程意义上的语义等价证明：源码和 API 完整盘点、行为契约、原测试迁移、C/Rust 差分测试、随机状态机测试、mutation testing 和端到端复验共同降低遗漏风险。

它不等同于数学意义上的形式化证明。如果比赛要求形式化等价，需要额外引入模型检查、定理证明或经验证编译链；当前 `work/design/README.md` 的验收措辞更符合可重复的工程验证。

## 14. 后续使用方式

后续每个 OpenSpec change 应从本文对应章节提取：

1. 范围与非目标；
2. 机器可验证的需求；
3. 实现任务；
4. 独立验证任务；
5. 必须生成的证据；
6. 阻塞和回退条件。

每个 change 只能在自己的硬性验收标准全部满足后关闭；Change 6 通过之前，不得对外声明项目完整满足比赛要求。
