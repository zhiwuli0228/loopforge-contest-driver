# V2 Design Blueprint: Agent-First C-to-Rust Migration

## Core Architecture

```
Agent = 全部判断（理解、设计、生成、门禁）
Python = 纯工具（解析、执行、报告）
OpenSpec = Agent 的思考框架
SuperSpec = 执行阶段定义
SuperPower = 权限边界
```

## 核心决策

| # | 决策 | 理由 |
|---|------|------|
| 1 | Agent-First | Agent 做所有判断，Python 不做任何 pass/fail |
| 2 | OpenSpec-Driven | proposal → design → specs → tasks 作为思考框架 |
| 3 | 模块级 Spec | 函数级会导致功能紊乱，模块级保证能力一致性 |
| 4 | SuperPower 必须 | 标准化 plan → 标准化 subagent → 可验证结果 |
| 5 | CLI 统一入口 | tools.py 作为唯一 Python 入口，所有 coding tool 通过 Bash 调用 |
| 6 | 干净版本 | 不保留 legacy 模块，不做兜底，不混搭 |
| 7 | 仅 Linux | WSL Ubuntu 验证，不考虑 Windows |

## 数据流

```
Phase 0: Preflight
  Python: tools.py self-check → 文件存在性数据
  Agent: 判断是否可以继续

Phase 1: Understand (OpenSpec: proposal)
  Python: tools.py parse-source → source-inventory.json
  Agent: 读源码 + 参考 JSON → proposal.md

Phase 2: Design (OpenSpec: design)
  Agent: 基于 proposal + source analysis → design.md

Phase 3: Spec (OpenSpec: specs, per module)
  Agent: 基于 design + 源码 → specs/<module>/spec.md

Phase 4: Plan (OpenSpec: tasks)
  Agent: 基于 design + specs + SuperPower → tasks.md

Phase 5: Implement (Subagent per batch)
  Subagent: 读 spec + 源码 → 写 Rust → cargo build
  Python: tools.py run-verification → cargo 结果数据
  Agent: 判断 build 结果

Phase 6: Test (Subagent per batch)
  Subagent: 读 spec → 写测试 → cargo test
  Python: tools.py run-verification → cargo test 数据
  Agent: 判断 test 结果

Phase 7: Repair Loop (Agent 驱动)
  Agent: 读 cargo 错误 → 诊断 → 修复 → 重试
  Python: tools.py run-verification → cargo 结果数据

Phase 8: Semantic Audit (Agent 驱动)
  Agent: 读 spec 中的不变量 → 写不变性测试 → 运行
  Python: tools.py run-verification → cargo test 数据

Phase 9: Quality Gates
  Python: tools.py check-unsafe → 比例数据
  Python: tools.py fault-injection → 注入结果数据
  Python: tools.py neutrality-audit → 扫描数据
  Agent: 综合判断门禁

Phase 10: Finalize
  Agent: 汇总 → result/output.md, issues/00-summary.md
```

## 文件结构

```
work/
├── runtime/
│   └── tools.py                          ← CLI 入口（新建）
├── profiles/
│   ├── superpower/
│   │   └── c-to-rust-migration-guards.yaml  ← 权限边界（新建）
│   └── superspec/
│       └── c-to-rust-migration-stages.yaml  ← 阶段定义（新建）
├── skills/
│   └── c-to-rust-migration-v2/
│       └── SKILL.md                      ← 编排 prompt（新建）
├── subagent/
│   ├── c2r-00-preflight.md
│   ├── c2r-01-understand.md
│   ├── c2r-02-design.md
│   ├── c2r-03-spec.md
│   ├── c2r-04-plan.md
│   ├── c2r-05-implement.md
│   ├── c2r-06-test.md
│   ├── c2r-07-repair.md
│   ├── c2r-08-semantic-audit.md
│   ├── c2r-09-quality-gates.md
│   └── c2r-10-finalize.md
├── migration-openspec/                   ← 运行时 artifacts（运行时生成）
└── docs/
    └── V2-DESIGN-BLUEPRINT.md            ← 本文档
```

## Python tools.py 命令

```bash
# 数据解析（返回原始数据，不做判断）
python tools.py parse-source --source-root /path --work-dir work

# 验证执行（只跑命令，返回结果）
python tools.py run-verification --project-dir /path --commands '["cargo build --locked"]'

# 数值计算（返回数据）
python tools.py check-unsafe --project-dir /path

# 故障注入（执行测试，返回数据）
python tools.py fault-injection --trace-dir /path

# 中立性审计（扫描文件，返回数据）
python tools.py neutrality-audit --paths '[...]' --forbidden-terms '[...]'

# 报告写入（格式化输出）
python tools.py write-report --result-dir result --data '...'
```

## Subagent 上下文控制

每个 subagent：
- 注入 prompt ~2K tokens（SuperPower 规则 + 任务描述 + 文件路径）
- 自己读取需要的内容（按需 Read）
- 返回 ~500 tokens（结果摘要）
- 总上下文 ~5-8K tokens

## Change 划分

| Change | 内容 | 依赖 |
|--------|------|------|
| 1 | Python Tools Layer | 无 |
| 2 | Execution Framework (SuperPower + SuperSpec) | Change 1 |
| 3 | Agent Orchestration (SKILL.md + subagents) | Change 1 + 2 |

## 约束

- 零项目定制，零硬编码（比赛要求，定制即淘汰）
- Python 不做任何判断
- 所有门禁由 agent 综合判断
- 文件交接为唯一跨阶段通信方式
- 每个 subagent 上下文有界
