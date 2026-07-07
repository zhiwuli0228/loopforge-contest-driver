# LoopForge 设计与实现不一致校验工程设计文档

> 文档版本：v0.1  
> 工程名称：`loopforge-design-implementation-consistency`  
> 推荐分支：`design_impl_consistency_claude`  
> 基线分支：`origin/c_2_rust_claude`  
> 默认语言适配器：Java  
> 核心定位：语言无关的设计与实现一致性校验框架  
> 默认执行模式：`analyze-only`  

---

## 1. 背景与目标

当前 `loopforge-contest-driver` 已经在 `c_2_rust_claude` 分支中沉淀出较完整的 Loop Engineering 执行框架，包括阶段化流水线、子代理隔离、证据链输出、工具层零判断、结果报告和可追溯执行日志。

在此基础上，新的工程方向不再面向 C 到 Rust 的迁移，而是面向更通用的工程治理场景：

> 对设计文档、需求规格、架构约束、接口约定、错误码规范、状态流转规则与真实代码实现之间的一致性进行校验，并输出证据化差异报告。

该工具不应被设计成 Java 专用工具。Java 仅作为默认语言适配器和第一验证场景。核心能力应脱离编程语言范畴，围绕“设计资产”和“实现资产”之间的可追溯映射与 Drift 分析展开。

---

## 2. 核心结论

建议从 `c_2_rust_claude` 拉出新分支进行定制：

```bash

git fetch origin
git checkout -b design_impl_consistency_claude origin/c_2_rust_claude

```

新工程的核心定位为：

```text
Design-Implementation Consistency Checker
  = Language-Agnostic Core
  + Default Java Adapter
  + Pluggable Language Adapters
  + Domain / Project Profiles
```

也就是说，工程不直接判断“Java Controller 是否正确”，而是判断：

```text
设计中定义的行为、接口、状态、数据、异常、配置、安全、测试约束，
在实现资产中是否存在、是否一致、是否可验证。
```

---

## 3. 工程定位

### 3.1 工程名称

推荐名称：

```text
loopforge-design-implementation-consistency
```

可简称：

```text
loopforge-consistency-checker
```

不建议使用以下名称：

```text
java-design-consistency-checker
java-implementation-validator
spring-design-checker
```

原因：这些名称会把工程误导为 Java / Spring 专用工具，不符合通用 Loop Engineering 的演进目标。

---

### 3.2 核心能力

| 能力 | 说明 |
|---|---|
| 设计资产读取 | 读取需求文档、设计文档、接口规格、状态机说明、错误码规范等。 |
| 实现资产扫描 | 扫描源码、配置、接口定义、测试文件、错误码定义、数据模型等。 |
| 设计模型抽取 | 将非结构化或半结构化设计资产转换为统一 Design Model。 |
| 实现模型抽取 | 将不同语言、框架、项目结构转换为统一 Implementation Model。 |
| 可追溯映射 | 建立设计项与实现项之间的 Traceability Link。 |
| Drift 分析 | 识别设计与实现之间的缺失、冗余、语义偏差和风险。 |
| 证据化报告 | 每条问题必须绑定设计证据、实现证据、判断理由、影响范围。 |
| 可选修复计划 | 默认只输出修复建议，不修改代码。 |
| 可选受控修复 | 显式开启后，按修复计划进行受控补丁。 |
| 验证闭环 | 支持自动识别或配置验证命令，输出最终校验报告。 |

---

## 4. 设计原则

### 4.1 Core 语言无关

Core 只识别抽象模型，不识别具体语言和框架。

错误设计：

```text
检查 Controller 是否实现设计接口。
```

正确设计：

```text
检查 DesignInterface 是否存在对应 ImplementationEndpoint。
```

`Controller`、`Service`、`Mapper`、`Entity`、`Spring`、`Maven` 等概念只能存在于 Java Adapter 中，不能污染 Core。

---

### 4.2 Java 是默认适配器，不是默认世界观

默认支持 Java 是合理的，因为当前主要落地场景大概率是 Java / Spring 存量系统。

但工程结构必须满足以下要求：

```text
Core 不依赖 Java。
Java Adapter 依赖 Core Model。
其他语言 Adapter 可以替换 Java Adapter。
```

默认配置可以是 Java：

```yaml
language:
  default: java
  detection: auto
  adapter: java
  fallback_adapter: generic
```

但工程名称、Core 模型、子代理职责、报告结构都不能 Java-only。

---

### 4.3 工具层零判断

Python / Shell 工具只负责：

- 文件扫描；
- 文本抽取；
- 符号索引；
- JSON 结构化；
- 验证命令执行；
- 报告文件写入。

工具层不负责：

- 判断是否一致；
- 判断是否阻塞；
- 判断是否应该修复；
- 判断修复是否语义正确。

最终判断由 Agent 基于证据完成。

---

### 4.4 子代理隔离上下文

大项目源码不能一次性塞入主上下文。必须通过阶段化子代理处理：

```text
主编排器只传递文件路径和阶段输出摘要。
子代理读取声明输入。
子代理写入声明输出。
子代理返回简短结论。
跨阶段通信只通过 logs/trace/consistency 下的文件。
```

---

### 4.5 默认只读分析

默认模式必须是：

```yaml
execution:
  allow_patch: false
  allow_code_generation: false
  default_action: analyze_only
```

也就是说，第一目标是“找出设计与实现不一致”，不是“自动改代码”。

修复能力必须作为二阶段能力显式开启：

```yaml
execution:
  allow_patch: true
  max_repair_rounds: 1
```

---

### 4.6 证据优先

任何 Drift Finding 都必须包含：

- 设计证据；
- 实现证据；
- 判断理由；
- 风险等级；
- 影响范围；
- 建议动作。

不允许输出没有证据的泛化判断。

---

## 5. 总体架构

```text
work/design/
    ↓
Design Scanner
    ↓
Design Model Extraction
    ↓
Design Model

SOURCE_ROOT
    ↓
Language Adapter / Generic Adapter
    ↓
Implementation Model Extraction
    ↓
Implementation Model

Design Model + Implementation Model
    ↓
Traceability Mapping
    ↓
Drift Analysis
    ↓
Risk Classification
    ↓
Report / Repair Plan / Optional Patch
```

---

## 6. 架构分层

### 6.1 Language-Agnostic Core

建议目录：

```text
work/core/
├── design_model.py
├── implementation_model.py
├── traceability_model.py
├── drift_taxonomy.py
├── evidence_contract.py
├── severity_policy.py
└── report_model.py
```

Core 中只允许出现抽象概念。

| Core 概念 | 说明 |
|---|---|
| `DesignRequirement` | 设计要求。 |
| `DesignConstraint` | 设计约束。 |
| `DesignInterface` | 设计接口。 |
| `DesignStateFlow` | 状态流转设计。 |
| `DesignDataModel` | 设计数据模型。 |
| `ImplementationSymbol` | 实现符号。 |
| `ImplementationEndpoint` | 实现接口。 |
| `ImplementationDataModel` | 实现数据模型。 |
| `ImplementationBehavior` | 实现行为。 |
| `ImplementationConfig` | 实现配置。 |
| `TraceabilityLink` | 设计与实现映射关系。 |
| `DriftFinding` | 不一致发现。 |
| `EvidenceRef` | 证据引用。 |

Core 不允许出现：

```text
Controller
Service
Mapper
Entity
Spring
SpringBoot
Maven
Gradle
JUnit
MyBatis
```

---

### 6.2 Default Java Adapter

Java Adapter 是默认适配器，用于将 Java / Spring 项目转换为统一的 Implementation Model。

建议目录：

```text
work/adapters/java/
├── java_project_detector.py
├── java_symbol_scanner.py
├── java_endpoint_scanner.py
├── java_dto_scanner.py
├── java_error_code_scanner.py
├── java_config_scanner.py
├── java_test_detector.py
└── java_verification_adapter.py
```

Java Adapter 可识别：

| Java / Spring 概念 | 转换后的 Core 概念 |
|---|---|
| `@RestController` | `ImplementationEndpoint` |
| `@RequestMapping` / `@PostMapping` | `ImplementationEndpoint.method/path` |
| DTO / POJO | `ImplementationDataModel` |
| Enum / 常量类 | `ImplementationErrorCode` |
| Service 方法 | `ImplementationBehavior` |
| YAML / Properties | `ImplementationConfig` |
| JUnit 测试 | `ImplementationTestEvidence` |
| MyBatis Mapper | `ImplementationPersistence` |

示例转换：

```java
@RestController
@PostMapping("/orders")
public OrderResponse createOrder(@RequestBody CreateOrderRequest request) {
    return orderService.createOrder(request);
}
```

转换为：

```yaml
kind: endpoint
name: createOrder
method: POST
path: /orders
input_model: CreateOrderRequest
output_model: OrderResponse
evidence:
  file: src/main/java/.../OrderController.java
  symbol: createOrder
```

---

### 6.3 Generic Adapter

Generic Adapter 必须存在，用于非 Java 项目或 Java 识别失败时降级分析。

建议目录：

```text
work/adapters/generic/
├── generic_file_inventory.py
├── generic_symbol_indexer.py
├── generic_config_scanner.py
├── generic_test_detector.py
└── generic_text_evidence_scanner.py
```

Generic Adapter 支持：

| 能力 | 支持程度 |
|---|---|
| 文件扫描 | 支持 |
| 目录结构识别 | 支持 |
| Markdown / YAML / JSON 读取 | 支持 |
| 配置文件抽取 | 支持 |
| 测试文件存在性判断 | 支持 |
| 简单函数 / 类 / 符号索引 | 部分支持 |
| 业务语义判断 | 依赖 Agent |

---

### 6.4 Pluggable Language Adapters

未来可扩展：

```text
work/adapters/
├── java/
├── python/
├── go/
├── rust/
├── typescript/
└── generic/
```

所有 Adapter 必须输出统一结构：

```yaml
implementation_model:
  endpoints: []
  symbols: []
  data_models: []
  configs: []
  state_flows: []
  error_codes: []
  tests: []
  dependencies: []
```

---

## 7. 执行流水线设计

建议将原 C2Rust 阶段改造为以下 10 阶段：

| Phase | 阶段名称 | 子代理 | 输入 | 输出 |
|---:|---|---|---|---|
| 0 | Preflight | `dic-00-preflight.md` | 配置、路径、模式 | `00-preflight.md/json` |
| 1 | Design Intake | `dic-01-design-intake.md` | `work/design` | `01-design-inventory.md/json` |
| 2 | Source Inventory | `dic-02-source-inventory.md` | `SOURCE_ROOT` | `02-source-inventory.md/json` |
| 3 | Design Model Extraction | `dic-03-design-model.md` | 设计清单 | `03-design-model.json` |
| 4 | Implementation Model Extraction | `dic-04-implementation-model.md` | 源码清单、语言适配器 | `04-implementation-model.json` |
| 5 | Traceability Mapping | `dic-05-traceability-map.md` | 设计模型、实现模型 | `05-traceability-map.md/json` |
| 6 | Drift Analysis | `dic-06-drift-analysis.md` | 映射结果 | `06-drift-report.md/json` |
| 7 | Risk Classification | `dic-07-risk-classification.md` | Drift 报告 | `07-risk-classification.md/json` |
| 8 | Repair Plan / Optional Patch | `dic-08-repair-plan.md` | 风险报告、执行开关 | `08-repair-plan.md` / patch |
| 9 | Verification & Finalize | `dic-09-finalize.md` | 全部证据、验证结果 | `result/output.md` |

---

## 8. 子代理职责设计

### 8.1 `dic-00-preflight.md`

职责：

- 检查 `work/loopforge.config.yaml` 是否存在；
- 检查 `work/design` 是否存在；
- 检查 `SOURCE_ROOT` 是否存在；
- 检查输出目录是否可写；
- 检查当前模式是否为 `consistency-check`；
- 检查是否允许补丁；
- 生成前置检查报告。

禁止：

- 不得读取大量源码；
- 不得判断设计与实现是否一致；
- 不得修改业务代码。

---

### 8.2 `dic-01-design-intake.md`

职责：

- 读取设计资产；
- 建立设计文档索引；
- 标记需求、接口、数据、状态、错误码、配置、安全、测试等候选信息；
- 输出设计资产清单。

输出示例：

```yaml
design_inventory:
  documents:
    - file: work/design/README.md
      type: design_entry
      sections:
        - title: 接口设计
        - title: 状态流转
        - title: 错误码约束
```

---

### 8.3 `dic-02-source-inventory.md`

职责：

- 扫描源码目录；
- 自动识别语言和框架；
- 建立文件级和模块级索引；
- 选择默认语言适配器；
- 输出源代码资产清单。

禁止：

- 不得一次性读取全部源码内容；
- 不得在该阶段做 Drift 判断。

---

### 8.4 `dic-03-design-model.md`

职责：

- 将设计资产转换为 Design Model；
- 提取设计要求、设计接口、状态流、数据模型、错误码、配置约束、安全约束、测试要求；
- 为每个模型元素绑定证据。

输出核心文件：

```text
logs/trace/consistency/03-design-model.json
```

---

### 8.5 `dic-04-implementation-model.md`

职责：

- 根据 `language.adapter` 调用对应语言适配器；
- 将源码实现转换为 Implementation Model；
- 对 Java 项目默认启用 Java Adapter；
- Java 识别失败时降级到 Generic Adapter。

输出核心文件：

```text
logs/trace/consistency/04-implementation-model.json
```

---

### 8.6 `dic-05-traceability-map.md`

职责：

- 建立设计模型和实现模型之间的映射；
- 标记强匹配、弱匹配、未匹配、冲突匹配；
- 输出 Traceability Map。

映射关系示例：

```yaml
traceability_links:
  - design_id: API-001
    implementation_id: IMPL-API-003
    relation: matched
    confidence: high
    evidence:
      reason: path and method matched
```

---

### 8.7 `dic-06-drift-analysis.md`

职责：

- 基于 Traceability Map 识别不一致；
- 输出 Drift Finding；
- 每条 Drift 必须包含证据和理由。

禁止：

- 不得输出无证据结论；
- 不得因为命名不同直接判定不一致；
- 不得因为实现中暂未识别到就直接判定缺失，应标记置信度。

---

### 8.8 `dic-07-risk-classification.md`

职责：

- 对 Drift Finding 进行风险分级；
- 识别阻塞级问题；
- 区分设计缺失、实现缺失、语义不一致、测试缺口；
- 输出风险摘要。

风险级别：

| 等级 | 含义 |
|---|---|
| `CRITICAL` | 直接违反核心业务流程、安全约束、数据一致性或关键接口契约。 |
| `HIGH` | 影响主要功能正确性，可能导致线上缺陷。 |
| `MEDIUM` | 存在行为偏差或边界条件缺失，但不一定阻塞主流程。 |
| `LOW` | 命名、文档、测试覆盖、非核心配置等轻量问题。 |
| `INFO` | 提示项，不构成明确不一致。 |

---

### 8.9 `dic-08-repair-plan.md`

职责：

- 默认只生成修复计划；
- 当 `allow_patch=true` 时才允许进入补丁阶段；
- 每个修复动作必须反向关联 Drift Finding；
- 必须给出验证方式。

默认禁止：

```yaml
execution:
  allow_patch: false
  allow_code_generation: false
```

---

### 8.10 `dic-09-finalize.md`

职责：

- 汇总所有阶段结果；
- 生成 `result/output.md`；
- 生成 `result/issues/00-summary.md`；
- 生成 `logs/trace/final-report.md`；
- 输出最终状态。

最终状态建议：

| 状态 | 含义 |
|---|---|
| `PASS` | 未发现关键不一致。 |
| `PASS_WITH_WARNINGS` | 存在低风险或中风险问题。 |
| `DEGRADED` | 存在高风险问题，但未阻塞整体分析。 |
| `BLOCKED_WITH_REPORT` | 存在阻塞问题或输入不足，但已输出报告。 |
| `FAILED_NO_REPORT` | 框架异常，未能生成有效报告。此状态应尽量避免。 |

---

## 9. Drift 分类模型

建议内置以下 Drift 类型：

| 类型 | 说明 | 示例 |
|---|---|---|
| `MISSING_IMPLEMENTATION` | 设计有，代码没有。 | 设计要求接口幂等，代码无幂等逻辑。 |
| `EXTRA_IMPLEMENTATION` | 代码有，设计没有。 | 实现了额外状态流转，设计未说明。 |
| `SEMANTIC_MISMATCH` | 名义存在，但语义不一致。 | 设计要求失败回滚，代码失败跳过。 |
| `API_CONTRACT_MISMATCH` | 接口入参、出参、错误码不一致。 | 设计返回错误码 A，代码返回 B。 |
| `DATA_MODEL_MISMATCH` | 表、DTO、领域对象字段不一致。 | 设计字段必填，代码允许为空。 |
| `STATE_FLOW_MISMATCH` | 状态流转不一致。 | 设计禁止逆向流转，代码允许。 |
| `ERROR_HANDLING_MISMATCH` | 异常、重试、降级策略不一致。 | 设计要求重试 3 次，代码直接失败。 |
| `CONFIG_MISMATCH` | 配置项、默认值、开关不一致。 | 设计默认关闭，代码默认开启。 |
| `SECURITY_MISMATCH` | 权限、鉴权、敏感数据处理不一致。 | 设计要求鉴权，接口未校验。 |
| `TEST_COVERAGE_GAP` | 关键设计约束缺少测试覆盖。 | 幂等、重试、状态边界没有测试。 |
| `DESIGN_AMBIGUITY` | 设计表达不足，无法可靠判断。 | 设计只说“失败要处理”，没有定义策略。 |
| `IMPLEMENTATION_UNCLEAR` | 实现复杂或动态，无法可靠识别。 | 反射、动态代理、配置驱动路径无法静态确认。 |

---

## 10. 证据模型

每条 Drift Finding 至少包含以下字段：

```yaml
drift_id: DIC-0001
type: SEMANTIC_MISMATCH
severity: HIGH
confidence: medium
summary: 订单创建幂等设计与实现不一致
design_evidence:
  file: work/design/order-design.md
  section: 幂等约束
  quote: 订单创建接口必须支持重复请求幂等返回
implementation_evidence:
  file: src/main/java/com/example/order/OrderService.java
  symbol: createOrder
  observation: 未发现幂等键校验或重复请求处理逻辑
reason: 设计要求重复提交返回原结果，当前实现每次调用均创建新订单
impact: 可能导致重复订单和重复扣费
suggested_action: 在创建订单前增加幂等键校验，或修正设计说明
repair_allowed: false
verification_hint: 增加重复请求测试用例
```

---

## 11. 配置文件设计

建议 `work/loopforge.config.yaml` 调整为：

```yaml
framework:
  name: loopforge-design-implementation-consistency
  input_model: design-plus-source
  default_mode: consistency-check

platform:
  layout: single-root
  work_dir: work
  linux_source_root_env: SOURCE_ROOT
  design_root: work/design
  artifact_dir: logs/trace
  official_submission_os: linux
  local_development_os:
    - windows
    - linux

task:
  name: design-implementation-consistency-check
  mode: consistency-check
  source: preloaded-design
  profile: profiles/examples/default-java-consistency.yaml

language:
  default: java
  detection: auto
  adapter: java
  fallback_adapter: generic
  adapters:
    - java
    - generic

core:
  analyze_dimensions:
    - api_contract
    - data_model
    - state_flow
    - business_rule
    - error_handling
    - config
    - security
    - test_coverage

execution:
  unattended: true
  allow_manual_interaction: false
  allow_code_generation: false
  allow_patch: false
  max_repair_rounds: 0
  fail_soft: true
  always_finalize: true
  commit: false
  push: false
  create_pr: false

verification:
  source: profile-or-framework-default
  working_directory: SOURCE_ROOT
  timeout_seconds: 1800
  commands:
    default:
      - auto-detect

outputs:
  result_report: result/output.md
  issue_summary: result/issues/00-summary.md
  trace_dir: logs/trace
  consistency_dir: logs/trace/consistency
  final_report: logs/trace/final-report.md
```

---

## 12. Profile 设计

默认 Java Profile：

```text
work/profiles/examples/default-java-consistency.yaml
```

建议内容：

```yaml
profile:
  name: default-java-consistency
  description: Default profile for Java/Spring design-implementation consistency checking.

language:
  adapter: java
  fallback_adapter: generic

java:
  framework_detection:
    - spring
    - springboot
    - springmvc
    - mybatis
    - maven
    - gradle

  source_patterns:
    controllers:
      - "**/*Controller.java"
      - "**/*Resource.java"
    services:
      - "**/*Service.java"
      - "**/*ServiceImpl.java"
    data_models:
      - "**/*DTO.java"
      - "**/*Request.java"
      - "**/*Response.java"
      - "**/*Entity.java"
      - "**/*VO.java"
    tests:
      - "**/*Test.java"
      - "**/*Tests.java"

  verification:
    default_commands:
      - mvn test
      - gradle test

analysis:
  dimensions:
    - api_contract
    - data_model
    - state_flow
    - business_rule
    - error_handling
    - config
    - security
    - test_coverage

severity_policy:
  api_contract_mismatch: HIGH
  state_flow_mismatch: HIGH
  security_mismatch: CRITICAL
  test_coverage_gap: MEDIUM
```

---

## 13. 目录结构建议

```text
.
├── INSTRUCTION.md
├── README.md
├── work/
│   ├── design/
│   │   └── README.md
│   ├── loopforge.config.yaml
│   ├── core/
│   │   ├── design_model.py
│   │   ├── implementation_model.py
│   │   ├── traceability_model.py
│   │   ├── drift_taxonomy.py
│   │   ├── evidence_contract.py
│   │   ├── severity_policy.py
│   │   └── report_model.py
│   ├── adapters/
│   │   ├── java/
│   │   │   ├── java_project_detector.py
│   │   │   ├── java_symbol_scanner.py
│   │   │   ├── java_endpoint_scanner.py
│   │   │   ├── java_dto_scanner.py
│   │   │   ├── java_error_code_scanner.py
│   │   │   ├── java_config_scanner.py
│   │   │   ├── java_test_detector.py
│   │   │   └── java_verification_adapter.py
│   │   └── generic/
│   │       ├── generic_file_inventory.py
│   │       ├── generic_symbol_indexer.py
│   │       ├── generic_config_scanner.py
│   │       ├── generic_test_detector.py
│   │       └── generic_text_evidence_scanner.py
│   ├── skills/
│   │   ├── loopforge-driver/
│   │   │   └── SKILL.md
│   │   └── design-implementation-consistency/
│   │       ├── SKILL.md
│   │       └── references/
│   │           ├── drift-taxonomy.md
│   │           ├── evidence-contract.md
│   │           ├── traceability-model.md
│   │           └── repair-policy.md
│   ├── subagent/
│   │   ├── dic-00-preflight.md
│   │   ├── dic-01-design-intake.md
│   │   ├── dic-02-source-inventory.md
│   │   ├── dic-03-design-model.md
│   │   ├── dic-04-implementation-model.md
│   │   ├── dic-05-traceability-map.md
│   │   ├── dic-06-drift-analysis.md
│   │   ├── dic-07-risk-classification.md
│   │   ├── dic-08-repair-plan.md
│   │   └── dic-09-finalize.md
│   ├── profiles/
│   │   ├── examples/
│   │   │   └── default-java-consistency.yaml
│   │   ├── superpower/
│   │   │   └── design-implementation-consistency-guards.yaml
│   │   └── superspec/
│   │       └── design-implementation-consistency-stages.yaml
│   ├── rules/
│   │   └── loopforge/
│   │       └── adapters/
│   │           └── design-implementation-consistency/
│   │               ├── 00-core.md
│   │               ├── 01-design-evidence.md
│   │               ├── 02-code-evidence.md
│   │               ├── 03-drift-analysis.md
│   │               ├── 04-repair-boundary.md
│   │               └── 05-final-report.md
│   ├── runtime/
│   │   ├── tools.py
│   │   ├── design_scanner.py
│   │   ├── code_inventory.py
│   │   ├── traceability_builder.py
│   │   ├── drift_classifier.py
│   │   ├── verification_runner.py
│   │   └── report_writer.py
│   └── scripts/
│       ├── run.sh
│       └── run.ps1
├── logs/
│   └── trace/
└── result/
    └── issues/
```

---

## 14. 文件改造清单

### 14.1 必改文件

| 文件 | 修改动作 |
|---|---|
| `README.md` | 从 C2Rust 说明改为一致性校验工程说明。 |
| `INSTRUCTION.md` | 替换运行入口描述，去掉 Rust / Cargo 强绑定。 |
| `work/README.md` | 改为一致性校验工作区说明。 |
| `work/loopforge.config.yaml` | `mode` 改为 `consistency-check`，默认 profile 指向 Java Consistency。 |
| `work/design/README.md` | 改为一致性校验任务契约。 |
| `work/skills/loopforge-driver/SKILL.md` | 保留入口能力，切换到新 skill。 |
| `work/runtime/tools.py` | 增加设计扫描、源码扫描、报告写入等命令。 |

---

### 14.2 新增文件

| 文件 | 说明 |
|---|---|
| `work/skills/design-implementation-consistency/SKILL.md` | 一致性校验主 Skill。 |
| `work/skills/design-implementation-consistency/references/drift-taxonomy.md` | Drift 分类说明。 |
| `work/skills/design-implementation-consistency/references/evidence-contract.md` | 证据模型规范。 |
| `work/skills/design-implementation-consistency/references/traceability-model.md` | 映射模型规范。 |
| `work/skills/design-implementation-consistency/references/repair-policy.md` | 修复边界策略。 |
| `work/subagent/dic-00-preflight.md` | 前置检查子代理。 |
| `work/subagent/dic-01-design-intake.md` | 设计读取子代理。 |
| `work/subagent/dic-02-source-inventory.md` | 源码清单子代理。 |
| `work/subagent/dic-03-design-model.md` | 设计模型抽取子代理。 |
| `work/subagent/dic-04-implementation-model.md` | 实现模型抽取子代理。 |
| `work/subagent/dic-05-traceability-map.md` | 映射子代理。 |
| `work/subagent/dic-06-drift-analysis.md` | Drift 分析子代理。 |
| `work/subagent/dic-07-risk-classification.md` | 风险分级子代理。 |
| `work/subagent/dic-08-repair-plan.md` | 修复计划子代理。 |
| `work/subagent/dic-09-finalize.md` | 最终报告子代理。 |
| `work/profiles/examples/default-java-consistency.yaml` | 默认 Java Profile。 |
| `work/profiles/superspec/design-implementation-consistency-stages.yaml` | 阶段定义。 |
| `work/profiles/superpower/design-implementation-consistency-guards.yaml` | 权限与行为守卫。 |
| `work/core/*.py` | Core 模型定义。 |
| `work/adapters/java/*.py` | Java Adapter。 |
| `work/adapters/generic/*.py` | Generic Adapter。 |

---

### 14.3 建议归档或禁用文件

以下 C2Rust 相关文件不建议直接删除，第一轮建议移动到归档目录或保留为非默认 Adapter：

```text
work/skills/c-to-rust-migration/
work/skills/c-to-rust-migration-v2/
work/rules/loopforge/adapters/c-to-rust/
work/subagent/c2r-*.md
work/runtime/rust_project_generation.py
work/runtime/check_unsafe_ratio.py
work/runtime/test_migration_validation.py
```

建议归档目录：

```text
work/archived/c-to-rust/
```

---

## 15. `tools.py` 命令设计

建议扩展以下命令：

```bash
python work/runtime/tools.py scan-design \
  --design-root work/design \
  --output logs/trace/consistency/01-design-inventory.json

python work/runtime/tools.py scan-code \
  --source-root "$SOURCE_ROOT" \
  --language auto \
  --output logs/trace/consistency/02-source-inventory.json

python work/runtime/tools.py extract-implementation \
  --source-root "$SOURCE_ROOT" \
  --adapter java \
  --fallback generic \
  --output logs/trace/consistency/04-implementation-model.json

python work/runtime/tools.py build-traceability \
  --design-model logs/trace/consistency/03-design-model.json \
  --implementation-model logs/trace/consistency/04-implementation-model.json \
  --output logs/trace/consistency/05-traceability-map.json

python work/runtime/tools.py run-verification \
  --source-root "$SOURCE_ROOT" \
  --commands '["mvn test"]'

python work/runtime/tools.py write-report \
  --result-dir result \
  --data logs/trace/consistency/final-data.json
```

注意：

```text
scan-design / scan-code / extract-implementation 只负责数据提取。
build-traceability 可输出候选映射，但不做最终一致性判断。
Drift 判断由 Agent 完成。
```

---

## 16. 输入契约设计

### 16.1 设计输入

默认路径：

```text
work/design/
```

最小输入：

```text
work/design/README.md
```

推荐结构：

```text
work/design/
├── README.md
├── requirements.md
├── api-contract.md
├── data-model.md
├── state-flow.md
├── error-code.md
├── config.md
├── security.md
└── test-expectation.md
```

---

### 16.2 源码输入

默认通过环境变量传入：

```bash
export SOURCE_ROOT=/path/to/project
```

源码目录只读，除非显式开启：

```yaml
execution:
  allow_patch: true
```

---

## 17. 输出契约设计

最终输出：

```text
result/output.md
result/issues/00-summary.md
logs/trace/final-report.md
```

阶段输出：

```text
logs/trace/consistency/
├── 00-preflight.md
├── 00-preflight.json
├── 01-design-inventory.md
├── 01-design-inventory.json
├── 02-source-inventory.md
├── 02-source-inventory.json
├── 03-design-model.json
├── 04-implementation-model.json
├── 05-traceability-map.md
├── 05-traceability-map.json
├── 06-drift-report.md
├── 06-drift-report.json
├── 07-risk-classification.md
├── 07-risk-classification.json
├── 08-repair-plan.md
└── 09-finalize.md
```

---

## 18. 报告结构建议

`result/output.md` 建议结构：

```markdown
# Design-Implementation Consistency Report

## 1. Final Status

- Status: DEGRADED
- Critical Issues: 0
- High Issues: 2
- Medium Issues: 4
- Low Issues: 3

## 2. Scope

- Design Root: work/design
- Source Root: ${SOURCE_ROOT}
- Language Adapter: java
- Fallback Adapter: generic
- Patch Enabled: false

## 3. Summary

## 4. Drift Findings

## 5. Traceability Coverage

## 6. Risk Classification

## 7. Suggested Repair Plan

## 8. Verification Result

## 9. Evidence Index
```

---

## 19. 最小可行版本范围

第一版不要做过重，建议只实现以下能力：

1. 读取 `work/design/README.md`。
2. 扫描 `SOURCE_ROOT` 目录结构。
3. 自动识别 Java / Generic。
4. 输出设计资产清单。
5. 输出源码资产清单。
6. 生成 Design Model 初版。
7. 生成 Implementation Model 初版。
8. 生成 Traceability Map 初版。
9. 识别三类 Drift：
   - `MISSING_IMPLEMENTATION`
   - `EXTRA_IMPLEMENTATION`
   - `SEMANTIC_MISMATCH`
10. 输出 `result/output.md`。
11. 默认不修改代码。

这一版的目标是跑通闭环，而不是一次性实现精准语义审计。

---

## 20. 第二阶段增强能力

第二阶段再增强：

| 增强项 | 说明 |
|---|---|
| Java AST 级扫描 | 更精准识别类、方法、注解、字段。 |
| Spring Endpoint 提取 | 自动提取 REST 接口契约。 |
| DTO 字段比对 | 支持字段必填、类型、默认值、枚举值差异。 |
| 错误码比对 | 识别设计错误码与代码错误码偏差。 |
| 状态机比对 | 对状态流转进行更精确的路径校验。 |
| 测试覆盖映射 | 判断关键设计项是否有测试覆盖。 |
| 可选修复 | 显式开启后按修复计划修改代码。 |
| 多语言 Adapter | Python / Go / TypeScript / Rust。 |

---

## 21. 推荐开发路线

### Step 1：创建分支

```bash
git fetch origin
git checkout -b design_impl_consistency_claude origin/c_2_rust_claude
```

### Step 2：改入口文档

优先修改：

```text
README.md
INSTRUCTION.md
work/README.md
work/loopforge.config.yaml
```

目标是去掉 C2Rust 语义，改成一致性校验入口。

---

### Step 3：新增 Skill 与 Profile

新增：

```text
work/skills/design-implementation-consistency/SKILL.md
work/profiles/examples/default-java-consistency.yaml
work/profiles/superspec/design-implementation-consistency-stages.yaml
work/profiles/superpower/design-implementation-consistency-guards.yaml
```

---

### Step 4：改造子代理

从现有阶段化子代理复制并重命名，替换任务语义：

```text
opencode-design-read-subagent.md        -> dic-01-design-intake.md
opencode-implementation-map-subagent.md -> dic-04-implementation-model.md
opencode-drift-analysis-subagent.md     -> dic-06-drift-analysis.md
opencode-repair-plan-subagent.md        -> dic-08-repair-plan.md
opencode-verification-subagent.md       -> dic-09-finalize.md
```

如果现有子代理名称不完全一致，以实际仓库文件为准。

---

### Step 5：实现最小 runtime

第一版只实现：

```text
work/runtime/design_scanner.py
work/runtime/code_inventory.py
work/runtime/report_writer.py
work/runtime/tools.py
```

Java Adapter 可以先做正则级和文件级识别，不必第一版引入复杂 AST。

---

### Step 6：构造样例工程

准备一个最小 Java Demo，用于验证闭环：

```text
work/code/demo-order-service/
├── pom.xml
├── src/main/java/...
└── src/test/java/...
```

故意制造 3 类问题：

1. 设计要求幂等，代码未实现。
2. 设计要求状态流 `INIT -> PAID -> DONE`，代码允许逆向流转。
3. 设计要求错误码 `ORDER_NOT_FOUND`，代码返回 `SYSTEM_ERROR`。

---

## 22. 验收标准

第一版验收标准：

| 编号 | 验收项 | 标准 |
|---|---|---|
| A1 | 可运行 | 能从 `INSTRUCTION.md` 或脚本启动完整流程。 |
| A2 | 不依赖 Java-only Core | Core 模型中不出现 Java / Spring 概念。 |
| A3 | 默认 Java Adapter | 未指定语言时优先使用 Java Adapter。 |
| A4 | Generic Fallback | Java 识别失败时能够降级通用扫描。 |
| A5 | 输出完整 | 能生成 `result/output.md` 和 `result/issues/00-summary.md`。 |
| A6 | 证据完整 | 每条 Drift 有设计证据和实现证据。 |
| A7 | 默认不修复 | `allow_patch=false` 时不得修改源码。 |
| A8 | 阶段可追溯 | `logs/trace/consistency` 下有阶段产物。 |
| A9 | 可扩展 | 能通过新增 Adapter 支持其他语言。 |

---

## 23. 风险与约束

| 风险 | 说明 | 应对 |
|---|---|---|
| 语义误判 | Agent 可能误解设计或代码。 | 强制证据引用与置信度字段。 |
| 上下文爆炸 | 大项目源码过多。 | 坚持子代理分阶段和文件交接。 |
| Java 污染 Core | 默认 Java 容易变成 Java-only。 | Core 层禁止出现 Java/Spring 概念。 |
| 设计文档质量差 | 设计不完整导致无法判断。 | 增加 `DESIGN_AMBIGUITY` 类型。 |
| 动态实现难识别 | 反射、配置驱动、动态代理难以静态分析。 | 增加 `IMPLEMENTATION_UNCLEAR` 类型。 |
| 自动修复风险 | 修复可能改变业务语义。 | 默认关闭 patch，显式开启后才允许。 |

---

## 24. 最终建议

该工程应定义为：

```text
语言无关的设计与实现一致性校验框架，
Java 作为默认适配器，
支持后续按语言、框架、领域进行插件化扩展。
```

核心不是“检查 Java 代码”，而是构建：

```text
Design Model
    ↔ Traceability Link
Implementation Model
    ↘ Drift Finding
      ↘ Evidence-based Report
```

第一版应优先追求：

```text
能运行、能输出、能证据化、能扩展、默认不改代码。
```

不建议第一版追求：

```text
复杂 AST 全覆盖、自动修复所有问题、多语言全面支持、精准业务语义理解。
```

推荐最终形态：

```text
Core：语言无关
Default Adapter：Java
Fallback Adapter：Generic
Mode：consistency-check
Default Action：analyze-only
Optional Action：repair-enabled
```

这条路线既继承了 `c_2_rust_claude` 分支已经验证过的强工程化执行框架，又避免把新工具锁死在 Java 或单一项目场景中，更符合通用 Loop Engineering 工程的长期演进方向。
