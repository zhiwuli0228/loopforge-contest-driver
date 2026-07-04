## ADDED Requirements

### Requirement: Independently scan critical source sets
系统 SHALL 使用不复用主分析器抽取逻辑的独立扫描器发现核心源文件、公开 API 声明候选和源测试，并 SHALL 将结果写入 `independent-source-scan.json`。

#### Scenario: Independent scan of a resolved C project
- **WHEN** 主分析和独立扫描针对同一输入根与范围配置执行
- **THEN** 独立证据包含核心源文件、公开 API 候选和源测试的非空集合及各自来源位置

### Requirement: Cross-check analyzer completeness
验证器 MUST 比较主分析器与独立扫描器的核心源文件、公开 API 和源测试集合；只有集合一致或每项差异均具有可验证分类证据时才可通过该检查。

#### Scenario: Both scanners agree
- **WHEN** 两种扫描得到相同的规范化核心源文件、公开 API 和源测试集合
- **THEN** `analysis-verification.json` 将三个集合一致性检查标记为通过

#### Scenario: Main analyzer misses a public API
- **WHEN** 独立扫描发现一个具有公开头文件证据但主分析结果中不存在的 API
- **THEN** 验证状态为 `BLOCKED_WITH_REPORT`，并记录缺失 API、双方证据和首个阻塞点

#### Scenario: Difference is explicitly classified
- **WHEN** 两种扫描存在集合差异且差异被声明为配置排除或独立扫描误报
- **THEN** 验证器仅在分类包含匹配的源码证据、规则标识和非空原因时接受该差异

### Requirement: Enforce non-vacuous completeness gates
验证器 MUST 要求 `source_file_count > 0`、`public_api_count > 0` 和 `source_test_count > 0`，并 MUST 要求核心源文件覆盖率、公开 API 声明/定义/证据覆盖率以及核心类型成员建模覆盖率均为 100%。计算覆盖率时不得从分母中静默移除缺失项。

#### Scenario: A required count is zero
- **WHEN** 核心源文件、公开 API 或源测试任一计数为零
- **THEN** 验证状态为 `BLOCKED_WITH_REPORT`，且不得进入代码生成

#### Scenario: One core structure field is missing
- **WHEN** 独立证据或 AST 表明核心结构体含有一个未出现在类型模型中的字段
- **THEN** 类型成员覆盖检查失败并报告缺失字段的源码位置

### Requirement: Reject unresolved core analysis failures
验证器 MUST 拒绝任何未解释的悬空符号、核心函数或核心类型解析失败，以及缺少声明、定义或源码证据的公开 API。

#### Scenario: Public declaration has no definition
- **WHEN** 公开 API 声明无法关联到定义且不存在经过验证的外部实现分类
- **THEN** 验证状态为 `BLOCKED_WITH_REPORT` 并列出该悬空符号

#### Scenario: Function pointer signature is incomplete
- **WHEN** 核心函数指针的参数或返回类型无法解析
- **THEN** 验证器将该核心类型标记为不完整并阻止后续阶段

### Requirement: Publish a coherent verification result
系统 SHALL 生成 `analysis-verification.json`，其中包含统一运行标识、每项门禁的输入计数和结论、全部阻塞原因以及总体状态；验证器 MUST 拒绝运行标识不一致、schema 无效、引用路径不存在或混用旧运行产物的证据包。

#### Scenario: All gates pass with coherent evidence
- **WHEN** 八类证据来自同一运行、通过 schema 校验且全部完整性门禁通过
- **THEN** 分析验证状态为通过，并允许流水线进入语义建模与迁移规划阶段

#### Scenario: Evidence comes from mixed runs
- **WHEN** 任一必需证据文件的运行标识与其他文件不一致
- **THEN** 总体状态为 `BLOCKED_WITH_REPORT`，并指出不一致的文件
