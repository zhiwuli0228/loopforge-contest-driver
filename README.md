# LoopForge Core

LoopForge is a reusable unattended AI coding framework. In this contest package, the repository root is the submission root, `work/` holds the runnable framework assets, and `code/` is the local fallback source tree.

## Quick Start

For execution and reproduction, start from [INSTRUCTION.md](E:/009workspace/codex/loopforge-contest-driver/INSTRUCTION.md).

The expected root-level execution summary is written to [result/output.md](E:/009workspace/codex/loopforge-contest-driver/result/output.md).

## Platform Model

```text
.
├── INSTRUCTION.md
├── code/    # local fallback source tree
├── work/    # framework assets
├── result/  # root-level output placeholder
└── logs/    # root-level execution records
```

- Root `INSTRUCTION.md` is the only contest entry file.
- `work/` contains instructions, rules, profiles, runtime code, scripts, docs, and templates.
- `code/` remains available as the default local target project path.
- `code/.loopforge/` stores runtime artifacts, reports, and snapshots for actual execution.

## Design Boundaries

- LoopForge core is task-agnostic.
- Tasks are configured through `Mode + Profile`.
- Static files in this root, except `code/`, are human-owned and read-only to the agent.
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

- `INSTRUCTION.md`
- `work/HARNESS.md`
- `work/loopforge.config.yaml`
- `work/runtime/loopforge_runner.py`
- `work/skills/loopforge-driver/SKILL.md`

## Directory Map

```text
.
├── code/
├── work/
│   ├── docs/
│   ├── profiles/
│   ├── rules/
│   ├── runtime/
│   ├── scripts/
│   ├── subagent/
│   └── skills/
├── result/
└── logs/
```

Use `work/profiles/templates/` as starting points during adaptation and `work/profiles/examples/` as reference configurations for different task classes.

## Verification Model

LoopForge does not guess project verification commands. Human adaptation must provide `verification.commands` in `work/loopforge.config.yaml`. The runner executes those commands inside the configured working directory and records the result under `code/.loopforge/state/`.

## Execution Model

LoopForge uses unattended delegated staged execution for `consistency-check` tasks.

The user or contest platform only needs to start from `INSTRUCTION.md`.

The main session is an orchestrator only. It must not execute stage work in a monolithic parent context.

All stage contracts are stored in:

- `work/profiles/superspec/consistency-check-stages.yaml`
- `work/profiles/superpower/consistency-check-guards.yaml`
- `work/rules/loopforge/modes/consistency-check/delegated-execution.md`

Runtime artifacts are written to:

- `code/.loopforge/consistency/`
- `code/.loopforge/reports/final-report.md`

The delegated execution contract requires:

- `subagent_required: true`
- `fallback_to_main_context_allowed: false`
- `missing_subagent_policy: BLOCKED_WITH_REPORT`
- `parent_direct_execution_allowed: false`
- `file_handoff_required: true`

If the required subagent layer is unavailable, the run must stop with `BLOCKED_WITH_REPORT` instead of continuing in the main Build context.

## Runner Validation

Before or during execution, the runner validates:

- `platform.work_dir` and `platform.code_dir` against the actual invocation
- `task.mode` against supported modes
- `task.profile` existence and basic structure
- profile mode alignment with `work/loopforge.config.yaml`
- verification working-directory placement under `code/`
- output paths staying under `code/`
- delegated subagent contract presence for consistency-check stages
- final report evidence requirements for subagent-executed stages

Phase-6 validation should cover both:

- positive smoke checks for artifact creation
- negative-path checks that prove invalid contracts degrade into `BLOCKED_WITH_REPORT`
