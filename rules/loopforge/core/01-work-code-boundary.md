# Root And Code Boundary

## Directory Roles

- The current root holds static platform assets: instructions, config, rules, profiles, runtime source, scripts, and docs.
- `code/` holds the nested target project to inspect, repair, migrate, or extend.
- `code/.loopforge/` holds LoopForge execution artifacts generated during the run.

## Allowed Actions

- Read files from the current root as the source of truth for execution policy.
- Inspect files under `code/` to understand the target project.
- Modify files under `code/` when the selected mode and configuration allow code generation.
- Create or update artifact files only under `code/.loopforge/`.

## Forbidden Actions

- Do not write any runtime artifact into the static root outside `code/.loopforge/`.
- Do not move target-project files out of `code/`.
- Do not rewrite root docs, rules, profiles, scripts, or config during execution.
- Do not treat the LoopForge root itself as the mutable business-code area.

## Boundary Checks

Before making code changes, the agent should confirm:

- the current root actually contains `code/`
- `code/` is nested under the current root
- the configured artifact directory resolves under `code/`

If any boundary check fails, execution should block with a report rather than proceed heuristically.
