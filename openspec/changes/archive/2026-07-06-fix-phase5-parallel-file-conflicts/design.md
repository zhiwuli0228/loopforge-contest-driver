## Context

Phase 5 (Implement) uses dynamic batch scheduling: the orchestrator parses `implement-plan.md`, groups batches by priority (P0→P1→P2), and dispatches independent batches at the same priority level in parallel. Each subagent writes Rust code, runs `cargo build`, writes tests, and returns a gate token.

Analysis of a full pipeline execution log reveals that parallel batches frequently modify the same physical source files:

- `lib.rs` — every batch adds `pub mod` declarations
- `Cargo.toml` — batches add feature flags and dependencies
- Shared capability modules (e.g., `kvdb.rs` modified by 5 batches, `tsdb.rs` by 3 batches)
- `types.rs` — all batches add types to the shared type pool

When `cargo build` (a global compilation) fails due to errors in files written by parallel batches, subagents "helpfully" fix the errors in those files — creating race conditions where two subagents simultaneously edit the same file. The observed consequences include: empty task results requiring re-dispatch, subagents spending cycles fixing other batches' code, post-Phase-5 build errors requiring manual fixes, and 17 compiler warnings (lifetime elision mismatches, unused variables, dead code) from inconsistent conventions across independently-written test files.

## Goals / Non-Goals

**Goals:**
- Eliminate file-level write conflicts between parallel Phase 5 subagent batches
- Make each batch's build self-contained: `cargo build` succeeds or fails based only on that batch's own code, not on parallel batches' incomplete code
- Enforce file ownership boundaries via the `implement-plan.md` contract, not via prompt "advice"
- Keep the change generic — no project-specific paths, file names, or heuristics

**Non-Goals:**
- Changing the priority-level scheduling algorithm itself
- Modifying the Python runner or tools.py
- Adding workspace/crate-level isolation (over-engineering for current scale)
- Changing Phase 6-10 behavior
- Making `implement-plan.md` generation smarter (Phase 4 already declares `rust_target` per batch)

## Decisions

### Decision 1: One capability = one module file

Each batch writes to its own capability-specific module file(s). No batch appends to a file declared as `rust_target` for another batch.

**Rationale**: Rust allows `impl` blocks for the same struct across multiple files within a crate. Capability modules can `use crate::types::Kvdb` and add `impl Kvdb { ... }` blocks without colliding. This is the standard Rust pattern for splitting large modules.

**Alternative considered**: Workspace-based isolation (sub-crates). Rejected because it introduces unnecessary complexity for the current pipeline scale — cross-crate API management, version coordination, and increased subagent prompt complexity.

### Decision 2: Scaffold batch reads implement-plan to pre-declare everything

The lowest Batch ID at P0 (conventionally Batch 0 or Batch 1) is designated as the scaffold batch. Before writing its own capability code, it:
1. Reads `implement-plan.md` and extracts every batch's `rust_target` field
2. Writes `lib.rs` with all `pub mod` declarations for every module in the plan
3. Writes `Cargo.toml` with all `[features]` entries from the plan
4. Writes minimal shared types (`Db`, `Error`) in `types.rs`
5. Proceeds to implement its own capability code

Subsequent batches never modify `lib.rs`, `Cargo.toml`, or another batch's `rust_target` files.

**Rationale**: `implement-plan.md` already declares `rust_target` per batch — this is the existing Phase 4 output contract. The scaffold batch reads it and materializes the shared infrastructure. No new Phase 4 prediction required.

**Alternative considered**: Separate "Phase 4.5" scaffold phase. Rejected because it adds pipeline complexity for a simple read-then-write operation that fits naturally in P0.

### Decision 3: Subagent prompt forbids cross-batch file modifications

`c2r-05-implement.md` is updated to include:
- A rule: "Only write to files listed in your batch's `rust_target` field from the implement plan."
- A fallback: "If `cargo build` fails with errors in files NOT listed in your batch's `rust_target`, do NOT modify those files. Report those errors as `PHASE_DEGRADED` with the error details."
- A note: "You may READ any file in the project to understand types, traits, and signatures. The restriction applies only to WRITE operations."

**Rationale**: Subagents in the log analysis showed a consistent pattern of "helpful" cross-batch fixing. Prompt-level guardrails are lightweight but the wording must be explicit — "do NOT modify" rather than "avoid modifying."

**Alternative considered**: SuperPower guard enforcement. Rejected because SuperPower already allows `src/**/*.rs` — file-level discrimination within that glob would require per-batch dynamic guard generation, which is a different architectural problem.

### Decision 4: implement-plan `rust_target` field becomes a contract

Phase 4's `c2r-04-plan.md` prompt already produces a `rust_target` field per batch (e.g., `Rust target: src/kvdb.rs`). This field is formalized as a file-level ownership contract:
- The scheduling algorithm in SKILL.md verifies no two batches share a `rust_target` before dispatching in parallel
- If a conflict is detected, the orchestrator falls back to sequential execution for conflicting batches

**Rationale**: This turns an advisory field into a verified invariant. The verification is cheap (string comparison on target paths) and catches Phase 4 output bugs before they cause runtime corruption.

## Risks / Trade-offs

- **Cross-module type visibility**: When capability modules need access to private types declared in another module (e.g., `pub(crate)` helpers), the owning module must expose them. Risk: may require minor follow-up edits to add `pub(crate)` visibility. Mitigation: subagents READ all existing modules, so they can see what's available and annotate as needed within their own module.

- **Scaffold batch failure**: If the scaffold batch fails (returns PHASE_BLOCKED), no lib.rs/Cargo.toml exists and all subsequent batches would fail. Mitigation: this is already the case today — the P0 batch that creates the project skeleton failing halts Phase 5. The scheduling algorithm handles this by not advancing past P0 until all P0 batches return gate tokens.

- **Phase 4 output contract dependency**: If Phase 4 fails to declare all `rust_target` fields correctly, the scaffold batch's pre-declared lib.rs will be incomplete. Mitigation: the scaffold batch validates that every batch in implement-plan.md has a `rust_target` field and returns `PHASE_BLOCKED` with a specific error if any are missing.

- **Test file isolation**: Tests are typically per-capability (`tests/<capability>_tests.rs`), which is already the convention. No additional risk beyond what source file isolation introduces.
