## Why

完整 Rust 工程生成后，仍不能证明迁移结果与 C 原实现语义等价；现有简单 fixture、恒真断言或只看 `cargo test` 退出码都可能形成比赛验收中的伪通过。需要把原始测试场景迁移为有效 Rust 测试，并用 C 原实现作为 Oracle 对同一输入和初始存储状态执行差分验证，同时确保验证框架不包含任何面向 FlashDB 的定制特判。

## What Changes

- 从已验证的源码测试清单、行为契约、语义不变量和 Rust 实现映射生成源测试到 Rust 测试的完整映射，要求每个源断言都有有效 Rust 断言或机器可审计的等价覆盖。
- 构建项目无关的 C/Rust 差分验证 harness，对返回值、错误、状态、遍历顺序、持久化重开、容量边界、失败恢复和 GC 前后可见状态进行确定性比较。
- 引入固定随机种子的状态机差分测试、语义不变量测试映射和 mutation testing，证明测试可以识别关键语义错误。
- 强制扫描并拒绝恒真、自比较、全匹配断言、空测试、只检查构建成功的测试，以及任何通过项目名、领域名、文件名或符号前缀识别 FlashDB 的定制逻辑。
- 生成 `source-test-map.json`、`differential-test-vectors.json`、`differential-test-report.json`、`semantic-invariant-test-map.json`、`mutation-test-report.json` 和 `cargo-test.log`，并在证据缺失或不一致时输出 `BLOCKED_WITH_REPORT`。
- 只在 Change 1/2/3 的同一证据链全部通过且 Rust 工程门禁通过后运行；本变更不负责修复编译或语义失败，失败将交给后续自愈闭环。

## Capabilities

### New Capabilities

- `source-test-migration`: 将原始 C 测试场景、断言和语义不变量迁移或等价覆盖为有效 Rust 测试，并证明覆盖分母不可被缩小。
- `differential-validation`: 使用项目无关 harness 对 C 原实现与 Rust 重写执行同输入、同初始状态的差分验证、状态机测试和 mutation testing。

### Modified Capabilities

无。

## Impact

- 影响 runner 中完整工程生成之后、编译/语义自愈之前的验证阶段，以及 `work/runtime/` 中测试迁移器、差分 harness、测试有效性扫描器、mutation runner 和证据发布逻辑。
- 新增对原始 C 工程测试入口、生成 Rust 工程、存储后端 fixture、C Oracle 构建产物和 Cargo 测试日志的统一运行身份绑定。
- 后续 Change 5 必须消费本变更的失败报告、差分向量、mutation 结果和测试日志；本变更通过前不得声明 `READY_FOR_EVALUATION`。
