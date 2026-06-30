# Daily Dev Usage

## Setup

1. Create and activate a Python environment.
2. Install `work/requirements.txt`.
3. Set `SOURCE_ROOT` to the source tree you want to evaluate, or use local fallback `code/`.

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

- `result/output.md`
- `result/issues/00-summary.md`
- `logs/interaction.md`
- `logs/trace/run-summary.json`
