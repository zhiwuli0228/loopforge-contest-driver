## Context

竞赛运行时会注入只读源码，并预加载唯一题目设计文档。提交包不得携带目标项目的预分析结论或人工编写领域配置。profile 即使与核心算法分离，只要预置了目标项目 capability、API 角色、revision 或平台端口，仍然构成输入泄漏。

```text
runtime source analysis       runtime preloaded design evidence
           |                              |
           +--------------+---------------+
                          v
               generic semantic obligations
        signatures / results / effects / resources /
        call edges / external boundaries / invariants
                          |
                          v
                  generic Rust plan
```

## Goals / Non-Goals

**Goals:**

- 核心运行包对任意 C 项目使用同一算法和 schema。
- 所有结论可反向引用当次运行的源码或设计 evidence。
- 保持公开 API、类型、共享状态和调用边完整分母。
- 仅从结构事实生成模块和外部边界，不使用项目名称或 API 名称分类。
- 对不能静态证明的业务语义建立保持源码行为的义务，不伪造具体领域结论。

**Non-Goals:**

- 不在提交包中维护任何目标项目 profile、revision、capability 或黄金语义模型。
- 不声称静态规划本身已经证明业务等价；最终证明由生成后测试和语义审计完成。
- 不通过函数名猜测读写、持久化、恢复或错误语义。

## Decisions

### 1. 只接受运行时证据，不接受 bundled project knowledge

规划器只消费通过门禁且身份一致的分析 evidence。题目设计证据若参与规划，必须来自当次预加载文件及其 digest；仓库内不得存在目标项目专属 profile 或默认路径。

### 2. semantic IR 只表达可证明事实与保持义务

每个公开 API 生成签名、source result space、source-observable effect 和前后置保持义务。共享状态来自 global-state map；调用不在内部定义集合中时形成 external boundary；类型和函数指针来自 type map。IR 不包含固定 capability 枚举。

### 3. 模块与端口由结构关系产生

目标模块默认沿用定义文件身份。调用边若目标在项目内部，则规划为 module call；若目标无法解析为内部定义，则形成证据化 external port。禁止固定生成 storage、flash、clock 或 lock。

### 4. 保守而不猜测

规划器不把名称包含 `set`、`get`、`kv`、`ts` 等视为语义证据。它为每个 API 建立“保持全部源码可观察 effect/result”的义务，使后续生成器和验证器不能省略行为，但不补造具体业务状态。

### 5. 独立重算完整性分母

验证器重新计算 API、类型/字段、共享状态和调用边集合，要求 contract、mapping 和 implementation obligation 100% 覆盖。每个 port 必须关联 source-derived boundary；所有文档共享 planning run、analysis run、source digest、IR digest 和 input digest。

### 6. 测试数据必须领域中立

单元测试使用最小 counter/container 等通用 C fixture，仅验证结构与证据规则。禁止在 runtime 或 fixture 中保存目标项目 API、revision、capability、错误码或端口清单。

## Risks / Trade-offs

- [静态计划较抽象] → 明确保留 source-observable obligations，具体等价由生成后差分测试和语义审计验证。
- [外部调用可能误分类] → fail closed 保留边证据，下游可以基于更完整定义表纠正，不能按名称白名单。
- [题目设计包含项目名称] → 允许运行时读取，因为它是比赛输入；不得将其内容复制为提交包常量。

## Migration Plan

1. 删除 bundled profile、默认 profile 接线和 profile metadata。
2. 将 semantic planner 改为纯 analysis-evidence 驱动。
3. 从定义位置、类型、全局状态和调用图生成通用 IR 与 Rust plan。
4. 更新下游 schema、runner、文档和负向测试。
5. 扫描 runtime 与 fixtures，确保不存在目标项目知识泄漏。
