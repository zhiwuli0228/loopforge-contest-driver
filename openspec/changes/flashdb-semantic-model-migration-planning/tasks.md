## 1. 清除定制知识

- [x] 1.1 删除 bundled target-project profile、默认 profile 路径、固定 revision 和 profile metadata
- [x] 1.2 删除固定 capability、目标项目错误码、端口清单和 API 名称启发式
- [x] 1.3 增加 runtime/fixture 扫描测试，拒绝目标项目知识泄漏
- [x] 1.4 将旧 v1 和 profile 驱动 v2 schema 标记为必须重新规划

## 2. 通用 semantic IR

- [x] 2.1 仅从一致且验证通过的运行时 analysis evidence 加载输入
- [x] 2.2 为全部公开 API 生成签名、source result、source-observable effect 和 transition obligation
- [x] 2.3 从 global-state map 生成 resource，从 type map 生成类型和函数指针事实
- [x] 2.4 为每项结论记录 source-derived derivation kind 和非空 evidence IDs
- [x] 2.5 验证相同输入的规范化 IR 确定性

## 3. 通用 Rust migration plan

- [x] 3.1 完整映射核心类型、字段和共享状态，不注入项目默认所有权模型
- [x] 3.2 由 API 定义文件确定目标模块，禁止按 API 名称分类
- [x] 3.3 由内部定义集合和调用边确定 module call 与 external boundary
- [x] 3.4 只为 source-derived external boundary 生成 port
- [x] 3.5 为全部公开 API 生成 contract/effect/result/module/boundary 完整实现义务

## 4. Fail-closed 验证与接线

- [x] 4.1 独立重算公开 API、类型/字段、共享状态和调用边分母
- [x] 4.2 检测无 source evidence 结论、缺失 obligation 和伪造 port
- [x] 4.3 原子发布 v3 evidence 并绑定 analysis/source/IR/input identity
- [x] 4.4 更新 Rust generation 和 runner，移除 profile identity 与专属文件依赖
- [x] 4.5 使用领域中立 C fixture 验证规划成功且无领域泄漏
- [x] 4.6 更新运行时与下游消费文档并执行全量回归
