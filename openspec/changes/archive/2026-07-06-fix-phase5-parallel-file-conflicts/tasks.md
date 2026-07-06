## 1. Update c2r-05-implement.md — batch-scoped file ownership

- [x] 1.1 Add `rust_target` extraction step: after reading batch assignment (Step 1), extract the `rust_target` file list from the batch entry and store it as the batch's write scope
- [x] 1.2 Replace Step 5 ("Update Project Files") with scaffold vs non-scaffold branching: if BATCH_ID is the scaffold batch (lowest P0 batch_id), read all batch entries from implement-plan.md, extract all module names and feature flags, write complete lib.rs and Cargo.toml; if not the scaffold batch, skip lib.rs/Cargo.toml modifications entirely
- [x] 1.3 Add file ownership constraint to Step 4 ("Write Rust Code"): subagent SHALL only create or modify files listed in its batch's `rust_target` field; reading any file in OUTPUT_DIR/ is allowed
- [x] 1.4 Update Step 7 ("Build Verification") error handling: add a rule that compilation errors in files NOT in the batch's `rust_target` list SHALL NOT be fixed; the subagent SHALL report them as PHASE_DEGRADED with file paths, line numbers, and error messages
- [x] 1.5 Update the Gate section: PHASE_DEGRADED description now includes "external compilation errors in other batches' files" as a valid degradation reason
- [x] 1.6 Add scaffold batch validation: if acting as scaffold batch, validate that every batch entry in implement-plan.md has a `rust_target` field; return PHASE_BLOCKED if any batch is missing it

## 2. Update SKILL.md Phase 5 — scaffold pre-declaration and file isolation

- [x] 2.1 Update Phase 5 scheduling algorithm (Step 1): before dispatching P0 batches, designate the scaffold batch (lowest batch_id at P0) and note its special responsibilities
- [x] 2.2 Add file isolation verification step: after parsing batches, check that no two batches at the same priority level share a `rust_target` file; if conflicts exist, mark affected batches for sequential execution and log a warning
- [x] 2.3 Update Phase 5 output description: note that lib.rs and Cargo.toml are written only by the scaffold batch, while each capability module file is owned by exactly one batch
- [x] 2.4 Add Phase 5 dispatch note: the scaffold batch is dispatched first (or concurrently with other P0 batches, but its lib.rs/Cargo.toml must be written before non-scaffold batches read them — other P0 batches can still run in parallel since they write to their own module files)

## 3. Update c2r-04-plan.md — enforce implement-plan file contract

- [x] 3.1 In the implement-plan batch template (Step 4), add a note that `Rust target files` entries MUST be unique per batch — no two batches may list the same file
- [x] 3.2 Add `[features]` declaration to the first batch (scaffold) entry template: the scaffold batch entry SHALL list all Cargo.toml feature flags needed by any batch, so the scaffold subagent can pre-declare them
- [x] 3.3 Add validation guidance: the Phase 4 subagent SHALL check that each batch declares at least one non-shared `Rust target file` and that no file appears in more than one batch's target list before finalizing implement-plan.md
- [x] 3.4 Update the batch format example to show `Rust target files` as a non-comment marker (ensure it uses a consistent key name like `rust_target` or `Rust target files` that the scaffold batch can parse)

## 4. Verification — cross-reference and consistency check

- [x] 4.1 Verify that c2r-05-implement.md uses consistent terminology with SKILL.md (scaffold batch designation, `rust_target` field name, PHASE_DEGRADED format)
- [x] 4.2 Verify that SKILL.md Phase 5 dispatch protocol references the same field name (`rust_target`) that c2r-04-plan.md produces and c2r-05-implement.md consumes
- [x] 4.3 Review all modified files for project-specific (FlashDB) hardcoded content — any such content must be replaced with generic, path-variable-based descriptions
