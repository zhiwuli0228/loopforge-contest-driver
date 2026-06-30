# Contest Execution Instruction

This repository is a contest driver. The only required external input is the source tree root, exposed as `SOURCE_ROOT`.

## Environment

Supported execution environments:

- Linux with `bash`
- Windows with PowerShell

Required tools:

- Python 3
- `pip`
- `git`
- Rust toolchain with `cargo`

Optional virtual environment setup:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r work/requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install -r work/requirements.txt
```

## Source Root Protocol

Source path resolution priority:

1. Contest platform explicit source path
2. `--source-root <path>`
3. `SOURCE_ROOT`
4. Path extracted by the agent from natural-language task input and normalized into `SOURCE_ROOT`
5. Linux fallback: `/__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB`
6. Local fallback: `code`

The framework reads requirements and constraints from the source README near `SOURCE_ROOT`. Supported names:

- `${SOURCE_ROOT}/README.md`
- `${SOURCE_ROOT}/README`
- `${SOURCE_ROOT}/readme.md`
- `${SOURCE_ROOT}/Readme.md`

If multiple files exist, the runner records the selected README path in the run trace.

## Run

Linux:

```bash
SOURCE_ROOT=<path> bash work/scripts/run.sh
```

Windows PowerShell:

```powershell
$env:SOURCE_ROOT="<path>"
powershell -ExecutionPolicy Bypass -File work/scripts/run.ps1
```

If no explicit source path is provided, the scripts first try `/__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB` on Linux and otherwise fall back to `code`.

## Results

Primary evaluator output:

- `result/output.md`

Issue summary:

- `result/issues/00-summary.md`

Trace logs:

- `logs/trace/`

The internal runtime cache remains under `SOURCE_ROOT/.loopforge/`, but it is not the primary evaluator-facing result.

## Scope

- This file is an execution manual, not a business-rule document.
- Do not require humans to edit `work/loopforge.config.yaml` for new tasks.
- Requirements should come from `SOURCE_ROOT` and its README, not from manual placeholder filling.
