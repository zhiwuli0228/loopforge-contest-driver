## ADDED Requirements

### Requirement: Scaffold batch extracts all module names from implement-plan

The first P0 batch (lowest `batch_id`, conventionally Batch 0 or Batch 1) SHALL be the scaffold batch. Before writing its own capability code, it SHALL read `implement-plan.md` and extract every batch's `rust_target` field to produce a complete list of all module files in the migration.

#### Scenario: Scaffold batch discovers modules from plan
- **WHEN** the scaffold batch executes
- **THEN** it reads `implement-plan.md` before writing any code
- **THEN** it extracts the `rust_target` field from every batch entry
- **THEN** it produces a deduplicated list of all module files (e.g., `src/status.rs`, `src/flash.rs`, ...)
- **THEN** it derives the corresponding module names (e.g., `status`, `flash`, ...)

### Requirement: Scaffold batch writes complete lib.rs with all module declarations

The scaffold batch SHALL write `OUTPUT_DIR/src/lib.rs` containing `pub mod` declarations for every module discovered from `implement-plan.md`.

#### Scenario: lib.rs with full module declarations
- **WHEN** the scaffold batch completes its `lib.rs` writing
- **THEN** `lib.rs` contains a `pub mod` declaration for every module file in the migration
- **THEN** no subsequent batch needs to add, remove, or reorder `pub mod` entries
- **THEN** `#![cfg_attr(...)]` attributes at the top of `lib.rs` are written by the scaffold batch and never modified by other batches

#### Scenario: Scaffold batch validates plan completeness
- **WHEN** the scaffold batch checks each batch entry in `implement-plan.md`
- **AND** a batch entry has no `rust_target` field
- **THEN** the scaffold batch SHALL return `PHASE_BLOCKED` with a message naming the incomplete batch

### Requirement: Scaffold batch writes complete Cargo.toml with all features

The scaffold batch SHALL write `OUTPUT_DIR/Cargo.toml` containing all `[features]` flags mentioned in any batch entry in `implement-plan.md`.

#### Scenario: Cargo.toml with all feature flags
- **WHEN** the scaffold batch completes its `Cargo.toml` writing
- **THEN** `Cargo.toml` contains all feature flag names from `implement-plan.md` batch entries in the `[features]` section
- **THEN** no subsequent batch needs to add or remove `[features]` entries

#### Scenario: No features declared
- **WHEN** `implement-plan.md` contains no feature flag declarations in any batch entry
- **THEN** `Cargo.toml` SHALL be written with no `[features]` section, or an empty `[features]` section
- **THEN** the scaffold batch still succeeds

### Requirement: Scaffold batch creates minimal shared type definitions

The scaffold batch SHALL write minimal foundational types in `OUTPUT_DIR/src/types.rs` (or equivalent shared module) that all subsequent batches depend on. At minimum: an error type and any root data structures declared in the design or spec phases.

#### Scenario: Foundation types created
- **WHEN** the scaffold batch writes `types.rs`
- **THEN** it contains at minimum an `Error` type (enum or struct) and a root database handle type
- **THEN** all subsequent batches use `use crate::types::Error` etc. without needing to extend the file

#### Scenario: Additional shared types needed later
- **WHEN** a subsequent batch discovers it needs a shared type not in `types.rs`
- **THEN** it SHALL define the type in its own capability module file
- **THEN** it SHALL NOT modify `types.rs`
- **THEN** other batches import it from the capability module

### Requirement: Subsequent batches never modify infrastructure files

Batches with `batch_id` greater than the scaffold batch's id SHALL NOT create, modify, or delete `OUTPUT_DIR/src/lib.rs`, `OUTPUT_DIR/Cargo.toml`, or `OUTPUT_DIR/src/types.rs`.

#### Scenario: Non-scaffold batch respects infrastructure boundaries
- **WHEN** a non-scaffold Phase 5 subagent executes
- **THEN** it reads `lib.rs`, `Cargo.toml`, and `types.rs` for reference
- **THEN** it SHALL NOT write to any of these files
- **THEN** if it needs a type that should be shared, it defines it in its own module and documents the import path for other batches
