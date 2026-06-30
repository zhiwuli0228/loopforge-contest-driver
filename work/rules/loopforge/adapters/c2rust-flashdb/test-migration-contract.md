# C2Rust FlashDB Test Migration Contract

- Inventory all C tests under FlashDB `tests/`.
- Create Rust tests under `flashDB_rust/tests/`.
- Each C test scenario must be migrated or equivalently covered.
- If a test cannot be migrated, document the reason in `result/issues/00-summary.md`.
- Empty tests are not acceptable.
- Tests without assertions are not acceptable.
- Synthetic Rust tests must still trace back to explicit C scenarios.
