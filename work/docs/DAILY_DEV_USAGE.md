# Daily Dev Usage

## Setup

1. Create and activate a Python environment.
2. Install `work/requirements.txt`.
3. Set `SOURCE_ROOT` explicitly; on Windows, `work/code/` is the default input when it is omitted.

## Common Commands

Linux:

```bash
SOURCE_ROOT="/path/to/source" bash work/scripts/run.sh
```

Windows:

```powershell
$env:SOURCE_ROOT="C:\path\to\source"
powershell -ExecutionPolicy Bypass -File work/scripts/run.ps1
```

## Expected Outputs

- `work/result/output.md`
- `work/result/issues/00-summary.md`
- `work/logs/interaction.md`
- `work/logs/trace/run-summary.json`
