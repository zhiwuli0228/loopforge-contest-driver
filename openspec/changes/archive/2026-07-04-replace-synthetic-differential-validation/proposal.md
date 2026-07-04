## Why

现有测试迁移门禁会用合成观测同时代表 C 与 Rust 结果、默认宣称全部 mutation 已检出，并把全部语义不变量绑定到首个断言或向量，因此能够在没有真实语义验证时产生 `PASSED`。同时 Windows E2E 仅凭 Cargo 成功直接写入 `READY_FOR_EVALUATION`，与 runner 的最终语义门禁和 Linux 行为不一致，无法满足 `work/design/README.md` 的语义等价与稳定生成要求。

## What Changes

- **BREAKING**：删除合成 C/Rust 观测和默认 mutation 检出行为；缺少独立执行证据时必须 fail closed。
- 引入真实、隔离且确定性的 C Oracle 与 Rust rewrite 执行协议，保存命令、环境、输入、日志和规范化观测。
- 实际注入固定 mutation 并重新运行关联测试或差分向量，只有可追溯失败证据才能标记 mutation 被检出。
- 建立唯一 canonical evidence manifest，统一源测试、源断言、API 和语义不变量分母及摘要。
- 要求语义不变量通过稳定 ID 关联到实际执行的断言或差分比较，不允许批量绑定占位覆盖。
- 统一 runner、Windows E2E 和 Linux 验收的最终状态计算，禁止包装脚本自行声明成功。
- 统一 Windows/Linux 生成修复策略，并用独立工作区连续运行验证规范化产物可重复、源目录不变。

## Capabilities

### New Capabilities

- `real-differential-execution`: 定义真实 C/Rust 隔离执行、规范化观测、差分比较和 mutation 检出证据的不可真空通过契约。
- `canonical-semantic-evidence`: 定义跨分析、规划、生成、测试迁移和最终语义审计共享的唯一分母、ID 关联和证据身份。
- `cross-platform-final-verdict`: 定义 Windows/Linux 使用同一最终门禁、生成策略和可重复性判定的契约。

### Modified Capabilities

无。现有相关能力尚未归档为基线 spec，本变更以纠偏能力明确替代其合成实现。

## Impact

- 影响 `work/runtime/test_migration_validation.py`、语义规划/审计、runner 最终状态汇总、生成修复 provider 配置及 Windows/Linux 包装脚本。
- 差分验证需要可构建的 C Oracle 适配产物、隔离临时目录和结构化观测协议。
- 现有仅依赖结构或合成数据的测试必须改写；旧报告 schema 需要版本升级并拒绝作为成功证据。
- 修复完成前，当前 change 不应归档，也不得声明 `READY_FOR_EVALUATION`。
