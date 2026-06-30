# C2Rust FlashDB Semantic Equivalence Contract

- READY requires the semantic gate in addition to build, test, and unsafe gates.
- The generated Rust project must not be an empty crate.
- Rust tests must contain real assertions for migrated scenarios.
- `todo!()` and `unimplemented!()` are forbidden in generated Rust sources and tests.
- Generated Rust APIs must preserve the primary FlashDB source behaviors identified during analysis.
