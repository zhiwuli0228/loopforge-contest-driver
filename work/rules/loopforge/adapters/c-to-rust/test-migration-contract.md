# C-To-Rust Test Migration Contract

- Inventory all C tests under the resolved source project test directories.
- Create Rust tests under the runtime-derived output project `tests/`.
- Each C test scenario must be migrated or equivalently covered.
- If a test cannot be migrated, document the reason in `work/result/issues/00-summary.md`.
- Empty tests are not acceptable.
- Tests without assertions are not acceptable.
- Synthetic Rust tests must still trace back to explicit C scenarios.
