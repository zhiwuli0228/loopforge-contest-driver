## Why

已验证的源码事实和语义迁移计划仍不能证明系统能够产出真实可用的 Rust 重写；当前生成结果可能遗漏核心函数、破坏模块调用关系，或用占位逻辑形成表面可编译的伪实现。需要建立与具体题目无关、fail-closed 的完整工程生成能力，使每个公开 API、核心函数和调用边都有可追溯实现，并为后续测试迁移提供稳定目标。

## What Changes

- 从通过 Change 1、Change 2 门禁且运行身份一致的分析与语义规划证据生成完整 Cargo 工程，工程名和模块树仅由输入证据确定。
- 按迁移计划中的真实模块职责实现公共 API、状态所有权和外部端口，保留核心模块关系与调用语义，不识别或硬编码项目名、领域名及符号前缀。
- 生成 C 函数、公开 API、模块和核心调用边到 Rust 实现的完整映射；函数级生成问题不中断主生成流程，而是记录诊断、在最终阶段统一执行一次项目无关修复尝试，仍未解决时进入最终报告，禁止 `todo!()`、`unimplemented!()`、恒定返回值或空函数伪实现。
- 强制执行 `cargo build --locked`、`unsafe` 比例严格低于 10% 及逐处必要性说明，并发布可审计构建证据。
- 支持以目标模块为边界的单点渐进式重新生成，只允许更新目标及直接依赖范围，并证明无依赖模块文件哈希不变。

## Capabilities

### New Capabilities

- `rust-project-generation`: 从已验证的源码与语义规划证据生成完整、可构建、无不支持核心函数的 Rust Cargo 工程，并验证实现映射和安全约束。
- `incremental-rust-regeneration`: 受控地重新生成目标 Rust 模块及其直接依赖范围，以文件清单和前后哈希证明无关模块未发生变化。

### Modified Capabilities

无。

## Impact

- 主要影响语义规划之后、测试迁移之前的生成阶段，以及 `work/runtime/` 中的 Rust 工程生成器、完整性验证器和 runner 接线。
- 生成或重建运行时契约指定的 `work/output/<project>`，新增 `implementation-map.json`、`unsupported-functions.json`、`module-edge-map.json`、`incremental-regeneration-report.json`、构建日志和 `unsafe` 审计证据。
- Change 4 必须消费本变更验证通过的工程与稳定实现 ID；生成、构建、映射、占位扫描或安全门禁任一失败时统一输出 `BLOCKED_WITH_REPORT`。
