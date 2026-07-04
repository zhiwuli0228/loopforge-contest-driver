## Why

[1-2 sentences on the problem or opportunity. What problem does this solve? Why now? Reference the capability map if a brainstorm has been completed. If this is before the brainstorm phase, describe the migration goal in terms of the source project.]

## What Changes

[Bullet list of changes. Be specific about new capabilities, modifications, or removals. Each bullet should map to a capability or a pipeline artifact.]

- [Change 1 — e.g., "Migrate the CRC32 computation module from fdb_utils.c to Rust with identical table and algorithm"]
- [Change 2 — ...]

## Capabilities

### New Capabilities

[List each new capability being introduced. Each becomes `specs/<capability-id>/spec.md`. If brainstorm has not yet run, list estimated capabilities based on source code structure.]

- **[capability-id]**: [One-line description of what this capability does]
- **[capability-id]**: [One-line description]

### Modified Capabilities

[List existing capabilities whose requirements are changing. If none, write: "None — all capabilities are new."]

- **[capability-id]**: [Description of what is changing and why]

## Impact

[Affected code, APIs, dependencies, or systems. List specific files or modules that will be created or modified.]

- **New files**: [list]
- **Modified files**: [list or "None"]
- **Dependencies**: [external crates, tools, or systems affected]
