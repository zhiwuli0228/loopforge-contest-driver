## Why

Change 1 (Python Tools Layer) provides raw data commands but no structured execution framework. The V2 architecture defines SuperSpec as execution stage definitions and SuperPower as permission boundaries. SuperSpec should extend OpenSpec's schema system (not be a standalone YAML) so that `openspec instructions` and `openspec status` work natively for all migration phases.

## What Changes

- Fork the `spec-driven` schema into a project-local `c2r-migration` schema that adds `implement-plan` and `verification-report` artifacts after `tasks`
- Add `work/profiles/superpower/c-to-rust-migration-guards.yaml` — permission boundary definitions mapping each phase to allowed/forbidden actions
- The schema becomes the single source of truth for execution stages; OpenSpec CLI handles dependency ordering and context delivery

## Capabilities

### New Capabilities

- `c2r-migration-schema`: OpenSpec schema fork extending `spec-driven` with execution artifacts (implement-plan, verification-report), dependency ordering, and instruction templates
- `superpower-guards`: Permission boundary YAML — maps each migration phase to allowed tools.py commands, filesystem access patterns, and forbidden actions

### Modified Capabilities

(none)

## Impact

- New schema under `openspec/schemas/c2r-migration/` (project-local)
- New YAML under `work/profiles/superpower/`
- `openspec new change` can use the new schema: `--schema c2r-migration`
- Change 3 (SKILL.md + subagents) consumes schema artifacts and SuperPower guards at runtime
- No code changes to existing modules
