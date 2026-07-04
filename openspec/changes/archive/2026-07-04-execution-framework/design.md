## Context

V2 architecture defines:
- OpenSpec = thinking framework (proposal → design → specs → tasks)
- SuperSpec = execution stage definitions (implement, test, repair, etc.)
- SuperPower = permission boundaries

The key insight: SuperSpec should NOT be a standalone YAML. It should extend OpenSpec's schema system so that `openspec instructions`, `openspec status`, and dependency tracking work natively for execution phases.

Current state: `spec-driven` schema has 4 artifacts (proposal, specs, design, tasks). We need to add 2 execution artifacts (implement-plan, verification-report) to cover Phases 5-10 from the V2 blueprint.

## Goals / Non-Goals

**Goals:**
- Fork `spec-driven` schema into project-local `c2r-migration` schema
- Add `implement-plan` artifact: batch-level implementation plan (spec → Rust mapping, batch boundaries)
- Add `verification-report` artifact: cargo build/test results, repair log, gate outcomes
- Create SuperPower YAML for permission boundaries (separate from schema)
- Use `openspec schema init` or manual creation under `openspec/schemas/`

**Non-Goals:**
- No changes to the `spec-driven` package schema
- No Python code changes
- No agent orchestration logic (that's Change 3)
- No runtime execution

## Decisions

**1. Schema fork via `openspec schema init` + manual extension**

Use `openspec schema init c2r-migration --artifacts proposal,specs,design,tasks` to scaffold, then manually add `implement-plan` and `verification-report` artifacts with their templates and instructions.

Alternatives considered:
- `openspec schema fork spec-driven c2r-migration`: copies all templates, but we need to verify the output structure
- Manual creation from scratch: more control but more work

**2. Two execution artifacts, not six**

`implement-plan` covers Phase 5-6 (implement + test batch planning). `verification-report` covers Phase 7-10 (repair, semantic audit, quality gates, finalize results). This keeps the artifact count manageable while preserving phase-level granularity in the YAML instructions.

**3. implement-plan is per-batch, verification-report is aggregate**

The implement-plan artifact describes ONE batch of work (which specs, which functions, expected outputs). The verification-report aggregates all build/test/repair/gate results into a single report. This matches the subagent model: each subagent works one batch, then results are aggregated.

**4. SuperPower stays as YAML, not schema artifacts**

Permission boundaries are config (what you CAN do), not workflow (what you SHOULD do). They belong in YAML under `work/profiles/`, not as OpenSpec artifacts. The schema defines the workflow; SuperPower constrains the execution.

**5. Schema location: `openspec/schemas/c2r-migration/`**

Project-local schemas go under `openspec/schemas/`. This is the standard OpenSpec convention. The schema is automatically discovered by `openspec new change --schema c2r-migration`.

## Risks / Trade-offs

- **[Risk] Schema init command may not support custom artifacts well** → Fallback: manually create schema.yaml and templates
- **[Risk] Two artifacts may be too coarse for complex migrations** → Agent can create sub-plans within implement-plan; verification-report can have detailed sections
- **[Trade-off] Fewer artifacts = simpler workflow vs. more granular tracking** → Chosen: simpler workflow, agent handles granularity internally

## Migration Plan

1. Run `openspec schema init c2r-migration` to scaffold
2. Edit `openspec/schemas/c2r-migration/schema.yaml` to add implement-plan and verification-report
3. Create templates for new artifacts
4. Validate with `openspec schema validate c2r-migration`
5. Create SuperPower YAML under `work/profiles/superpower/`

## Open Questions

- Should `openspec new change --schema c2r-migration` be the default for all migration changes? (Decision: yes, set `--default` during init)
