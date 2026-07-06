## Why

E2E session analysis (`session-ses_0ced.md`) revealed that Phase 3 wrote 14 spec files inline in the main agent context, Phase 4 wrote 2 plan files inline, and Phase 5 fabricated massive inline prompts bundling 6+ batches per subagent. By the time Phase 5 reached the TSDB subagent, the context window was exhausted and the task was cancelled. The delegation strategy in SKILL.md and INSTRUCTION.md incorrectly marks heavy-output phases as "Keep inline", causing predictable context explosion on any non-trivial migration.

## What Changes

- **Phase 3 (Spec)**: Changed from "Keep inline" to delegated via `c2r-03-spec.md`. Subagent reads capability map, writes all spec files in isolation, returns a gate token.
- **Phase 4 (Plan)**: Changed from "Keep inline" to delegated via `c2r-04-plan.md`. Subagent reads specs, writes `tasks.md` and `implement-plan.md` in isolation, returns a gate token.
- **Phase 5 (Implement)**: Delegated with a dynamic scheduling algorithm. Main agent parses `implement-plan.md` to discover batch count and dependency graph, then dispatches one subagent per batch at each priority level. Batches at the same level with no inter-dependencies run in parallel. Each subagent references `c2r-05-implement.md` by file path with only `BATCH_ID` and context variables — no inline-constructed prompts. Subagents return only gate tokens (`PHASE_PASS` + one-line summary).
- **Subagent result compression**: All subagent gate responses are reinforced to return `PHASE_PASS`/`PHASE_BLOCKED`/`PHASE_DEGRADED` plus a one-line summary, not full implementation reports.
- **INSTRUCTION.md delegation table**: Updated to match the corrected strategy.

## Capabilities

### New Capabilities

- `context-safe-delegation`: SKILL.md orchestration rules that enforce all heavy-output phases (Spec, Plan, Implement) are delegated to subagents, with subagent prompt files referenced by path rather than inline-constructed.
- `dynamic-batch-scheduling`: Algorithm for Phase 5 that parses `implement-plan.md`, discovers batch count and dependencies at runtime, and dispatches one subagent per batch with dependency-aware parallelism.

### Modified Capabilities

- `superpower-guards`: Phase 3 and Phase 4 guard definitions must be updated from "Keep inline" to "Delegate" with their respective subagent prompt file references.

## Impact

- `work/skills/c-to-rust-migration-v2/SKILL.md` — delegation table, Phase 3/4/5 orchestration rules
- `INSTRUCTION.md` — Phase 3/4/5 delegation strategy in the two-stage pipeline table
- `work/subagent/c2r-03-spec.md` — verify completeness (may need minor updates for batch output expectations)
- `work/subagent/c2r-05-implement.md` — verify it supports per-batch dispatch (one batch per invocation)
