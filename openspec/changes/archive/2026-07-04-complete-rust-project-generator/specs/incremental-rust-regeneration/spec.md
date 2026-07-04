## ADDED Requirements

### Requirement: Compute an explicit incremental change boundary
系统 MUST 从已验证模块与调用边映射计算增量重新生成的允许变更闭包，该闭包 SHALL 仅包含请求的目标模块及迁移计划标识的直接依赖，并 MUST 在执行前记录闭包理由。

#### Scenario: Select one target module
- **WHEN** 调用方请求重新生成一个 Rust 模块
- **THEN** 增量计划列出目标、允许变化的直接依赖、闭包边证据和明确禁止变化的其余生成文件

#### Scenario: Target identity is unknown
- **WHEN** 请求的模块不存在于当前已验证实现映射或依赖图
- **THEN** 系统拒绝运行并报告未知目标，不扩大到完整工程或猜测匹配模块

### Requirement: Stage and validate incremental regeneration transactionally
系统 SHALL 在独立暂存目录重新生成允许闭包，MUST 对候选工程重新执行完整性、占位、unsafe 和 `cargo build --locked` 门禁，并 SHALL 仅在全部门禁通过后原子发布变化。

#### Scenario: Candidate regeneration passes all gates
- **WHEN** 暂存候选仅修改允许闭包且所有完整生成门禁通过
- **THEN** 系统原子发布候选文件，并保持工程和证据属于同一新生成运行

#### Scenario: Candidate regeneration fails validation
- **WHEN** 候选构建失败、出现不支持项或未满足任一完整生成门禁
- **THEN** 系统丢弃候选发布，保留原已验证工程并生成阻塞报告

### Requirement: Prove unrelated generated files remain unchanged
系统 MUST 在增量运行前后计算规范化生成树文件清单和内容哈希，并 SHALL 要求允许变更闭包之外的所有文件集合及哈希完全不变。

#### Scenario: Only the target closure changes
- **WHEN** 增量生成完成且所有变化文件均位于允许闭包
- **THEN** `incremental-regeneration-report.json` 记录前后哈希、变化集合、未变化集合和闭包核对通过结论

#### Scenario: An unrelated file changes
- **WHEN** 无依赖模块、清单外文件或其他禁止目标的内容哈希发生变化
- **THEN** 系统阻止发布并报告越界文件及其前后哈希

### Requirement: Make incremental regeneration deterministic and traceable
系统 SHALL 将每次增量运行绑定到父生成 run ID、目标、输入摘要、工具版本和允许闭包；对相同父工程及相同输入重复执行时，规范化候选内容和变化集合 MUST 一致。

#### Scenario: Repeat the same incremental request
- **WHEN** 使用相同父工程、目标、证据和工具版本重复增量生成
- **THEN** 除明确标注的运行元数据外，候选文件内容、变化集合和闭包验证结果完全一致

#### Scenario: Parent project changed since planning
- **WHEN** 执行时当前工程摘要与增量计划绑定的父生成摘要不一致
- **THEN** 系统拒绝使用陈旧计划并要求重新计算变更闭包
