# Core Consistency Models

`work/core/` defines the adapter-neutral model contract for design-implementation consistency checks.

Rules:

- Use language-neutral kinds and field names.
- Keep framework-specific metadata in optional extension fields.
- Do not require Java-, Spring-, controller-, service-, or repository-specific concepts in shared model contracts.
- Treat evidence references as part of the canonical data model rather than a reporting-only concern.
