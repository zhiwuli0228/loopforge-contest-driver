# Contest Execution Instruction

This file is the root entrypoint for the contest evaluator and AI coding agent.

## 1. Read platform materials

Before making any change, read the runnable framework materials under:

- `work/HARNESS.md`
- `work/skills/loopforge-driver/SKILL.md`
- `work/loopforge.config.yaml`

Do not treat `INSTRUCTION.md` as the full workflow. It only routes the agent to the runnable materials in `work/`.

## 2. Resolve source path

Resolve the source project path in the following order:

1. Use the source path provided by the contest platform when invoking this instruction.
2. If no platform path is provided on Linux, try the configured absolute path in `work/loopforge.config.yaml`.
3. If still unresolved, use `code/` under this repository root as the local fallback path.

## 3. Execute framework

Follow `work/HARNESS.md`.

The framework assets are under `work/`. The source project is outside `work/`, or under `code/` only for local fallback.

## 4. Required output locations

When execution completes, ensure these paths exist:

- `result/output.md`
- `logs/interaction.md`
- `logs/trace/`

Do not require human interaction during automated execution.
