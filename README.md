# LoopForge Contest Driver

LoopForge Contest Driver is a reusable contest-oriented automation base for unattended AI coding tasks. It uses a `Skill + Rule + Runner` structure so the same driver can be copied into unknown target repositories and still bootstrap a consistent execution loop without hooks, custom servers, or third-party dependencies.

## Why This Exists

Contest environments usually provide a place to copy skills and rules, but do not guarantee project-local tools, hooks, or pre-created runtime directories. LoopForge is designed for that constraint set:

- `Skill` is the single entry point.
- `Rule` files define protocol, outputs, and guardrails.
- `Runner` performs deterministic local actions.
- `.loopforge/` stores state, evidence, and reports.

## Design Choices

### No Hook Requirement

LoopForge does not rely on hooks because contest environments may disable or omit them. The workflow remains functional with only copied `skills/` and `rules/`.

### Runner-First Execution

The runner is generated into the target repository from `rules/loopforge/20-runner-source-python.md`. This keeps the deterministic logic local to the target project and avoids requiring additional installation steps.

## Repository Layout

```text
.
├── README.md
├── RUNNING.md
├── skills/
│   └── loopforge-driver/
│       └── SKILL.md
├── rules/
│   └── loopforge/
│       ├── 00-core.md
│       ├── 01-bootstrap-runner.md
│       ├── 02-mode-selection.md
│       ├── 03-spec-normalization.md
│       ├── 04-brainstorm.md
│       ├── 05-subagent-lease.md
│       ├── 06-gate-policy-contest.md
│       ├── 07-verification-policy.md
│       ├── 08-repair-policy.md
│       ├── 09-final-report.md
│       ├── 10-java-maven.md
│       ├── 11-python-pytest.md
│       ├── 12-test-generation.md
│       ├── 13-spec-code-drift.md
│       ├── 20-runner-source-python.md
│       └── 21-tool-wrapper-optional.md
└── optional-opencode/
    └── tools/
        └── loopforge.ts
```

## Supported Modes

- `spec-implementation`
- `test-generation`
- `spec-code-drift`

`clean-code-repair` is defined in the design but intentionally not implemented in this MVD.

## Execution Flow

1. Load `skills/loopforge-driver/SKILL.md`.
2. Load the LoopForge rule pack under `rules/loopforge/`.
3. Bootstrap `.loopforge/` in the target repository.
4. Materialize `.loopforge/runtime/loopforge_runner.py` from the runner source rule.
5. Run runner phases such as `--init`, `--self-check`, `--detect`, `--snapshot`, `--prepare`, `--start-apply`, `--complete-apply`, `--integrate-review`, `--verify`, `--repair`, `--finalize`.
6. Let the coding agent apply changes within the current work tree.
7. Run verification and finalize phases in later milestones.
8. Emit `.loopforge/reports/final-report.md` or a degraded fallback report.

## Current Milestone

This repository now covers V0.1-V0.5 from the design document:

- project skeleton and documentation
- skill entrypoint
- core rule pack
- Python runner template
- runner support for `--init`, `--self-check`, `--detect`, `--snapshot`
- deterministic workflow artifact generation through `--prepare <task-file>`
- apply-stage evidence scaffolding through `--start-apply`
- subagent report backfill through `--complete-apply`
- lease-based integrate review through `--integrate-review`
- Java Maven verification support in `--verify`
- repair state progression through `--repair`
- final report generation in `--finalize`

Not yet implemented in the runner:

- repair orchestration
- executable non-Java verification
- automatic business-code application under lease control
- repair loop

## Failure and Degrade Strategy

LoopForge follows `fail-soft, block-late`:

- ordinary failures should prefer retry, repair, or degrade
- hard blocking is reserved for destructive or unrecoverable situations
- final report generation remains mandatory whenever possible

## Runtime Artifacts

When copied into a target project and executed, LoopForge creates:

```text
.loopforge/
├── runtime/
├── task/
├── spec/
├── brainstorm/
├── plan/
├── leases/
├── snapshots/
├── subagents/
├── gates/
├── state/
└── reports/
```

The runner can now generate the initial workflow artifacts from a raw task file:

```bash
python .loopforge/runtime/loopforge_runner.py --prepare path/to/task.txt
```

## How To Run

See `RUNNING.md` for the contest-facing copy and execution instructions.

## Known Limits

- repair orchestration is not implemented yet
- Python, Node, and Go verification remain rule-defined but not executable yet
- drift analysis is rule-defined only in this milestone
- no hooks, no MCP server, no custom tool dependency
