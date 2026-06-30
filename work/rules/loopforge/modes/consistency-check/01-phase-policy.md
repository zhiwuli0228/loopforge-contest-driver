# Phase Policy

- Default to analysis, mapping, and reporting before any repair.
- Read frozen design documents listed by the active profile or task configuration as the first evidence source.
- Perform repair only when explicitly enabled.
- Classify drift before proposing any code change.
- Create an implementation mapping and traceability matrix before repair.
- Create a repair plan before editing code.
- Separate confirmed drift from ambiguous design gaps.
- Preserve traceability between each finding and its evidence source.
- Execute configured verification commands after repair, or record a degraded verification reason when blocked by external dependencies.

