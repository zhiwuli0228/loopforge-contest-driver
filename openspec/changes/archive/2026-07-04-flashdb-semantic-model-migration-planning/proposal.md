## Why

源码事实需要转换为可供 Rust 生成和验证消费的语义义务，但竞赛提交包不能预置任何目标项目知识。此前把 FlashDB 知识放入 acceptance profile，仍然泄漏了目标项目的 capability、错误、端口、revision 和场景，属于定制实现而非通用 Harness。

本变更将语义规划重构为完全由当次运行证据驱动的通用能力。提交包只包含领域中立算法；目标项目名称、API、模块、错误码、状态、端口和验收场景只能来自只读源码分析证据及比赛预加载设计证据，不能来自仓库内 profile、常量表、名称启发式或默认值。

## What Changes

- 建立项目无关 semantic IR，表达源码签名、结果空间、可观察 effect、状态资源、调用边、外部边界和迁移义务。
- 删除所有 bundled project profile、默认 profile 路径、固定 revision 和目标领域 fixture。
- 模块由源码定义位置与关系图确定；外部端口仅由未在项目内定义的调用边或函数指针边界确定。
- 禁止按名称猜测 capability、错误、模块或端口，也禁止补造目标项目业务语义。
- 无法由运行时证据证明的业务结论不写入 IR；计划只建立“保持源码可观察行为”的验证义务，由后续差分测试和语义审计证明。
- 使用领域中立的最小 C fixture 验证算法，不在测试数据中编码竞赛目标项目知识。

## Capabilities

### New Capabilities

- `semantic-migration-modeling`: 从已验证源码事实构建领域中立、可追溯的 semantic IR。
- `rust-migration-planning`: 从 semantic IR 生成类型、所有权、模块、外部边界和实现/验证义务。

### Modified Capabilities

无。

## Impact

- `work/runtime/semantic_planning.py` 不再加载项目 profile，schema 升级为 `semantic-migration-planning/v3`。
- 删除 `work/runtime/profiles/flashdb-acceptance.json` 及所有默认接线。
- 下游 Rust generation 只绑定 analysis run、source digest、semantic IR digest 和 planning run，不再包含 profile identity。
- 旧的 FlashDB 专属 v1 和 profile 驱动 v2 evidence 必须重新规划。
