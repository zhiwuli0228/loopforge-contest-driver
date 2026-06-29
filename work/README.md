# LoopForge Core

LoopForge is a reusable Loop Engineering hosting platform for unattended AI coding workflows. It separates static human-maintained driver assets from mutable target-project artifacts through a strict `work/` and `code/` layout.

## Platform Model

```text
workspace/
├── work/   # driver package
└── code/   # target project
```

- `work/` contains instructions, rules, profiles, runtime code, and scripts.
- `code/` contains the project under repair, migration, development, or analysis.
- `code/.loopforge/` stores execution artifacts, reports, and snapshots.

## Design Boundaries

- LoopForge core is task-agnostic.
- Tasks are configured through `Mode + Profile`.
- Static files under `work/` are human-owned and read-only to the agent.
- The agent may change files only in `code/` and `code/.loopforge/`.
- The runner executes only human-configured verification commands.
- LoopForge never performs commit, push, PR creation, or platform submission.

## Supported Modes

- `feature-development`: requirement-driven delivery
- `migration`: source-to-target migration with compatibility control
- `defect-repair`: minimal bug fixing with regression awareness
- `consistency-check`: design-versus-implementation analysis with optional controlled repair
- `skill-generation`: reusable business-skill creation from a tool capability

Each mode defines:

- applicability
- ordered workflow phases
- required artifacts
- forbidden actions
- final-report extensions

## Key Files

- [`INSTRUCTION.md`](</E:/009workspace/codex/loopforge-contest-driver/work/INSTRUCTION.md>)
- [`loopforge.config.yaml`](</E:/009workspace/codex/loopforge-contest-driver/work/loopforge.config.yaml>)
- [`runtime/loopforge_runner.py`](</E:/009workspace/codex/loopforge-contest-driver/work/runtime/loopforge_runner.py>)
- [`skills/loopforge-driver/SKILL.md`](</E:/009workspace/codex/loopforge-contest-driver/work/skills/loopforge-driver/SKILL.md>)

## Directory Map

```text
work/
├── docs/
├── profiles/
├── rules/
├── runtime/
├── scripts/
└── skills/
```

Use `profiles/templates/` as starting points during adaptation and `profiles/examples/` as reference configurations for different task classes.

## Verification Model

LoopForge does not guess project verification commands. Human adaptation must provide `verification.commands` in `work/loopforge.config.yaml`. The runner executes those commands inside the configured working directory and records the result under `code/.loopforge/state/`.

## Runner Validation

Before or during execution, the runner validates:

- `platform.work_dir` and `platform.code_dir` against the actual invocation
- `task.mode` against supported modes
- `task.profile` existence and basic structure
- profile mode alignment with `loopforge.config.yaml`
- verification working-directory placement under `code/`
- output paths staying under `code/`

Phase-6 validation should cover both:

- positive smoke checks for artifact creation
- negative-path checks that prove invalid contracts degrade into `BLOCKED_WITH_REPORT`
