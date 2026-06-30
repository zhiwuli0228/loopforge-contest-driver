# C-to-Rust Harness：Subagent 化源码分析、独立 Verify 与场景化验收设计文档

> 版本：v1.0  
> 适用项目：LoopForge C-to-Rust 迁移执行框架  
> 目标：把当前“能生成、能编译、能跑测试”的流程型 harness，升级为“能分阶段分析、能独立核验、能发现遗漏、能回修、能防止 READY 误报”的语义级 harness。  
> 设计重点：按场景分类、按 subagent 分工、按 artifact 验证、按 gate 阻断、按验收条件收口。

---

## 1. 背景与问题定义

当前框架已具备基础无人托管能力：

- 能通过 `INSTRUCTION.md` 或脚本入口启动；
- 能读取目标 C 项目源码路径；
- 能生成 Rust 项目；
- 能执行 `cargo build` / `cargo test`；
- 能生成 `result/output.md`、`result/issues/00-summary.md`、`logs/trace/`；
- 能做基础 unsafe 检查、API mapping、test mapping 和 semantic gate。

但三方验收暴露出核心缺陷：

- 当前 `cargo test` 通过不代表语义等价；
- 当前 semantic gate 对“源码能力是否完整识别”没有足够判断；
- 当前分析阶段可能遗漏 C 源码中的结构关系、状态转移和边界路径；
- 当前测试生成更偏 source test mirror，缺少 adversarial / invariant-derived tests；
- 当前 READY 口径过于乐观，存在误报风险；
- 当前流程更接近 runner + generator + shallow verifier，还不是完整 semantic repair harness。

核心风险链路如下：

```text
C 源码结构 / 功能 / 状态模型分析不完整
=> capability map 缺项
=> Rust 实现遗漏能力或状态不变量破坏
=> 现有测试未覆盖该路径
=> cargo test 仍通过
=> semantic_gate 误报 True
=> result/output.md 误报 READY_FOR_EVALUATION
```

因此，下一阶段必须先解决“源码分析可信度”问题，而不是只继续加强 Rust 生成。

---

## 2. 设计目标

### 2.1 总目标

建立一条 **subagent 化、artifact 驱动、逐阶段 verify、失败回退** 的 C-to-Rust harness 执行链。

目标执行模型：

```text
requirement analysis
-> requirement verify
-> source structure analysis
-> source structure verify
-> data model analysis
-> data model verify
-> capability analysis
-> capability verify
-> state model analysis
-> state model verify
-> test coverage analysis
-> test coverage verify
-> source analysis verify gate
-> Rust generation
-> Rust test generation
-> cargo / unsafe / semantic audit
-> repair loop
-> final report
```

### 2.2 关键设计原则

| 原则 | 说明 |
|---|---|
| 分阶段分析 | 不允许一个 agent 一次性完成所有源码理解、转换和验证 |
| 独立验证 | 每个 analyzer 的输出必须由 verifier 独立核验 |
| Artifact 驱动 | 阶段间只传结构化 artifact，不传长上下文 |
| 证据优先 | 每个结论必须带源码文件、符号、行号或模式证据 |
| 缺项阻断 | 分析不完整时阻断，不允许带病生成 Rust |
| 严格 READY | 只有源码分析、能力覆盖、语义测试、cargo、unsafe、repair 全部通过后才能 READY |
| 不污染源码 | 不向 `SOURCE_ROOT` 写框架状态或生成项目 |
| 输出明确 | 生成 Rust 项目统一放到 `work/output/<output_project_name>/`，并在 `result/output.md` 与 `INSTRUCTION.md` 中明确位置 |

---

## 3. 范围与非范围

### 3.1 本阶段范围

本阶段设计和实施关注：

1. 源码分析 subagent 拆分；
2. 源码分析 artifact 设计；
3. analyzer / verifier 双角色流程；
4. Source Analysis Verify Gate；
5. capability / data model / state model / test coverage 完整性门禁；
6. semantic audit 与 repair loop 的接入条件；
7. 场景化验收标准。

### 3.2 本阶段非范围

本阶段不优先处理：

- 新增 Linux E2E 测试脚本；
- 压缩 zip 包体积；
- UI 展示；
- 复杂 C 语法全量支持；
- 手工修复某个具体 Rust bug；
- 改动比赛题面文件；
- 向 `SOURCE_ROOT` 写 `.loopforge` 状态。

---

## 4. 标准目录与交付约束

### 4.1 根目录保留

推荐根目录：

```text
<submission-root>/
├── INSTRUCTION.md
├── INSTRUCTION.linux.md
├── README.md
├── work/
├── result/
└── logs/
```

不建议根目录堆放：

```text
ACCEPTANCE_REPORT.md
c-to-rust-*-design.md
c-to-rust-*-checklist.md
SUBMISSION.md
flashDB_rust/
```

### 4.2 设计文档归档

```text
work/references/design/
├── c-to-rust-generic-harness-design.md
├── c-to-rust-generic-harness-self-checklist.md
├── c-to-rust-semantic-self-audit-harness-design.md
└── c-to-rust-subagent-source-analysis-verify-design.md
```

### 4.3 验收报告归档

```text
logs/trace/acceptance/
├── ACCEPTANCE_REPORT.failed-<date>.md
└── ACCEPTANCE_REPORT.passed-<date>.md
```

### 4.4 生成 Rust 项目输出位置

统一输出到：

```text
work/output/<output_project_name>/
```

当前题面解析出的项目名为 `flashDB_rust` 时：

```text
work/output/flashDB_rust/
├── Cargo.toml
├── src/
└── tests/
```

`INSTRUCTION.md` 和 `result/output.md` 必须明确告诉执行 agent / 评委：

```text
rust_project: work/output/flashDB_rust
cargo_toml: work/output/flashDB_rust/Cargo.toml
```

---

## 5. Subagent 总体分工

### 5.1 Subagent 列表

| 阶段 | Analyzer | Verifier | 主要产物 |
|---|---|---|---|
| 需求读取 | `source-requirement-reader` | `source-requirement-verifier` | `00-requirement-extraction.json` |
| 源码结构 | `source-structure-analyzer` | `source-structure-verifier` | `01a-structure-map.json` |
| 数据模型 | `c-data-model-analyzer` | `c-data-model-verifier` | `01b-data-model-map.json` |
| 能力模型 | `c-capability-analyzer` | `c-capability-verifier` | `01c-capability-map.json` |
| 状态模型 | `c-state-model-analyzer` | `c-state-model-verifier` | `01d-state-transition-map.json` |
| API 行为 | `c-api-behavior-analyzer` | `c-api-behavior-verifier` | `01e-api-behavior-map.json` |
| 测试覆盖 | `c-test-coverage-analyzer` | `c-test-coverage-verifier` | `01f-test-coverage-map.json`、`01g-missing-capability-report.md` |
| Rust 实现 | `rust-implementation-generator` | `semantic-audit-verifier` | Rust 源码、`semantic-audit-report.md` |
| Rust 测试 | `rust-test-generator` | `semantic-audit-verifier` | `source_migration.rs`、`semantic_invariants.rs` |
| 回修 | `repair-loop-agent` | `semantic-audit-verifier` | `repair-rounds.json` |

### 5.2 Subagent 文件建议

```text
work/subagent/
├── source-requirement-reader.md
├── source-requirement-verifier.md
├── source-structure-analyzer.md
├── source-structure-verifier.md
├── c-data-model-analyzer.md
├── c-data-model-verifier.md
├── c-capability-analyzer.md
├── c-capability-verifier.md
├── c-api-behavior-analyzer.md
├── c-api-behavior-verifier.md
├── c-state-model-analyzer.md
├── c-state-model-verifier.md
├── c-test-coverage-analyzer.md
├── c-test-coverage-verifier.md
├── rust-implementation-generator.md
├── rust-test-generator.md
├── semantic-audit-verifier.md
└── repair-loop-agent.md
```

---

## 6. Artifact 设计

所有 artifact 输出到：

```text
logs/trace/c-to-rust/
```

### 6.1 `00-requirement-extraction.json`

用途：提取运行任务要求。

必须包含：

```json
{
  "source_root": "<resolved-source-root>",
  "source_readme": "<SOURCE_ROOT/README or READNE>",
  "task_requirement_readme": "work/code/README.md",
  "source_dirs": ["src"],
  "test_dirs": ["tests"],
  "output_project_name": "flashDB_rust",
  "output_project_dir": "work/output/flashDB_rust",
  "build_commands": ["cargo build", "cargo test"],
  "unsafe_limit": 0.1,
  "evidence": []
}
```

### 6.2 `01a-structure-map.json`

用途：描述 C 项目结构。

必须包含：

```json
{
  "core_files": [],
  "header_files": [],
  "test_files": [],
  "modules": [],
  "public_apis": [],
  "api_declarations": [],
  "api_definitions": [],
  "unresolved_declarations": [],
  "evidence": []
}
```

### 6.3 `01b-data-model-map.json`

用途：描述 C 数据结构、字段语义和 Rust 映射。

必须包含：

```json
{
  "structs": [
    {
      "name": "...",
      "fields": [],
      "field_semantics": [],
      "invariants": [],
      "rust_mapping": {}
    }
  ],
  "macros": [],
  "capacity_constants": [],
  "evidence": []
}
```

### 6.4 `01c-capability-map.json`

用途：从 API、结构和测试抽象能力。

必须包含：

```json
{
  "capabilities": [
    {
      "id": "capability-id",
      "name": "...",
      "apis": [],
      "behaviors": [],
      "normal_paths": [],
      "boundary_paths": [],
      "error_paths": [],
      "state_effects": [],
      "evidence": [],
      "coverage": {
        "source_test": false,
        "derived_test": false
      }
    }
  ],
  "unmapped_public_apis": []
}
```

### 6.5 `01d-state-transition-map.json`

用途：描述 API 对状态的影响。

必须包含：

```json
{
  "states": [],
  "transitions": [
    {
      "api": "...",
      "from": "...",
      "to": "...",
      "preconditions": [],
      "effects": [],
      "return_behavior": "...",
      "state_preservation_on_failure": true,
      "evidence": []
    }
  ]
}
```

### 6.6 `01e-api-behavior-map.json`

用途：逐 API 描述行为。

必须包含：

```json
{
  "apis": [
    {
      "name": "...",
      "signature": "...",
      "kind": "init|query|mutation|delete|count|other",
      "inputs": [],
      "outputs": [],
      "side_effects": [],
      "failure_modes": [],
      "evidence": []
    }
  ]
}
```

### 6.7 `01f-test-coverage-map.json`

用途：映射 source tests 和 derived tests 对能力的覆盖。

必须包含：

```json
{
  "source_tests": [],
  "source_assertions": [],
  "covered_apis": [],
  "covered_capabilities": [],
  "uncovered_capabilities": [],
  "required_derived_tests": [],
  "generated_derived_tests": []
}
```

### 6.8 `01g-missing-capability-report.md`

用途：可读阻断报告。

必须包含：

```text
status
first_blocking_point
missing public APIs
missing capabilities
missing data invariants
missing state transitions
missing boundary tests
missing error-path tests
severity
```

### 6.9 `semantic-audit-report.md`

用途：最终语义审计。

必须包含：

```text
source analysis gate result
capability completeness gate result
state invariant gate result
derived test coverage gate result
cargo build/test result
unsafe result
repair loop result
final semantic verdict
```

---

## 7. 场景分类设计与验收条件

本章是本设计的核心：所有能力按场景分类，每类场景必须有分析要求、verify 要求、生成要求和验收条件。

---

### 场景 A：输入与题面解析场景

#### A.1 风险

- Agent 把 `work/code/README.md` 当作源码 README；
- Agent 把 `work/code` 当作 `SOURCE_ROOT`；
- `SOURCE_ROOT` 不存在或不是 C 项目根；
- 输出项目名没有从 README/题面解析，而是硬编码；
- Windows / Linux 入口不一致。

#### A.2 解决方案

- `source-requirement-reader` 只负责读取 `SOURCE_ROOT`、`SOURCE_ROOT/README|READNE`、`work/code/README.md`；
- `source-requirement-verifier` 独立验证：
  - `SOURCE_ROOT` 存在；
  - `SOURCE_ROOT` 下存在源码目录或 README 声明的源码目录；
  - `work/code/README.md` 只能作为任务要求 fallback，不能作为源码根；
  - `output_project_name` 需要有证据来源。

#### A.3 产物

```text
logs/trace/c-to-rust/00-requirement-extraction.json
logs/trace/c-to-rust/00-requirement-verification.json
```

#### A.4 验收条件

| 条件 | 必须结果 |
|---|---|
| `SOURCE_ROOT` 存在 | true |
| `SOURCE_ROOT` 不是 `work/code` | true |
| 源码 README/READNE 被识别 | true，或明确 fallback 原因 |
| `source_dirs` 存在 | true |
| `test_dirs` 存在 | true |
| `output_project_name` 有证据来源 | true |
| `output_project_dir` 为 `work/output/<name>` | true |

失败时：

```text
status: BLOCKED_WITH_REPORT
first_blocking_point: A_SOURCE_ROOT 或 B_REQUIREMENT_PARSE
```

---

### 场景 B：C 源码结构识别场景

#### B.1 风险

- 漏掉 `.h` 中 public API；
- 漏掉 `.c` 中 definition；
- 将测试/示例/工具代码误判为核心逻辑；
- 只得到函数列表，没有模块结构；
- API declaration 与 definition 不一致未发现。

#### B.2 解决方案

- `source-structure-analyzer` 构建结构图；
- `source-structure-verifier` 用不同扫描策略复核：
  - header declarations；
  - C definitions；
  - test references；
  - README 指定目录。

#### B.3 产物

```text
logs/trace/c-to-rust/01a-structure-map.json
logs/trace/c-to-rust/01a-structure-verification.json
```

#### B.4 验收条件

| 条件 | 必须结果 |
|---|---|
| core `.c` 文件数量 > 0 | true |
| public header 数量 > 0 | 如项目存在 header，则 true |
| public API count > 0 | true |
| 每个 public declaration 有 definition 或明确 external reason | true |
| 每个 test referenced API 可追溯到 public API 或内部测试 API | true |
| 未归类源码文件数量 | 0 或有理由 |

失败时：

```text
status: BLOCKED_WITH_REPORT
first_blocking_point: C_SOURCE_ANALYSIS
```

---

### 场景 C：C 数据模型识别场景

#### C.1 风险

- 只翻译函数，不理解 struct 字段关系；
- fixed array + count 模式未识别；
- capacity 宏未识别；
- Rust `Vec` 与 C 数组逻辑长度关系破坏；
- 初始化 / reset 行为不完整。

#### C.2 解决方案

- `c-data-model-analyzer` 分析：
  - struct / typedef / enum；
  - macro capacity；
  - array field；
  - count / size / len field；
  - field invariant；
  - Rust mapping。
- `c-data-model-verifier` 独立检查字段覆盖和 invariant 覆盖。

#### C.3 产物

```text
logs/trace/c-to-rust/01b-data-model-map.json
logs/trace/c-to-rust/01b-data-model-verification.json
```

#### C.4 验收条件

| 条件 | 必须结果 |
|---|---|
| 所有 public struct 被识别 | true |
| 所有 public struct 字段被列出 | true |
| capacity 常量被识别 | 如存在，则 true |
| fixed array + count 被识别 | 如存在，则 true |
| 每个状态字段有 semantic role | true |
| 每个 invariant 有源码证据 | true |
| Rust mapping 不破坏 invariant | true |

失败时：

```text
status: BLOCKED_WITH_REPORT
first_blocking_point: C_SOURCE_ANALYSIS
```

---

### 场景 D：API 行为分析场景

#### D.1 风险

- API 只被映射为名字，不知道语义；
- init/query/mutation/delete/count 行为混淆；
- return value 行为遗漏；
- side effect 遗漏；
- failure mode 未识别。

#### D.2 解决方案

- `c-api-behavior-analyzer` 对每个 public API 建模；
- `c-api-behavior-verifier` 复核：
  - 参数语义；
  - 返回值语义；
  - 状态副作用；
  - 错误路径。

#### D.3 产物

```text
logs/trace/c-to-rust/01e-api-behavior-map.json
logs/trace/c-to-rust/01e-api-behavior-verification.json
```

#### D.4 验收条件

| 条件 | 必须结果 |
|---|---|
| 每个 public API 有 behavior entry | true |
| 每个 API 有 kind 分类 | true |
| 每个 mutating API 有 side effects | true |
| 每个 API return behavior 明确 | true |
| 每个 failure path 有返回语义 | 如存在，则 true |
| API behavior 有源码证据 | true |

失败时：

```text
status: BLOCKED_WITH_REPORT
first_blocking_point: C_SOURCE_ANALYSIS
```

---

### 场景 E：能力模型分析场景

#### E.1 风险

- 函数都翻译了，但项目能力遗漏；
- API 与能力关系不清；
- 一个能力跨多个 API 时未合并；
- 边界能力没有测试。

#### E.2 解决方案

- `c-capability-analyzer` 从 API、数据模型、状态模型、测试中抽象能力；
- `c-capability-verifier` 检查每个 public API 是否归属能力，每个能力是否有行为、证据、覆盖计划。

#### E.3 产物

```text
logs/trace/c-to-rust/01c-capability-map.json
logs/trace/c-to-rust/01c-capability-verification.json
```

#### E.4 验收条件

| 条件 | 必须结果 |
|---|---|
| capability count > 0 | true |
| 每个 public API 属于至少一个 capability | true |
| 每个 capability 有 normal path | true |
| 每个 capability 有 boundary/error path 分析 | 如存在，则 true |
| 每个 capability 有源码证据 | true |
| 每个 capability 有实现计划 | true |
| 每个 capability 有测试覆盖计划 | true |

失败时：

```text
status: BLOCKED_WITH_REPORT
first_blocking_point: C_SOURCE_ANALYSIS
```

---

### 场景 F：状态转移分析场景

#### F.1 风险

- reset 不完整；
- update / insert 语义混淆；
- delete 后状态不一致；
- full / not-found 等失败路径未保持状态；
- count 与 collection 不一致。

#### F.2 解决方案

- `c-state-model-analyzer` 建立状态转移图；
- `c-state-model-verifier` 独立检查所有 mutating API 是否有状态转移。

#### F.3 产物

```text
logs/trace/c-to-rust/01d-state-transition-map.json
logs/trace/c-to-rust/01d-state-transition-verification.json
```

#### F.4 验收条件

| 条件 | 必须结果 |
|---|---|
| 所有 mutating API 有状态转移 | true |
| init/reset 行为覆盖旧状态 | 如存在，则 true |
| insert/update/delete 行为明确 | 如存在，则 true |
| failure path 是否保持状态明确 | true |
| capacity boundary 有状态转移 | 如存在，则 true |
| 所有状态转移有源码证据 | true |

失败时：

```text
status: BLOCKED_WITH_REPORT
first_blocking_point: C_SOURCE_ANALYSIS
```

---

### 场景 G：C 测试覆盖分析场景

#### G.1 风险

- 源测试 assert 识别不完整；
- 只识别调用，不识别断言；
- C 测试覆盖 happy path，但没覆盖 boundary/error；
- Rust 测试没有等价覆盖。

#### G.2 解决方案

- `c-test-coverage-analyzer` 提取 source assertions、API calls、测试路径；
- `c-test-coverage-verifier` 复核 source test 与 capability 的覆盖关系；
- 缺失路径进入 `missing-capability-report.md`。

#### G.3 产物

```text
logs/trace/c-to-rust/01f-test-coverage-map.json
logs/trace/c-to-rust/01f-test-coverage-verification.json
logs/trace/c-to-rust/01g-missing-capability-report.md
```

#### G.4 验收条件

| 条件 | 必须结果 |
|---|---|
| 所有 source test 文件被识别 | true |
| source assertions count >= 实际断言数量 | true 或有解释 |
| source referenced APIs 被识别 | true |
| 每个 source assertion 有 Rust 等价计划 | true |
| 每个 capability 有 source 或 derived coverage | true |
| P0/P1 missing capability 数量 | 0 |

失败时：

```text
status: BLOCKED_WITH_REPORT
first_blocking_point: C_SOURCE_ANALYSIS 或 F_CARGO_TEST_OR_SEMANTIC
```

---

### 场景 H：Rust 实现生成场景

#### H.1 风险

- generator 基于函数名硬编码；
- generator 重新做源码分析，绕过已验证 artifact；
- Rust 数据结构破坏 C invariant；
- output 目录混乱。

#### H.2 解决方案

- `rust-implementation-generator` 只消费已验证 artifact：
  - `data-model-map.json`
  - `api-behavior-map.json`
  - `capability-map.json`
  - `state-transition-map.json`
- 输出到 `work/output/<output_project_name>/`。

#### H.3 产物

```text
work/output/<output_project_name>/Cargo.toml
work/output/<output_project_name>/src/
work/output/<output_project_name>/tests/
```

#### H.4 验收条件

| 条件 | 必须结果 |
|---|---|
| 生成项目在 `work/output/<name>` | true |
| `Cargo.toml` 存在 | true |
| `src/` 存在 | true |
| `tests/` 存在 | true |
| 所有 mapped API 有 Rust 实现 | true |
| Rust 实现有 artifact 证据来源 | true |
| 不写入 `SOURCE_ROOT` | true |

失败时：

```text
status: BLOCKED_WITH_REPORT
first_blocking_point: D_RUST_GENERATION
```

---

### 场景 I：派生语义测试生成场景

#### I.1 风险

- 只生成源测试 mirror；
- 不生成 reset / boundary / not-found / delete / error path 测试；
- 测试含断言但没有覆盖关键能力。

#### I.2 解决方案

- `rust-test-generator` 根据 coverage map 和 missing capability report 生成：
  - `source_migration.rs`
  - `semantic_invariants.rs`
- 测试来源必须能追溯到 capability / state transition / invariant。

#### I.3 必须覆盖的测试类别

通用类别，不硬编码 API 名称：

| 类别 | 说明 |
|---|---|
| reset-after-mutation | 已有状态后重新初始化，旧逻辑状态失效 |
| capacity-boundary | 固定容量上限、满容量失败、状态不变 |
| not-found-query | 查询不存在元素的返回语义 |
| not-found-delete | 删除不存在元素的返回语义和状态保持 |
| update-existing | 已存在元素更新不增加逻辑数量 |
| delete-head-middle-tail | 删除首部、中部、尾部后状态一致 |
| state-preservation-after-error | 失败操作不破坏已有状态 |

#### I.4 验收条件

| 条件 | 必须结果 |
|---|---|
| `source_migration.rs` 存在 | true |
| `semantic_invariants.rs` 存在 | true |
| 每个 P0/P1 missing capability 有 derived test | true |
| 每个 state invariant 有测试 | true |
| 测试不是空断言或 smoke test | true |
| cargo test 中执行 derived tests | true |

失败时：

```text
status: BLOCKED_WITH_REPORT
first_blocking_point: F_CARGO_TEST_OR_SEMANTIC
```

---

### 场景 J：源码分析 Verify Gate 场景

#### J.1 风险

- analyzer 幻觉；
- verifier 没有独立复核；
- artifact 缺字段但流程继续；
- generator 基于不完整模型生成。

#### J.2 解决方案

新增 `source_analysis_verify_gate.py`。

Gate 汇总验证：

```text
00-requirement-extraction.json
01a-structure-map.json
01b-data-model-map.json
01c-capability-map.json
01d-state-transition-map.json
01e-api-behavior-map.json
01f-test-coverage-map.json
01g-missing-capability-report.md
```

#### J.3 产物

```text
logs/trace/c-to-rust/source-analysis-verify-report.md
logs/trace/c-to-rust/source-analysis-verify.json
```

#### J.4 验收条件

| 条件 | 必须结果 |
|---|---|
| 所有 required artifact 存在 | true |
| 所有 analyzer artifact 有 verifier artifact | true |
| public API count == mapped behavior API count | true |
| unmapped public APIs 为空 | true |
| capability 无 P0/P1 unresolved | true |
| data invariants 有测试计划 | true |
| source assertions 有 Rust 覆盖计划 | true |

失败时：

```text
status: BLOCKED_WITH_REPORT
first_blocking_point: C_SOURCE_ANALYSIS
```

---

### 场景 K：Cargo / Unsafe / Semantic Audit 场景

#### K.1 风险

- cargo test 过但 semantic gate 弱；
- unsafe 比例符合但语义不等价；
- derived tests 没执行；
- semantic audit 未检查 capability coverage。

#### K.2 解决方案

`semantic-audit-verifier` 必须检查：

```text
cargo build
cargo test
unsafe ratio
API mapping
capability coverage
state invariant coverage
derived semantic tests
repair loop
```

#### K.3 产物

```text
logs/trace/c-to-rust/06-verification-report.md
logs/trace/c-to-rust/unsafe-ratio.json
logs/trace/c-to-rust/semantic-audit-report.md
```

#### K.4 验收条件

| 条件 | 必须结果 |
|---|---|
| `cargo build --locked` 通过 | true |
| `cargo test --locked -- --nocapture` 通过 | true |
| unsafe ratio < 10% | true |
| semantic invariant tests 全部执行 | true |
| semantic audit 无 P0/P1 | true |
| semantic gate 只在全部通过后 true | true |

失败时：

```text
status: BLOCKED_WITH_REPORT
first_blocking_point: E_CARGO_BUILD 或 F_CARGO_TEST_OR_SEMANTIC
```

---

### 场景 L：Repair Loop 场景

#### L.1 风险

- verify 失败后直接 BLOCKED，没有尝试修复；
- 修复没有记录；
- 修复轮次无限循环；
- 修复污染 source analysis artifact。

#### L.2 解决方案

`repair-loop-agent`：

- 最大 3 轮；
- 每轮只根据失败类型修复最小范围；
- 修复后重新执行 cargo / semantic audit；
- 不允许修改 `SOURCE_ROOT`；
- 不允许掩盖失败。

#### L.3 产物

```text
logs/trace/c-to-rust/repair-rounds.json
logs/trace/c-to-rust/repair-round-01.md
logs/trace/c-to-rust/repair-round-02.md
logs/trace/c-to-rust/repair-round-03.md
```

#### L.4 验收条件

| 条件 | 必须结果 |
|---|---|
| repair max rounds = 3 | true |
| 每轮有失败原因 | true |
| 每轮有修改范围 | true |
| 每轮有复测结果 | true |
| 最终未通过时 BLOCKED | true |
| 最终通过时 READY | true |

---

### 场景 M：上下文隔离与防爆炸场景

#### M.1 风险

- 单 agent 读取全仓库、全日志、全源码；
- 长上下文中混入历史 prompt；
- 后续阶段覆盖前序结论；
- generator 再次分析源码，造成不一致。

#### M.2 解决方案

每个 subagent 只读必要输入。

| Subagent | 允许读取 |
|---|---|
| requirement reader | `SOURCE_ROOT/README|READNE`、`work/code/README.md` |
| structure analyzer | `source_dirs`、headers、tests 路径列表 |
| data model analyzer | `.h`、struct 所在 `.c/.h`、macros |
| capability analyzer | structure map、data model map、API bodies、tests |
| state model analyzer | API behavior map、data model map |
| test coverage analyzer | tests、capability map、state map |
| generator | 已验证 maps，不重新全量源码分析 |
| verifier | 当前阶段 artifact + 最小源码证据 |

#### M.3 验收条件

| 条件 | 必须结果 |
|---|---|
| 每个 subagent 文档明确输入范围 | true |
| 每个 artifact 有 producer | true |
| 每个 artifact 有 verifier | true |
| generator 不重新做全量 source analysis | true |
| logs 不出现大段历史 prompt | true |

---

### 场景 N：输出目录与报告定位场景

#### N.1 风险

- Rust 项目生成到根目录，评委找不到或误判；
- 输出到 SOURCE_ROOT，污染输入源码；
- `INSTRUCTION.md` 和 `result/output.md` 没告诉位置；
- Windows / Linux 输出位置不一致。

#### N.2 解决方案

统一输出：

```text
work/output/<output_project_name>/
```

`INSTRUCTION.md` 与 `INSTRUCTION.linux.md` 明确：

```text
Generated Rust Project:
work/output/<output_project_name>/

Current task:
work/output/flashDB_rust/
```

`result/output.md` 明确：

```text
rust_project: work/output/flashDB_rust
cargo_toml: work/output/flashDB_rust/Cargo.toml
```

#### N.3 验收条件

| 条件 | 必须结果 |
|---|---|
| `work/output/<name>/Cargo.toml` 存在 | true |
| 根目录 `flashDB_rust` 不存在 | true |
| 不写入 `SOURCE_ROOT/flashDB_rust` | true |
| `INSTRUCTION.md` 说明输出位置 | true |
| `result/output.md` 说明输出位置 | true |
| Windows / Linux 脚本使用同一位置 | true |

---

## 8. Runner 编排设计

建议新增：

```text
work/runtime/subagent_pipeline.py
work/runtime/source_analysis_verify_gate.py
```

`loopforge_runner.py` 调用顺序：

```python
run_requirement_reader()
run_requirement_verifier()
run_structure_analyzer()
run_structure_verifier()
run_data_model_analyzer()
run_data_model_verifier()
run_api_behavior_analyzer()
run_api_behavior_verifier()
run_capability_analyzer()
run_capability_verifier()
run_state_model_analyzer()
run_state_model_verifier()
run_test_coverage_analyzer()
run_test_coverage_verifier()
run_source_analysis_verify_gate()
run_rust_generator()
run_rust_test_generator()
run_cargo_verify()
run_unsafe_gate()
run_semantic_audit()
run_repair_loop_if_needed()
write_final_report()
```

---

## 9. Skill 强化要求

修改：

```text
work/skills/c-to-rust-migration/SKILL.md
```

新增章节：

```md
## Subagent Source Analysis and Verification Policy

Do not generate Rust code from a single-pass function list.

Before Rust generation, the harness must produce and verify:

- requirement extraction
- source structure map
- data model map
- API behavior map
- capability map
- state transition map
- test coverage map
- missing capability report

Each analyzer output must be independently verified by a verifier subagent.

Every claim must include source evidence.

If any source-analysis verifier fails, stop with:

- status: `BLOCKED_WITH_REPORT`
- first_blocking_point: `C_SOURCE_ANALYSIS`

Do not report `READY_FOR_EVALUATION` until:

- source analysis verify gate passes
- generated Rust project builds
- source migration tests pass
- semantic invariant tests pass
- unsafe gate passes
- semantic audit passes
- repair loop has no unresolved failures
```

---

## 10. 实施阶段规划

### Phase 1：只读源码分析 artifact 落盘

目标：不改生成逻辑，只新增结构化分析文件。

交付：

```text
00-requirement-extraction.json
01a-structure-map.json
01b-data-model-map.json
01c-capability-map.json
01d-state-transition-map.json
01e-api-behavior-map.json
01f-test-coverage-map.json
01g-missing-capability-report.md
```

验收：

```text
所有 artifact 存在
所有 public API 被识别
所有 capability 有源码证据
missing report 能指出测试缺口
```

### Phase 2：Verifier subagent 与 Source Analysis Gate

目标：每个 analyzer 有 verifier，source analysis gate 能阻断缺项。

验收：

```text
所有 analyzer artifact 有 verifier artifact
source-analysis-verify-report.md 存在
故意删除一个 API 映射时 gate 能 BLOCKED
```

### Phase 3：Generator 消费已验证 artifact

目标：Rust 生成不再自己重新分析源码，而是消费 verified maps。

验收：

```text
Rust API 实现可追溯到 api-behavior-map
Rust 数据结构可追溯到 data-model-map
semantic tests 可追溯到 capability/state/test coverage maps
```

### Phase 4：Semantic Audit 与 Repair Loop 强化

目标：P0/P1 语义问题能被测试发现并回修。

验收：

```text
reset-after-mutation 测试存在并通过
capacity-boundary 测试存在并通过
not-found query/delete 测试存在并通过
delete head/middle/tail 测试存在并通过
repair-rounds.json 记录完整
```

### Phase 5：无人托管 E2E 验收

目标：只从 `INSTRUCTION.md` 进入，自动产出 READY 或 BLOCKED。

验收：

```text
result/output.md
result/issues/00-summary.md
logs/interaction.md
logs/trace/
work/output/flashDB_rust/Cargo.toml
cargo build --locked
cargo test --locked -- --nocapture
```

---

## 11. 总体验收清单

最终必须满足：

### 11.1 Artifact 完整性

```text
logs/trace/c-to-rust/00-requirement-extraction.json
logs/trace/c-to-rust/00-requirement-verification.json
logs/trace/c-to-rust/01a-structure-map.json
logs/trace/c-to-rust/01a-structure-verification.json
logs/trace/c-to-rust/01b-data-model-map.json
logs/trace/c-to-rust/01b-data-model-verification.json
logs/trace/c-to-rust/01c-capability-map.json
logs/trace/c-to-rust/01c-capability-verification.json
logs/trace/c-to-rust/01d-state-transition-map.json
logs/trace/c-to-rust/01d-state-transition-verification.json
logs/trace/c-to-rust/01e-api-behavior-map.json
logs/trace/c-to-rust/01e-api-behavior-verification.json
logs/trace/c-to-rust/01f-test-coverage-map.json
logs/trace/c-to-rust/01f-test-coverage-verification.json
logs/trace/c-to-rust/01g-missing-capability-report.md
logs/trace/c-to-rust/source-analysis-verify-report.md
logs/trace/c-to-rust/semantic-audit-report.md
```

### 11.2 Gate 完整性

```text
requirement gate passed
structure gate passed
data model gate passed
API behavior gate passed
capability gate passed
state model gate passed
test coverage gate passed
source analysis verify gate passed
cargo build passed
cargo test passed
unsafe gate passed
semantic audit passed
repair loop passed or not needed
```

### 11.3 输出完整性

```text
work/output/flashDB_rust/Cargo.toml
work/output/flashDB_rust/src/
work/output/flashDB_rust/tests/
result/output.md
result/issues/00-summary.md
logs/interaction.md
logs/trace/
```

### 11.4 READY 条件

`result/output.md` 只能在以下条件全部满足时写：

```text
status: READY_FOR_EVALUATION
```

条件：

```text
1. source analysis verify gate passed
2. no unresolved P0/P1 missing capability
3. all public APIs mapped
4. all capabilities implemented
5. all state invariants tested
6. source migration tests pass
7. semantic invariant tests pass
8. cargo build/test pass
9. unsafe < 10%
10. repair loop has no unresolved failure
```

---

## 12. 失败分类

统一失败分类：

| 类型 | 含义 |
|---|---|
| `A_SOURCE_ROOT` | 源码路径不存在、误选、无效 |
| `B_REQUIREMENT_PARSE` | README/READNE 或题面解析失败 |
| `C_SOURCE_ANALYSIS` | 结构、数据模型、能力、状态、测试覆盖分析不完整 |
| `D_RUST_GENERATION` | Rust 项目生成失败 |
| `E_CARGO_BUILD` | cargo build 失败 |
| `F_CARGO_TEST_OR_SEMANTIC` | cargo test、语义不变量、semantic audit 失败 |
| `G_REPORT_OR_LAUNCHER` | 入口、脚本、报告生成失败 |

---

## 13. 回滚策略

如果阶段化改造导致 E2E 退化：

1. 保留当前已通过的 generator 和 semantic invariant test；
2. 将 subagent pipeline 以 feature flag 接入：

```text
LOOPFORGE_STRICT_SOURCE_ANALYSIS=1
```

3. 默认先只落盘 artifact，不阻断；
4. 验证稳定后再启用 gate；
5. 每阶段单独提交，便于回滚。

---

## 14. 建议提交拆分

| 提交 | 内容 |
|---|---|
| Commit 1 | Add source analysis artifact pipeline |
| Commit 2 | Add source analysis verifier artifacts and gate |
| Commit 3 | Add subagent definitions for source analysis pipeline |
| Commit 4 | Make generator consume verified capability artifacts |
| Commit 5 | Strengthen semantic audit and repair loop gating |
| Commit 6 | Normalize output under work/output and update instructions |
| Commit 7 | Run unattended E2E and update result/log evidence |

---

## 15. 最终结论

当前框架下一步真正要补的不是单个 bug，而是：

```text
源码分析可信度
+ 分阶段 subagent 隔离
+ 独立 verifier
+ source analysis gate
+ capability coverage gate
+ semantic repair loop
```

只有当 C 源码结构、数据模型、能力模型、状态转移、测试覆盖都被结构化建模并独立 verify 后，Rust 生成和 semantic gate 才有可信输入。

最终目标不是“cargo test 通过”，而是：

```text
一个陌生评测 agent 只读 INSTRUCTION.md，传入 SOURCE_ROOT，框架无人托管执行，自动分析、生成、验证、回修，并在 result/output.md 中给出可信 READY 或明确 BLOCKED。
```

