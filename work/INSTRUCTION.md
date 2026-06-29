# LoopForge Execution Instruction

## 1. Environment Preparation

- Runtime expects a workspace with `work/` and `code/` at the same root.
- Python 3.11+ is required for `work/runtime/loopforge_runner.py`.
- Official submission environment is Linux with `bash` and `python3`.
- Windows local development uses PowerShell plus Python.
- Project-specific build and test tools must already exist for the target project in `code/`.
- LoopForge core does not require network access.

## 2. Workspace Layout

```text
workspace/
├── work/
└── code/
```

`work/` is the LoopForge driver package. `code/` is the platform-provided target project. Runtime artifacts are written under `code/.loopforge/`.

## 3. Human Adaptation Before Execution

Fill [`work/loopforge.config.yaml`](</E:/009workspace/codex/loopforge-contest-driver/work/loopforge.config.yaml>) before unattended execution:

- `task.name`
- `task.mode`
- `task.profile`
- `task.language`
- `task.objective`
- `verification.commands`

LoopForge must not modify this configuration file during execution.

## 4. Official Linux Submission Execution

From the workspace root:

```bash
bash work/scripts/bootstrap.sh --work-dir work --code-dir code
```

## 5. Windows Development Execution

For local development and smoke testing on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File work/scripts/bootstrap.ps1 -WorkDir work -CodeDir code
```

Windows execution is for development compatibility only. Official submission remains Linux-first.

## 6. Agent Entrypoint

Then use the LoopForge agent entrypoint:

```text
work/skills/loopforge-driver/SKILL.md
```

The skill reads `work/loopforge.config.yaml`, loads the relevant rules, applies code changes only inside `code/`, invokes the runner, and stops after writing the final report.

## 7. Completion Criteria

Execution is complete when all of the following are true:

- `code/` contains the generated or repaired changes
- `code/.loopforge/reports/final-report.md` exists
- verification results are recorded in `code/.loopforge/`
- no commit, push, PR, or submission action was performed

## 8. Result Retrieval

The platform retrieves:

- `code/`

Primary report:

- `code/.loopforge/reports/final-report.md`
