## ADDED Requirements

### Requirement: Each batch writes only to its declared module files

A Phase 5 implementation batch SHALL write exclusively to the module files declared in its batch entry in `implement-plan.md` under the `rust_target` field. The batch SHALL NOT create, modify, or delete any `.rs` file that is declared as a `rust_target` for a different batch.

#### Scenario: Batch writes to own module
- **WHEN** a Phase 5 subagent implements its assigned batch
- **THEN** it reads the `rust_target` field from its batch entry in `implement-plan.md`
- **THEN** it writes Rust code only to the files listed in its own `rust_target` field

#### Scenario: Batch reads but does not write other modules
- **WHEN** a Phase 5 subagent needs to understand types, traits, or function signatures from other modules
- **THEN** it SHALL read existing modules in `OUTPUT_DIR/src/` for reference
- **THEN** it SHALL NOT write to any file outside its own `rust_target` list

#### Scenario: Shared infrastructure files excluded from batch scope
- **WHEN** a Phase 5 subagent is not the scaffold batch
- **THEN** it SHALL NOT modify `lib.rs` or `Cargo.toml`
- **THEN** these files SHALL have been already written by the scaffold batch

### Requirement: Scheduling algorithm verifies file ownership before parallel dispatch

Before dispatching batches in parallel at a priority level, the orchestrator SHALL verify that no two batches at that level share a `rust_target` file. If a conflict is detected, the orchestrator SHALL fall back to sequential execution for the conflicting batches.

#### Scenario: No conflicts — dispatch in parallel
- **WHEN** the orchestrator checks `rust_target` fields for all batches at a priority level
- **AND** no file path appears in more than one batch's `rust_target` list
- **THEN** all batches at that level SHALL be dispatched in parallel

#### Scenario: File conflict detected — fall back to sequential
- **WHEN** two or more batches at the same priority level declare the same file in their `rust_target` field
- **THEN** the orchestrator SHALL log a warning naming the conflicting batches and the shared file
- **THEN** the conflicting batches SHALL be executed sequentially in batch_id order

### Requirement: Capability types are self-contained or re-exported

Each capability module SHALL own its data types. Shared types that span multiple capabilities SHALL be defined in `types.rs` by the scaffold batch. Capability-specific types SHALL be defined within the capability's own module file.

#### Scenario: Shared type usage
- **WHEN** a capability module needs a shared type (e.g., `Db`, `Error`)
- **THEN** it imports it from `crate::types` using `use crate::types::Db`
- **THEN** the type is already declared in `types.rs` by the scaffold batch

#### Scenario: Capability-specific type definition
- **WHEN** a capability needs a type used only by that capability
- **THEN** the type is defined within the capability's own module file
- **THEN** other modules access it via `use crate::<module>::<Type>` if needed
