# c2r-04: Plan

## Role

Create the implementation task list and batch plan. Write phase — produces `tasks.md` and `implement-plan.md`.

## Context

You receive:
- `OPENSPEC_CHANGE` — the OpenSpec change name
- `SOURCE_ROOT` — path to the C source tree
- `WORK_DIR` — path to the work directory
- Phase 2 output: `design.md` location
- Phase 3 output: `specs/` directory location

## SuperPower Rules

Read `work/profiles/superpower/c-to-rust-migration-guards.yaml`, section `plan`.

- **Allowed tools**: none (pure agent reasoning)
- **Allowed filesystem**: read `**`, write `openspec/changes/*/tasks.md`, write `openspec/changes/*/implement-plan.md`
- **Forbidden**: modify source code, modify tools.py, modify profiles

## Steps

1. Call `openspec instructions tasks --change "OPENSPEC_CHANGE" --json` to get the tasks template
2. Read `design.md` for the migration approach
3. Read all `specs/*/spec.md` files for requirements
4. Create `tasks.md`:
   - Group tasks by module/batch
   - Each task is a checkbox: `- [ ] X.Y Task description`
   - Order by dependency
5. Create `implement-plan.md`:
   - Map specs to code batches (5-8 functions per batch)
   - Define expected build/test commands per batch
   - Assign subagent strategy per batch
   - Each batch should be independently buildable

## Output

Write two files to the OpenSpec change directory:
- `tasks.md` — implementation checklist
- `implement-plan.md` — batch-level plan mapping specs to code

## Gate

Return one of:
- `PHASE_PASS` — both files written, plan is complete
- `PHASE_BLOCKED` — specs insufficient to create a plan
- `PHASE_DEGRADED` — plan exists but batches are uneven or unclear
