# C-To-Rust Semantic Equivalence Contract

- READY requires the semantic gate in addition to build, test, and unsafe gates.
- The generated Rust project must not be an empty crate.
- Rust tests must contain real assertions for migrated scenarios.
- `todo!()` and `unimplemented!()` are forbidden in generated Rust sources and tests.
- Generated Rust APIs must preserve the primary source behaviors identified during analysis.
# Pre-generation semantic planning gate

Before Rust project generation, the runner MUST successfully publish and verify the five artifacts defined in `work/docs/FLASHDB_SEMANTIC_PLANNING.md`. The planner MUST bind its evidence to one passed source-analysis run and MUST independently require 100% public API, core type/member, shared-state, and core call-edge coverage. State transitions and executable semantic invariants MUST be non-empty.

If this gate fails, the runner MUST report `BLOCKED_WITH_REPORT` with first blocking point `SEMANTIC_MIGRATION_PLANNING` and MUST NOT invoke project generation. Later Cargo or semantic checks cannot override this failure.
