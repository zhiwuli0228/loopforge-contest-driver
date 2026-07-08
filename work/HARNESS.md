# LoopForge Harness

## Workspace Model

LoopForge is a generic contest execution harness.

The external task input is:

```text
read-only SUBMISSION_ROOT
```

`SUBMISSION_ROOT` points to the contest-style submission package supplied by the platform or by a local evaluator.
Task requirements, constraints, and acceptance context come from `SUBMISSION_ROOT/README.md` and `SUBMISSION_ROOT/design-docs/`.

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
SUBMISSION_ROOT="/path/to/submission" bash work/scripts/run.sh
```

Linux fallback:

```bash
bash work/scripts/run.sh
```

## Source Path Resolution

Resolve the submission path in this order:

1. Platform-provided submission path
2. Explicit `--submission-root`
3. `SUBMISSION_ROOT`
4. Explicit `--source-root` or legacy `SOURCE_ROOT` as a temporary compatibility alias
5. Contest platform source mount on Linux

Runtime evidence must be written under `logs/trace/`. The submission package under `SUBMISSION_ROOT` is read-only in analyze-only mode and must not receive `.loopforge`, reports, snapshots, or generated artifacts.
Evaluator-facing outputs must be written under `result/` and `logs/`.
