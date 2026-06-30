# Root And Source Boundary

## Directory Roles

- The current root holds static platform assets: instructions, config, rules, profiles, runtime source, scripts, and docs.
- `SOURCE_ROOT` holds the resolved target project to inspect, repair, migrate, or extend.
- `SOURCE_ROOT/.loopforge/` holds LoopForge execution artifacts generated during the run.

## Allowed Actions

- Read files from the current root as the source of truth for execution policy.
- Inspect files under `SOURCE_ROOT` to understand the target project.
- Modify files under `SOURCE_ROOT` when the selected mode and configuration allow code generation.
- Create or update artifact files only under `SOURCE_ROOT/.loopforge/`.

## Forbidden Actions

- Do not write any runtime artifact into the static root outside `SOURCE_ROOT/.loopforge/`.
- Do not move target-project files out of `SOURCE_ROOT`.
- Do not rewrite root docs, rules, profiles, scripts, or config during execution.
- Do not treat the LoopForge root itself as the mutable business-code area.

## Boundary Checks

Before making code changes, the agent should confirm:

- `SOURCE_ROOT` resolves to an existing source tree
- the configured artifact directory resolves under `SOURCE_ROOT`
- evaluator-facing outputs resolve under `result/` and `logs/`

If any boundary check fails, execution should block with a report rather than proceed heuristically.

