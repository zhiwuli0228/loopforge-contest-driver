# LoopForge Harness

## Workspace Model

LoopForge is a generic contest execution harness.

The external task input is:

```text
SOURCE_ROOT + source README
```

`SOURCE_ROOT` points to the source tree supplied by the contest platform or by a local evaluator.
Task requirements, constraints, and acceptance context come from the README under `SOURCE_ROOT`.

## Read Order

Read and follow:

1. `INSTRUCTION.md`
2. `work/loopforge.config.yaml`
3. `work/rules/loopforge/common/`
4. `work/rules/loopforge/core/`
5. `work/rules/loopforge/modes/{task.mode}/`
6. `work/skills/loopforge-driver/SKILL.md`

## Entrypoints

Linux:

```bash
SOURCE_ROOT="/path/to/source" bash work/scripts/run.sh
```

Linux fallback:

```bash
bash work/scripts/run.sh
```

Windows PowerShell:

```powershell
$env:SOURCE_ROOT="C:\path\to\source"
powershell -ExecutionPolicy Bypass -File work/scripts/run.ps1
```

## Source Path Resolution

Resolve the source path in this order:

1. Platform-provided source path
2. Explicit `--source-root`
3. `SOURCE_ROOT`
4. Contest platform source mount on Linux
5. Local fallback `code/`

Runtime evidence may be written under `SOURCE_ROOT/.loopforge/`.
Evaluator-facing outputs must be written under `result/` and `logs/`.
