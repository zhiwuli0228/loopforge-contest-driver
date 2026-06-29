# LoopForge Execution Instruction

## 1. Environment Preparation

- Runtime expects a workspace with `work/` and `code/` at the same root.
- Python 3.11+ is required for `work/runtime/loopforge_runner.py`.
- A POSIX shell is expected for `work/scripts/bootstrap.sh` and `work/scripts/smoke-test.sh`.
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

## 4. Execution Method

From the workspace root:

```bash
bash work/scripts/bootstrap.sh --work-dir work --code-dir code
```

Then use the LoopForge agent entrypoint:

```text
work/skills/loopforge-driver/SKILL.md
```

The skill reads `work/loopforge.config.yaml`, loads the relevant rules, applies code changes only inside `code/`, invokes the runner, and stops after writing the final report.

## 5. Completion Criteria

Execution is complete when all of the following are true:

- `code/` contains the generated or repaired changes
- `code/.loopforge/reports/final-report.md` exists
- verification results are recorded in `code/.loopforge/`
- no commit, push, PR, or submission action was performed

## 6. Result Retrieval

The platform retrieves:

- `code/`

Primary report:

- `code/.loopforge/reports/final-report.md`
