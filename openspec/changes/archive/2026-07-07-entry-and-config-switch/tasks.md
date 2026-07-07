## 1. Entry Documentation Rewrite

- [x] 1.1 Rewrite `README.md` to present the repository as a design-implementation consistency checking harness.
- [x] 1.2 Rewrite `INSTRUCTION.md` so the primary task narrative, execution entry, and output expectations use `consistency-check` semantics.
- [x] 1.3 Update `work/README.md` to describe `work/` as the contract and runtime asset area for consistency-check workflows.

## 2. Default Configuration and Contract

- [x] 2.1 Update `work/loopforge.config.yaml` so the default mode resolves to `consistency-check`.
- [x] 2.2 Update `work/loopforge.config.yaml` so the default execution strategy resolves to `analyze-only`.
- [x] 2.3 Rewrite `work/design/README.md` to define the consistency-check task contract, expected inputs, and completion criteria for Change 1.

## 3. Verification and Consistency Review

- [x] 3.1 Verify that the top-level entry documents no longer frame the project as a Rust migration harness.
- [x] 3.2 Verify that the default configuration and design README use aligned terminology and do not contradict each other.
- [x] 3.3 Re-run `openspec status --change "entry-and-config-switch"` and confirm the change artifacts are complete enough for implementation.
