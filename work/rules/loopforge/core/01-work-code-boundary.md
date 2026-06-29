# Work And Code Boundary

## Directory Roles

- `work/` holds static platform assets: instructions, config, rules, profiles, runtime source, scripts, and docs.
- `code/` holds the target project to inspect, repair, migrate, or extend.
- `code/.loopforge/` holds LoopForge execution artifacts generated during the run.

## Allowed Actions

- Read files from `work/` as the source of truth for execution policy.
- Inspect files under `code/` to understand the target project.
- Modify files under `code/` when the selected mode and configuration allow code generation.
- Create or update artifact files only under `code/.loopforge/`.

## Forbidden Actions

- Do not write any runtime artifact into `work/`.
- Do not move target-project files into `work/`.
- Do not rewrite `work/` docs, rules, profiles, scripts, or config during execution.
- Do not treat the repository root as the mutable project root when `work/` and `code/` are present.

## Boundary Checks

Before making code changes, the agent should confirm:

- the workspace actually contains both `work/` and `code/`
- `work/` and `code/` are isolated sibling trees
- the configured artifact directory resolves under `code/`

If any boundary check fails, execution should block with a report rather than proceed heuristically.
