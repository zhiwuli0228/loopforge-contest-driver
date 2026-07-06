## ADDED Requirements

### Requirement: Phase 5 scheduling includes scaffold pre-declaration step

The Phase 5 scheduling algorithm in SKILL.md SHALL include a scaffold pre-declaration step executed by the first P0 batch before any parallel dispatch. The scaffold batch SHALL read all batch entries from `implement-plan.md` and write complete `lib.rs` and `Cargo.toml` with entries for every module and feature in the plan.

#### Scenario: Scaffold batch runs first in P0
- **WHEN** the orchestrator starts Phase 5
- **THEN** it dispatches all P0 batches including the scaffold batch
- **THEN** the scaffold batch writes complete `lib.rs` (all module declarations) and `Cargo.toml` (all feature flags) before writing its own capability code
- **THEN** subsequent P0 batches and all P1/P2 batches SHALL NOT modify `lib.rs` or `Cargo.toml`

### Requirement: Phase 5 scheduling verifies file isolation before parallel dispatch

The Phase 5 scheduling algorithm SHALL verify that no two batches at the same priority level share a `rust_target` file before dispatching them in parallel.

#### Scenario: Rust target overlap detected
- **WHEN** two or more batches at the same priority level declare overlapping `rust_target` files
- **THEN** the orchestrator SHALL log a warning identifying the conflicting batches and shared files
- **THEN** the orchestrator SHALL execute the conflicting batches sequentially in batch_id order within that priority level

#### Scenario: No overlap — parallel dispatch
- **WHEN** all batches at a priority level have mutually exclusive `rust_target` files
- **THEN** the orchestrator SHALL dispatch them in parallel as specified by the existing scheduling algorithm
