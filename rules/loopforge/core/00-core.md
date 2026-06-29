# LoopForge Core

## Purpose

LoopForge is a reusable Loop Engineering hosting platform. It hosts unattended AI coding workflows through a stable core plus configurable `Mode + Profile`, instead of embedding project-specific logic into the platform itself.

## Stable Model

- The current directory is the human-maintained LoopForge root.
- `code/` is the mutable target project nested under the root.
- `code/.loopforge/` is the runtime artifact area.
- `task.mode` selects the generic workflow pattern.
- `task.profile` selects task-specific configuration without changing the core.

## Execution Intent

LoopForge should be able to:

- read static platform instructions and constraints from the current root
- inspect and modify only the target project under `code/`
- run deterministic local verification from configured commands
- leave behind a report and evidence package under `code/.loopforge/`

LoopForge should not:

- assume a single contest problem or business domain
- encode specific project logic into the runner core
- rely on hooks, MCP servers, or external services for the core flow
- continue into source control or platform submission actions

## Required Read Order

The agent should read in this order:

1. `INSTRUCTION.md`
2. `loopforge.config.yaml`
3. all files under `rules/loopforge/core/`
4. the selected mode rules under `rules/loopforge/modes/{task.mode}/`
5. relevant adapter rules under `rules/loopforge/adapters/`
6. the configured profile under `profiles/`

## Completion Contract

A LoopForge run is considered complete only when:

- code changes, if any, are left in `code/`
- runtime evidence is left in `code/.loopforge/`
- the final report exists at the configured output path
- no commit, push, PR, or submission action has been performed
