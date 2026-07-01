## ADDED Requirements

### Requirement: Discover the complete resolved C source scope
系统 SHALL 从布局解析结果发现全部核心 C 源文件、公开头文件和源测试文件，并 SHALL 记录实际采用的范围。系统 MUST NOT 根据项目名选择范围规则。

#### Scenario: Analyze a resolved C layout
- **WHEN** `SOURCE_ROOT` 指向具有非空源码和测试目录的 C 工程
- **THEN** `source-inventory.json` 列出每个核心源文件、公开头文件和源测试文件的项目相对路径、类别与内容摘要

#### Scenario: Analyze an equivalent configured layout
- **WHEN** C 源码使用布局解析器发现的等价目录布局
- **THEN** 系统按该配置发现文件，并在清单中记录所采用的布局映射

### Requirement: Parse C language and preprocessing constructs
系统 MUST 使用能够建模预处理记录和 C 语法树的分析前端解析头文件、实现文件、宏、条件编译、`typedef`、结构体、联合体、枚举和函数指针，并 SHALL 保留有效编译参数和源码证据。

#### Scenario: Parse a function pointer nested in a structure
- **WHEN** 核心头文件通过 `typedef` 在结构体字段中声明函数指针
- **THEN** `type-map.json` 包含别名、结构体字段、函数参数及返回类型之间的完整关系和声明位置

#### Scenario: Parse conditional declarations
- **WHEN** 公开 API 或核心类型只在某个受支持的预处理配置下可见
- **THEN** `preprocessor-variants.json` 标识该配置的宏和 include 参数，相关 API 或类型证据关联到该变体

#### Scenario: Core translation unit cannot be parsed
- **WHEN** 任一核心翻译单元因缺失 include、宏配置或语法前端错误而无法解析
- **THEN** 分析结果记录确定的失败位置和原因，且不得将该翻译单元标记为已覆盖

### Requirement: Model cross-file symbols and relationships
系统 SHALL 建立符号声明与定义关系、include 图、函数调用图、类型依赖图以及共享全局状态的读写关系，并 MUST 对每个公开 API 给出声明、定义和源码证据位置。

#### Scenario: Public API declaration and definition are in different files
- **WHEN** 公开 API 在 `inc` 头文件声明并在 `src` 实现文件定义
- **THEN** `public-api-map.json` 将两个位置关联为同一稳定符号，`call-graph.json` 包含该定义可解析的调用边

#### Scenario: Shared state is accessed across modules
- **WHEN** 多个核心函数读取或修改同一全局或静态存储状态
- **THEN** `global-state-map.json` 列出状态定义以及每个读取和写入访问的函数与源码位置

### Requirement: Produce deterministic analysis evidence
系统 SHALL 为每次分析生成 `source-inventory.json`、`public-api-map.json`、`type-map.json`、`call-graph.json`、`global-state-map.json` 和 `preprocessor-variants.json`；所有文件 MUST 包含一致的运行标识、schema 版本、输入摘要，并 SHALL 使用稳定排序和项目相对路径。

#### Scenario: Repeat analysis without source changes
- **WHEN** 使用相同工具版本、配置和未变化的 C 源码连续执行两次分析
- **THEN** 除明确标注的运行元数据外，六类规范化分析内容完全一致

### Requirement: Preserve the source tree
分析过程 MUST 将 C 项目输入视为只读，且不得创建、修改、删除或改变输入树内文件的权限。

#### Scenario: Complete a source analysis run
- **WHEN** 分析器对任意 C 工程完成成功或阻塞运行
- **THEN** 运行前后的输入文件集合、内容摘要和权限保持一致
