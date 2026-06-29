# LoopForge Execution Instruction

This directory is the contest project root.

Do not look for another nested `work/` directory.

## 1. Environment Preparation

- Runtime expects the current directory to contain LoopForge assets plus `code/`.
- Python 3.11+ is required for `runtime/loopforge_runner.py`.
- Official submission environment is Linux with `bash` and `python3`.
- Windows local development uses PowerShell plus Python.
- Project-specific build and test tools must already exist for the target project in `code/`.
- LoopForge core does not require network access.

## 2. Workspace Layout

```text
.
├── INSTRUCTION.md
├── loopforge.config.yaml
├── code/
├── skills/
├── runtime/
├── scripts/
├── rules/
└── profiles/
```

Treat this directory as LoopForge driver assets. Treat `code/` as the target project. Runtime artifacts are written only under `code/.loopforge/`.

## 3. Human Adaptation Before Execution

Fill `loopforge.config.yaml` before unattended execution:

- `task.name`
- `task.mode`
- `task.profile`
- `task.language`
- `task.objective`
- `verification.commands`

LoopForge must not modify this configuration file during execution.

## 4. Official Linux Submission Execution

From this directory:

```bash
bash scripts/bootstrap.sh
```

## 5. Windows Development Execution

For local development and smoke testing on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
```

Windows execution is for development compatibility only. Official submission remains Linux-first.

## 6. Agent Entrypoint

Then use the LoopForge agent entrypoint:

```text
skills/loopforge-driver/SKILL.md
```

The skill reads `loopforge.config.yaml`, loads the relevant rules, applies code changes only inside `code/`, invokes the runner, and stops after writing the final report.

## 7. Agent Auto-Start

If you are an AI coding agent, contest executor, or OpenCode agent, execute this file directly.

Steps:

1. Read `skills/loopforge-driver/SKILL.md`.
2. Read `loopforge.config.yaml`.
3. Treat this root directory as LoopForge driver assets.
4. Treat `code/` as the target project.
5. Treat `code/docs/` as frozen design documents if present.
6. Write runtime artifacts only under `code/.loopforge/`.
7. Execute the task mode configured in `loopforge.config.yaml`.
8. Execute verification commands configured in `loopforge.config.yaml`.
9. Generate `code/.loopforge/reports/final-report.md`.
10. Stop after final report generation.

Forbidden:

- Do not modify `skills/**`, `rules/**`, `runtime/**`, `scripts/**`, `profiles/**` unless the task explicitly says to modify LoopForge itself.
- Do not modify `code/docs/**`.
- Do not run `git add`, `git commit`, `git push`, or create PRs.

## 8. Completion Criteria

Execution is complete when all of the following are true:

- `code/` contains the generated or repaired changes
- `code/.loopforge/reports/final-report.md` exists
- verification results are recorded in `code/.loopforge/`
- no commit, push, PR, or submission action was performed

## 9. Result Retrieval

The platform retrieves:

- `code/`

Primary report:

- `code/.loopforge/reports/final-report.md`
