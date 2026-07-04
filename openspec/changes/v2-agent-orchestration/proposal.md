## Why

Change 1 (Python Tools Layer) provides the CLI data commands. Change 2 (Execution Framework) provides the `c2r-migration` schema and SuperPower permission guards. Neither provides the actual agent orchestration logic — the piece that ties the 10-phase workflow into a coherent, self-driving migration. Without SKILL.md and phase-specific subagent prompts, the agent has no structured way to sequence phases, manage context boundaries, or enforce SuperPower rules at runtime.

## What Changes

- New `work/skills/c-to-rust-migration-v2/SKILL.md` — the top-level orchestration prompt that drives the entire 10-phase migration workflow (preflight → understand → design → spec → plan → implement → test → repair → semantic-audit → quality-gates → finalize)
- 11 new subagent prompt files under `work/subagent/`:
  - `c2r-00-preflight.md` through `c2r-10-finalize.md` — each defines the bounded context, allowed tools, read/write scope, expected output, and pass/fail gate for one migration phase
- Each subagent reads its SuperPower guards from `work/profiles/superpower/c-to-rust-migration-guards.yaml` and its stage definition from the `c2r-migration` schema
- SKILL.md consumes `openspec instructions` output for each phase to get artifact templates and dependency context

## Capabilities

### New Capabilities

- `skill-orchestration`: Top-level SKILL.md that sequences all 10 migration phases, delegates to subagents, handles phase transitions, and aggregates results
- `subagent-phase-prompts`: 11 phase-specific subagent prompts with bounded context (~2K tokens each), clear input/output contracts, and SuperPower-enforced write scope

### Modified Capabilities

(none)

## Impact

- **Files**: `work/skills/c-to-rust-migration-v2/SKILL.md` (new), `work/subagent/c2r-00-preflight.md` through `c2r-10-finalize.md` (11 new files)
- **Dependencies**: Consumes Change 1 (`tools.py` commands) and Change 2 (`c2r-migration` schema, SuperPower guards)
- **No code changes**: Pure prompt files, no Python or Rust modifications
- **Supersedes**: Existing `work/skills/c-to-rust-migration/SKILL.md` and old subagent files (can coexist, v2 is separate)
