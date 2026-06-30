# INSTRUCTION.md

This file is the execution guide for judges, platform Agents, opencode, and human reproducers.

It explains how to prepare the environment, install dependencies, provide the source path, run the tool, and collect results.

It does not contain business-specific task data or implementation strategy.

## 1. Runtime Requirements

Required:

- Linux with `bash`, or Windows with PowerShell for local development
- Python 3.11+
- `pip`
- `git`
- Rust toolchain when the downstream workflow needs Rust build or test validation

Check commands:

```bash
python3 --version
python3 -m pip --version
bash --version
git --version
```

For Rust-related validation:

```bash
cargo --version
rustc --version
```

## 2. Python Environment Setup

Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r work/requirements.txt
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r work\requirements.txt
```

If `work/requirements.txt` is effectively empty, no third-party Python dependency is required.

## 3. Source Path Input

The tool requires a source project path.

The Agent should resolve the source path in this order:

1. Use the source path explicitly provided by the contest platform.
2. If the user instruction contains a natural-language source path, extract that path.
3. If `--source-root` is provided, use it.
4. If `SOURCE_ROOT` is set, use it.
5. On Linux, fall back to `/__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB`.
6. On Windows or local development, fall back to `code`.

When the source path is resolved, pass it to the tool as `SOURCE_ROOT`.

Natural-language path examples the Agent should normalize before execution:

- `源码在 /workspace/input/FlashDB。`
- `请使用 /mnt/data/FlashDB 作为源码路径。`
- `The source project is located at /contest/source/FlashDB.`
- `源码路径是 D:\contest\FlashDB。`
- `本地测试时源码放在 ./code。`

## 4. Run the Tool

Linux:

```bash
SOURCE_ROOT="<resolved-source-path>" bash work/scripts/run.sh
```

Example:

```bash
SOURCE_ROOT="/workspace/input/FlashDB" bash work/scripts/run.sh
```

Windows PowerShell:

```powershell
$env:SOURCE_ROOT = "<resolved-source-path>"
powershell -ExecutionPolicy Bypass -File work\scripts\run.ps1
```

Example:

```powershell
$env:SOURCE_ROOT = "code"
powershell -ExecutionPolicy Bypass -File work\scripts\run.ps1
```

## 5. Result Retrieval

After execution, read:

```text
result/output.md
```

If issues are produced, read:

```text
result/issues/00-summary.md
```

Logs are stored in:

```text
logs/trace/
```

Human interaction records are stored in:

```text
logs/interaction.md
```

If execution is fully unattended, `logs/interaction.md` may remain unchanged except for the automatic header.

## 6. Failure Handling

If execution fails, collect and report:

- dependency installation result
- resolved `SOURCE_ROOT`
- executed command
- failed stage
- relevant log file path
- whether partial result exists

If delegated execution cannot continue because the required subagent layer is unavailable, stop with `BLOCKED_WITH_REPORT` and record the reason as `required subagent unavailable`.

Do not modify platform-provided source materials during failure handling.
