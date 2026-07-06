## Why

Phase 5 parallel batch scheduling dispatches multiple subagents that modify shared source files (`lib.rs`, `Cargo.toml`, `types.rs`, and same-capability `.rs` modules). These file-level write races cause compilation failures, subagent re-dispatches, and cascading "fixes" where subagents silently repair code owned by other batches. Total wall-clock time inflates because subagents spend cycles fixing each other's code instead of implementing their own.

## What Changes

- **Batch module isolation**: Each implementation batch writes exclusively to its own independent module file(s). No batch modifies files owned by another batch. Shared infrastructure files (`lib.rs`, `Cargo.toml`) are touched only by the scaffold batch.
- **Scaffold pre-declaration**: The first P0 batch (scaffold) reads `implement-plan.md` to discover all module names and feature flags, then writes complete `lib.rs` and `Cargo.toml` before any parallel batch starts.
- **Cross-batch repair prohibition**: Subagents must confine compilation fixes to their own batch's files. Cross-file compilation errors are surfaced as `PHASE_DEGRADED` rather than silently patched.
- **Implement-plan target file contract**: Phase 4's `implement-plan.md` batch entries must declare a non-overlapping `rust_targets` field per batch, enabling the scheduling algorithm to verify file isolation at dispatch time.

## Capabilities

### New Capabilities

- `batch-module-isolation`: Each Phase 5 batch writes to capability-specific module files only; the file ownership contract is verified against `implement-plan.md`; no batch may write to a file declared by another batch.
- `scaffold-predeclaration`: The scaffold batch (lowest P0 batch_id, or explicitly marked as scaffold) reads all batch entries from `implement-plan.md`, extracts module names and feature flags, and writes complete `lib.rs` and `Cargo.toml` before parallel dispatch begins.
- `cross-batch-repair-prohibition`: When `cargo build` fails with errors in files outside the subagent's own batch scope, the subagent reports the errors via `PHASE_DEGRADED` rather than modifying those files.

### Modified Capabilities

- `agent-driven-code-generation`: Add requirements for batch-scoped file ownership (read existing module files for type information, but only write to own batch's files) and cross-batch repair prohibition.
- `skill-orchestration`: Update Phase 5 scheduling entry to include scaffold pre-declaration step and module isolation contract.

## Impact

- Affected files: `work/skills/c-to-rust-migration-v2/SKILL.md`, `work/subagent/c2r-04-plan.md`, `work/subagent/c2r-05-implement.md`
- No changes to runner (`loopforge_runner.py`), tools.py, SuperPower guards, or OpenSpec schemas
- Backward compatible: existing `implement-plan.md` from completed migrations already declare `rust_target` per batch — those targets were simply being ignored; this change enforces them as a contract
- No project-specific (FlashDB) customizations — all rules are generic to any C-to-Rust migration
