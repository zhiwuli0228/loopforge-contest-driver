# Design

LoopForge is a reusable Loop Engineering hosting platform. Contest tasks are only one use case; the platform core remains generic and stable.

## Architectural Intent

- keep driver assets stable under the submission root
- keep target code isolated under `code/`
- keep runtime artifacts under `code/.loopforge/`
- keep task-specific details in profiles rather than in runner logic
- keep workflow selection in `task.mode`, not in hard-coded task packs

## Core Components

- `work/skills/loopforge-driver/SKILL.md`: agent entrypoint
- `work/runtime/loopforge_runner.py`: deterministic execution helper
- `work/rules/loopforge/core/`: invariant platform rules
- `work/rules/loopforge/modes/`: reusable flow definitions
- `work/rules/loopforge/adapters/`: language and platform guidance
- `work/profiles/`: configuration templates and examples
- `work/docs/CROSS_PLATFORM_DESIGN.md`: Windows-development and Linux-submission compatibility contract

## Execution Model

LoopForge operates as:

`Core + Mode + Profile`

Where:

- Core defines invariant platform boundaries and reporting contracts
- Mode defines the generic workflow shape
- Profile provides task-specific configuration only

## Boundary Contract

- the submission root outside `code/` is human-maintained and read-only during execution
- `code/` is the only business-code mutation area
- `code/.loopforge/` is the only runtime artifact area
- verification commands come only from `work/loopforge.config.yaml`
- LoopForge generates code and reports, but never commits, pushes, creates PRs, or submits results

## Runner Responsibilities

The runner is a deterministic executor. It is responsible for:

- reading `work/loopforge.config.yaml`
- validating the LoopForge root package and selected mode/profile contract
- creating `code/.loopforge/`
- copying its runtime into `code/.loopforge/runtime/`
- recording state, gate events, snapshots, and verification summaries
- executing configured `verification.commands`
- generating `code/.loopforge/reports/final-report.md`

The runner is not responsible for:

- understanding repository-specific business intent
- generating task-specific static rules
- guessing verification commands
- performing source-control submission actions
