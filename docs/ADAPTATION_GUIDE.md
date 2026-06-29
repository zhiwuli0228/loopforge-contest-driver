# Adaptation Guide

## Adaptation Sequence

1. Place the target repository under `code/`.
2. Choose the correct mode for the task:
   - `feature-development`
   - `migration`
   - `defect-repair`
   - `consistency-check`
   - `skill-generation`
3. Select or clone a suitable template from `profiles/templates/`.
4. Point `task.profile` at the chosen profile.
5. Update `loopforge.config.yaml` with task metadata and real verification commands.
6. Confirm that `execution.allow_code_generation` matches the intended run.
7. Use `scripts/bootstrap.sh` for Linux submission-oriented runs from the repository root.
8. Use `scripts/bootstrap.ps1` for Windows local development and smoke testing from the repository root.
9. Run the LoopForge skill and let it operate only inside `code/`.

## What Must Be Human-Adapted

- task name
- task mode
- profile path
- primary and secondary language fields
- objective text
- verification working directory
- verification commands
- platform-specific verification command profiles when Linux and Windows differ

## Profile Editing Rules

- keep profiles declarative
- do not move core policy from `rules/` into profiles
- do not encode repository-specific runner logic into profiles
- use `templates/` as starting points and `examples/` only as reference classes
- keep example profiles generic enough to reuse across repositories

## Mode Selection Guidance

- Use `feature-development` when the input is a requirement to build something new.
- Use `migration` when the task preserves behavior while moving across languages, frameworks, or platforms.
- Use `defect-repair` when a bug, regression, or failing behavior is the primary driver.
- Use `consistency-check` when analysis and drift reporting are primary and repair is optional.
- Use `skill-generation` when the output is a reusable business skill rather than business code.

## Adaptation Rules

- do not edit static root files during execution
- do not leave `verification.commands` as placeholders
- do not encode project-specific logic into the runner
- do not allow runtime artifacts to escape `code/.loopforge/`
- do not treat profiles as places for core logic

## Runner Contract Checks

The runner now checks the adapted package for basic contract validity. In practice this means:

- `task.profile` must exist under the LoopForge root
- profile `task.mode` must match `loopforge.config.yaml`
- `verification.working_directory` must stay inside `code/`
- configured report and snapshot outputs must stay inside `code/`

If these checks fail, LoopForge should block with report output rather than continue on guessed assumptions.

The runner also checks:

- required static files under the LoopForge root
- required core rule files
- required files for the selected mode directory
- basic profile section completeness
- template/example inventory counts for `profiles/`
- platform-specific verification command selection and fallback behavior
