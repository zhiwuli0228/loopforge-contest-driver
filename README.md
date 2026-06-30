# LoopForge Contest Driver

This repository is a generic source-readme-driven C-to-Rust migration harness. It accepts a source tree path through `SOURCE_ROOT`, derives migration context from the source README, and writes evaluator-facing results to `result/` and `logs/`.

The file `work/code/README.md` is a contest requirement document and runtime fallback metadata source, not a source directory.

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
├── .code/   # optional local fallback source area
├── code/    # optional legacy workspace area
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

If `SOURCE_ROOT` is not provided, the runner first checks platform mounts and then scans local fallback source areas generically.

## Notes

- `work/loopforge.config.yaml` carries framework defaults, not task-specific hardcoded placeholders.
- Runtime evidence is written under `logs/trace/`, not under `SOURCE_ROOT`.
- The evaluator should read `result/output.md` first, not the internal final report path.
