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

## Unattended Delegated Execution Contract

This project must be executed in unattended mode.

After reading this file, the agent must not wait for human confirmation between stages.

For non-trivial tasks, especially `consistency-check`, the agent must not execute the whole workflow in one monolithic reasoning context.

The agent must act as an orchestrator and execute the task through staged delegated execution.

Subagent execution is mandatory for each stage.

Required contract:

- `subagent_required: true`
- `fallback_to_main_context_allowed: false`
- `missing_subagent_policy: BLOCKED_WITH_REPORT`
- `parent_direct_execution_allowed: false`
- `file_handoff_required: true`

Required stages:

1. Preflight
2. Design Read
3. Implementation Mapping
4. Drift Analysis
5. Repair Planning
6. Patch Implementation
7. Verification
8. Final Report

Each stage must:

- read only its required input files
- write its output artifact under `code/.loopforge/consistency/`
- expose a machine-readable gate status
- avoid returning full long-form analysis to the orchestrator context
- use file artifacts as the handoff mechanism
- automatically continue to the next stage when the gate allows it
- be executed by its declared subagent
- set `parent_direct_execution_allowed: false`

No manual prompt between stages is allowed.

If a stage cannot continue, the agent must generate a blocked or degraded report and still produce `code/.loopforge/reports/final-report.md` when possible.

If required subagents are unavailable, stop immediately with:

```text
BLOCKED_WITH_REPORT
reason: required subagent unavailable
```

The main Build session must not simulate stage execution in its own context.

## Manual Stage Prompt Policy

Manual stage-by-stage prompting is forbidden.

The user or contest platform must not be required to issue separate prompts for:

- design reading
- implementation mapping
- repair planning
- patch implementation
- verification
- final report generation

All stage transitions must be decided by the orchestrator using file artifacts and gate statuses.

The orchestrator may only:

- read the entry instruction and stage contracts
- check subagent availability
- invoke the declared stage subagent
- read the stage artifact gate
- assemble the final report

The orchestrator must not directly perform design analysis, implementation mapping, drift analysis, repair planning, patching, or full verification inside the parent context.

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
