# 通用 C-to-Rust Migration Harness 设计文档

## 1. 目标

将当前 `c2rust-flashdb` 分支收敛为**通用 C-to-Rust 迁移框架**，而不是某个题目或某个源码项目的专用实现。

框架必须满足：

1. 从 `SOURCE_ROOT` 附近的 README/READNE 或 `work/code/README.md` 中读取任务约束。
2. 支持不同 C 项目、不同源码目录、不同测试目录、不同 Rust 输出项目名。
3. 框架资产、配置、skill、profile、adapter、subagent、runtime 代码中不得硬编码具体项目名、具体输出目录名、具体 API 前缀、具体业务模块名。
4. 对当前比赛题目，运行时可以从题面推导出具体项目、源码目录、测试目录和输出目录，但这些只能作为运行时派生数据出现在 `logs/`、`result/` 和生成物中。

## 2. 分层原则

### 2.1 框架层

框架层只允许出现通用概念：

- C source project
- Rust output project
- source README
- source directories
- test directories
- generated crate
- build commands
- unsafe threshold
- semantic mapping
- repair loop

框架层包括：

```text
INSTRUCTION.md
README.md
work/loopforge.config.yaml
work/runtime/*
work/skills/*
work/profiles/*
work/rules/*
work/subagent/*
```

这些文件不得硬编码具体题目名称、具体输出项目名、固定 API 名称、固定业务模块名。

### 2.2 题面输入层

题面输入层允许包含比赛要求中的具体名称。

允许位置：

```text
work/code/README.md
SOURCE_ROOT/README.md
SOURCE_ROOT/READNE.md
```

### 2.3 运行输出层

运行输出层允许出现从题面解析出的具体名称。

允许位置：

```text
result/output.md
result/issues/00-summary.md
logs/trace/**
生成的 Rust 输出项目目录
```

## 3. 最终目录命名

### 3.1 Skill

必须改为：

```text
work/skills/c-to-rust-migration/SKILL.md
```

删除：

```text
work/skills/c2rust-flashdb-migration/
```

`SKILL.md` frontmatter：

```yaml
---
name: c-to-rust-migration
description: Generic source-readme-driven C-to-Rust migration workflow. Use when a C source project must be rewritten or migrated into a Rust crate with tests and verification evidence.
---
```

`SKILL.md` 必须包含：

```md
## Generalization Boundary

This skill implements a generic C-to-Rust migration workflow. Project names, output project names, source directories, test directories, API prefixes, module hints, build commands, and unsafe thresholds must be derived from the active source README or active profile. They must not be hardcoded in the framework assets.
```

### 3.2 Profile

必须改为：

```text
work/profiles/examples/c-to-rust-migration.yaml
```

删除：

```text
work/profiles/examples/c2rust-flashdb-migration.yaml
```

建议内容：

```yaml
profile:
  name: "c-to-rust-migration"
  task_class: "migration"
  source_strategy: "source-readme-driven"

source_contract:
  source_language: "c"
  readme_candidates:
    - "README.md"
    - "README"
    - "READNE.md"
    - "readme.md"
    - "Readme.md"
  source_dirs_from_readme: true
  test_dirs_from_readme: true
  fallback_source_dirs:
    - "src"
  fallback_test_dirs:
    - "tests"

migration_contract:
  target_language: "rust"
  output_project_from_readme: true
  fallback_output_project: "rust_migration_output"
  crate_generation: "source-driven"

analysis_contract:
  required_outputs:
    - "logs/trace/c-to-rust/01-source-inventory.json"
    - "logs/trace/c-to-rust/02-api-mapping.json"
    - "logs/trace/c-to-rust/04-test-mapping.json"
  required_relations:
    - "include_graph"
    - "function_table"
    - "type_table"
    - "macro_table"
    - "api_to_module_map"
    - "test_to_api_map"

generation_contract:
  forbid:
    - "project_specific_default_api"
    - "fixed_business_demo"
    - "empty_stub_only"
    - "tests_without_assertions"
    - "semantic_equivalence_without_mapping"

repair_contract:
  enabled: true
  max_rounds_from_config: true
  required_logs:
    - "logs/trace/c-to-rust/repair-rounds.md"
    - "logs/trace/c-to-rust/repair-rounds.json"

verification_contract:
  build_commands_from_readme: true
  fallback_commands:
    - "cargo build"
    - "cargo test"
  unsafe_ratio_from_readme: true
  fallback_unsafe_ratio_max: 0.10

reporting_contract:
  required_files:
    - "result/output.md"
    - "result/issues/00-summary.md"
    - "logs/interaction.md"
    - "logs/trace"
```

### 3.3 Adapter

必须改为：

```text
work/rules/loopforge/adapters/c-to-rust/
```

删除：

```text
work/rules/loopforge/adapters/c2rust-flashdb/
```

目标文件：

```text
work/rules/loopforge/adapters/c-to-rust/
├── source-contract.md
├── output-contract.md
├── test-migration-contract.md
├── unsafe-contract.md
├── verification-contract.md
├── semantic-equivalence-contract.md
└── repair-loop-contract.md
```

所有 contract 文案只写通用 C-to-Rust 规则，不写具体题目名称。

### 3.4 Subagent

必须改名为：

```text
work/subagent/c-to-rust-source-inventory-subagent.md
work/subagent/c-to-rust-api-mapping-subagent.md
work/subagent/c-to-rust-implementation-subagent.md
work/subagent/c-to-rust-test-migration-subagent.md
work/subagent/c-to-rust-verification-subagent.md
work/subagent/c-to-rust-final-report-subagent.md
```

删除所有：

```text
work/subagent/c2rust-*.md
```

## 4. 配置修改

文件：

```text
work/loopforge.config.yaml
```

目标：配置只描述通用 migration，不写具体题目名称或输出目录。

建议结构：

```yaml
framework:
  name: "loopforge-contest-driver"
  input_model: "source-readme"
  default_mode: "migration"

platform:
  layout: "single-root"
  work_dir: "work"
  code_dir: ".code"
  local_fallback_source_dir: ".code"
  artifact_dir: "logs/trace"
  official_submission_os: "linux"
  local_development_os:
    - "windows"
    - "linux"

source:
  root_env: "SOURCE_ROOT"
  readme_required: true
  readme_candidates:
    - "README.md"
    - "README"
    - "READNE.md"
    - "readme.md"
    - "Readme.md"

task:
  name: "source-readme-driven-migration"
  mode: "migration"
  source: "source-readme"
  readme_required: true
  profile: "profiles/examples/c-to-rust-migration.yaml"

language:
  primary: "c"
  secondary:
    - "rust"

objective: "derive C-to-Rust migration requirements from source README/READNE and generate the requested Rust output project"

execution:
  unattended: true
  allow_manual_interaction: false
  max_repair_rounds: 2
  fail_soft: true
  always_finalize: true
  allow_code_generation: true
  allow_static_rule_modification: false
  commit: false
  push: false
  create_pr: false

coding_skill:
  enabled: true
  required: true
  skill: "skills/c-to-rust-migration/SKILL.md"
  apply_at:
    - "source_inventory"
    - "api_mapping"
    - "migration_plan"
    - "rust_project_generation"
    - "test_migration"
    - "verification"
  output: "logs/trace/c-to-rust/05-migration-summary.md"

verification:
  source: "profile-or-source-readme"
  working_directory: "SOURCE_README_DERIVED_OUTPUT_PROJECT"
  timeout_seconds: 600
  commands:
    default:
      - "cargo build"
      - "cargo test"

outputs:
  result_report: "result/output.md"
  issue_summary: "result/issues/00-summary.md"
  trace_dir: "logs/trace"
  interaction_log: "logs/interaction.md"
  migration_dir: "logs/trace/c-to-rust"
  source_inventory: "logs/trace/c-to-rust/01-source-inventory.md"
  api_mapping: "logs/trace/c-to-rust/02-api-mapping.md"
  migration_plan: "logs/trace/c-to-rust/03-migration-plan.md"
  implementation_summary: "logs/trace/c-to-rust/05-migration-summary.md"
  verification_report: "logs/trace/c-to-rust/06-verification-report.md"
  unsafe_report: "logs/trace/c-to-rust/unsafe-ratio.json"
  final_report: "logs/trace/final-report.md"
```

## 5. Runtime 修改

### 5.1 `work/runtime/agent_task_packet.py`

目标：任务包必须通用。

必须删除或替换：

```text
flashdb_root
```

建议数据结构：

```python
@dataclass
class SourceLayout:
    readme_path: Optional[Path]
    project_root: Optional[Path]
    src_dirs: List[Path]
    test_dirs: List[Path]

@dataclass
class MigrationContract:
    source_project_name: str
    source_language: str
    target_language: str
    output_project_name: str
    output_project_dir: Path
    source_dirs: List[str]
    test_dirs: List[str]
    build_commands: List[str]
    unsafe_ratio_max: float
    api_name_hints: List[str]
    module_hints: List[str]

@dataclass
class RuntimePaths:
    root_dir: Path
    work_dir: Path
    source_root: Path
    output_project_dir: Path
    trace_dir: Path
    migration_trace_dir: Path
    result_report: Path
    issue_summary: Path
```

字段来源优先级：

```text
1. SOURCE_ROOT README/READNE
2. work/code/README.md
3. active profile
4. framework defaults
```

### 5.2 `work/runtime/loopforge_runner.py`

目标：主链保留，命名通用化。

必须保留主链：

```text
self_check
create task packet
analyze_source
generate_project
run_repair_loop
evaluate_semantic_equivalence
verify_generated
finalize
write result
```

必须修改：

```text
REQUIRED_SKILL_FILES -> work/skills/c-to-rust-migration/SKILL.md
REQUIRED_ADAPTER_FILES -> work/rules/loopforge/adapters/c-to-rust/*.md
trace paths -> logs/trace/c-to-rust
output project -> packet.output_project_dir
verification working directory -> packet.output_project_dir
```

禁止硬编码：

```text
specific project name
specific output project name
specific API prefix
specific module names
specific business demo behavior
```

### 5.3 `work/runtime/c2rust_analysis.py`

文件名可以保留，因为它描述 C-to-Rust 能力类别；内部逻辑必须通用。

必须支持：

```text
.c/.h 扫描
include graph
function table
type table
macro table
public API extraction
test case extraction
assertion extraction
test-to-api candidate mapping
```

API 识别规则：

```text
1. 使用 packet.api_name_hints，若存在；
2. 使用 header declared functions；
3. 使用 non-static source functions；
4. 使用 tests referenced functions；
5. 不使用固定项目 API 前缀。
```

### 5.4 `work/runtime/c2rust_project_generator.py`

目标：改为 source-driven scaffold，不再生成固定业务 demo。

必须删除：

```text
fixed default API names
fixed KV demo
fixed Rust business struct
fixed BTreeMap behavior
fixed test file named after project
```

生成逻辑：

```text
Cargo.toml package name = normalized(packet.output_project_name)
src/lib.rs exports generated modules
src/types.rs generated from extracted structs/enums/typedefs
src/constants.rs generated from extracted macros where safe
src/modules/<normalized_c_file_stem>.rs generated from C source files
tests/source_migrated_tests.rs generated from extracted C test cases
```

如果无法完整语义迁移，必须在 generation payload 中写：

```json
{
  "generation_mode": "source_driven_scaffold",
  "full_semantic_translation": false,
  "semantic_equivalence_claim": "not_claimed"
}
```

### 5.5 `work/runtime/c2rust_repair.py`

目标：repair loop 通用，不关心具体项目。

最低能力：

```text
missing module file -> create module file
unresolved import/module -> fix mod/pub use when safe
duplicate export -> remove duplicate re-export when safe
missing Cargo.toml -> regenerate minimal Cargo.toml from packet
cargo build/test stderr -> write repair-rounds.md/json
type/borrow/test assertion failures -> generate repair task packet, not fake-fix
```

## 6. 说明文档修改

### 6.1 `INSTRUCTION.md`

标题改为：

```text
Source-README-driven C-to-Rust Migration Harness
```

描述原则：

```text
The harness derives source layout, output project name, build commands, test commands, and unsafe threshold from the source README/READNE or bundled task README. Framework assets must remain generic.
```

不要把当前题目项目名作为框架身份。

### 6.2 `README.md`

描述为：

```text
Generic source-readme-driven C-to-Rust migration harness for contest execution.
```

不要写成某个具体 C 项目的迁移器。

## 7. 运行结果要求

执行后必须生成：

```text
<runtime-derived-output-project>/Cargo.toml
<runtime-derived-output-project>/src/
<runtime-derived-output-project>/tests/
result/output.md
result/issues/00-summary.md
logs/trace/c-to-rust/
```

如果当前题面要求输出某个具体项目名，运行结果可以按题面生成该目录；但框架配置和源码不能写死该名字。

## 8. 禁止事项

禁止：

```text
框架文件名含具体项目名
skill/profile/adapter/subagent 名称含具体项目名
runtime 硬编码具体输出目录
runtime 硬编码具体 API 前缀
runtime 生成固定业务 demo 伪装迁移结果
只因 cargo test 通过就声明 semantic equivalence
提交本地绝对路径结果
向 SOURCE_ROOT 写入 .loopforge 或其他过程产物
```

