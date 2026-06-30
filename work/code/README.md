# 比赛说明文档

`work/code/README.md` 是仓库内保存的题面说明，不是 `SOURCE_ROOT`，也不是 FlashDB 源码目录。

# 题目名称

将FlashDB用Rust重写



# 题目背景

对于成熟的高性能库内存问题依然会时常出现，使用Rust编译时内存管理可大幅度减少内存问题。

因此，为该场景提供可服用的工程能力意义重大。

本题目选择了一个开源C/C++作为重构的样本，请选手设计合理的Harness工程，完成要求



# 解题要求

1. 跨文件深度关联性上下文管理：在不破坏项目各模块调用关系的前提下，实现单点渐进式重构，
2.  编译/编译自愈双向闭环：当遇到重构后库API更新带来的各种语法不兼容是，Agent需要能根据错误栈（Error Stack）进行精准自愈、自行打补丁
3. 语义等价性保证：要求重构升级后的业务逻辑100%不受破坏，且生成覆盖全部主路径的单元测试



# 交付件要求

1. 重构后的项目目录名称使用flashDB_rust，也可以按Rust构建成可执行文件
2. 测试用例也用Rust以及Rust主流测试框架

# 验证用例

1. `.code/FlashDB/src` 全部转换为Rust，并且编译通过
2. `.code/FlashDB/tests` 单元测试项完成重构，全部通过构建并测试执行成功
3. Rust unsafe比例小于10%







1. FlashDB源码是放在一个指定的地方，需要我们指定路径去读，
 2. FlashDB源码重点关注FlashDB/src，原始C代码，需要重写为Rust,FlashDB/tests，原始C测试，需要迁移或等价覆盖；
3. 参赛作品执行完成后，应生成Rust重写项目：项目名：flashDB_rust，目录下包含 Cargo.toml,scr,tests, 要求如下：
a. flashDB_rust应为可构建的RUST项目，
b.项目根目录应该包含Cargo.toml
c.FlashDB/src 中核心逻辑应转换为Rust实现
d.FlashDB/tests中测试场景迁移为Rust测试，或通过兼容方式等价覆盖
e. 项目应该能够执行 cargo build和cargo test
5. unsafe 使用比例应低于10%

建议同时生成执行说明报告：
result/output.md
result/issues/00-summary.md
用于说明转换过程、最终Rust项目位置、测试迁移情况、已知问题和严重结果
