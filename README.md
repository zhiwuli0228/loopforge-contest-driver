# LoopForge Contest Driver

This repository is a contest submission driver. It accepts a source tree path through `SOURCE_ROOT`, reads the source README to build task context, and writes evaluator-facing results to `result/` and `logs/`.

## Reproduce

Start from [INSTRUCTION.md](./INSTRUCTION.md).

Primary outputs:

- [result/output.md](./result/output.md)
- [result/issues/00-summary.md](./result/issues/00-summary.md)
- [logs/trace/](./logs/trace/)

## Input Model

The contest-facing input model is:

- `SOURCE_ROOT`
- README files located at the source root

Supported README names:

- `README.md`
- `README`
- `readme.md`
- `Readme.md`

The framework records which README was selected. If no README is available, the run degrades into an explicit report instead of waiting for manual config edits.

## Layout

```text
.
├── INSTRUCTION.md
├── code/    # local fallback source tree
├── work/    # framework assets
├── result/  # evaluator-facing outputs
└── logs/    # trace outputs
```

## Quick Start

Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r work/requirements.txt
SOURCE_ROOT="/path/to/source" bash work/scripts/run.sh
```

Linux fallback mode:

```bash
bash work/scripts/run.sh
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r work\requirements.txt
$env:SOURCE_ROOT="C:\path\to\source"
powershell -ExecutionPolicy Bypass -File work/scripts/run.ps1
```

If `SOURCE_ROOT` is not provided, Linux first checks the platform source mount and then falls back to `code`. Windows and local development fall back to `code`.

## Notes

- `work/loopforge.config.yaml` carries framework defaults, not per-task manual placeholders.
- Internal runtime artifacts may still appear under `SOURCE_ROOT/.loopforge/`.
- The evaluator should read `result/output.md` first, not the internal final report path.
