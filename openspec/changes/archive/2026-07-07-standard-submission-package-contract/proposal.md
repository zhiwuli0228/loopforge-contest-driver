## Why

当前仓库的默认输入模型仍然是 `work/design/README.md + SOURCE_ROOT`，这会把系统推向“尽量适配任意目标项目结构”。后续如果要把比赛题格式提升为统一标准，就必须反过来收紧契约: 平台只接受标准提交包，目标项目按标准包布局接入，校验和修复流程都围绕这个固定结构运行。

## What Changes

- 引入标准提交包输入契约，以 `SUBMISSION_ROOT` 作为唯一外部输入根，并要求固定包含 `README.md`、`design-docs/`、`code/`，以及可选或必选的 `test-cases/` 与元数据文件。
- 将设计输入真相源从仓库内置 `work/design/README.md` 调整为标准提交包中的比赛说明和设计目录，明确 `README.md` 负责比赛规则、冻结契约、验证命令，`design-docs/` 负责业务设计细节。
- 将实现与修复边界从“读写整个 `SOURCE_ROOT`”调整为“只允许分析标准包、只允许修改 `code/`”，并禁止修改 `design-docs/`、`test-cases/`、`README.md` 等验收基线。
- 将验证模型从“按语言或框架自动猜测命令”调整为“优先执行标准提交包声明的构建与黑盒验证命令”，自动探测只作为降级路径。
- 更新阶段、适配器与运行时契约，使其围绕标准提交包目录而不是任意源代码根工作。

## Capabilities

### New Capabilities
- `consistency-submission-package-contract`: 定义标准提交包目录、必需文件、只读/可写边界，以及比赛说明、设计文档、业务代码、黑盒测试之间的职责分工。

### Modified Capabilities
- `consistency-execution-contracts`: 将默认外部输入从 `SOURCE_ROOT` 调整为 `SUBMISSION_ROOT`，并要求执行契约围绕标准包固定子目录解析设计、代码与验证输入。
- `consistency-language-adapters`: 将适配器输入边界调整为标准包中的 `code/`，避免适配器直接面向任意仓库根做自由扫描。
- `consistency-stage-packages`: 调整 preflight、design intake、source inventory、repair planning 等阶段的输入输出边界，使其显式处理 `README.md`、`design-docs/`、`code/`、`test-cases/`。
- `consistency-runtime-reporting`: 调整 runtime 命令输入与验证命令来源，要求围绕标准提交包执行并在报告中体现标准包范围与验证基线。

## Impact

- 影响仓库输入模型、运行入口、阶段契约、适配器扫描边界与验证流程。
- 影响 `work/loopforge.config.yaml`、技能契约、profiles、superspec、guards、runtime 命令和报告范围。
- 会改变后续受控修复的写入边界: 允许写 `code/`，继续禁止修改设计基线和黑盒测试基线。
- 不直接要求本次变更实现全部修复能力，但会为后续 repair-enabled 模式提供稳定的标准包基础。
