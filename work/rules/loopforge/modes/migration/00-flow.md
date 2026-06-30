# Migration Flow

## Applies To

- language migrations
- framework migrations
- platform migrations
- bounded subsystem rewrites that preserve externally relevant behavior

## Flow

`SOURCE_INVENTORY -> TARGET_ARCHITECTURE -> COMPATIBILITY_CONTRACT -> MIGRATION_PLAN -> CODE_GENERATE -> COMPATIBILITY_VERIFY -> FINAL_REPORT`

## Phase Outcomes

- `SOURCE_INVENTORY`: map source modules, responsibilities, and risky dependencies
- `TARGET_ARCHITECTURE`: define the intended target structure before translation
- `COMPATIBILITY_CONTRACT`: state what must remain behaviorally compatible
- `MIGRATION_PLAN`: sequence the migration into bounded steps
- `CODE_GENERATE`: apply migration changes under `code/`
- `COMPATIBILITY_VERIFY`: run configured verification and compatibility checks
- `FINAL_REPORT`: capture migration coverage and unresolved gaps
