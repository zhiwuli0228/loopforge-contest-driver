## Context

The repository currently presents itself as a C/C++ to Rust migration harness, and the default workspace/configuration assets still reinforce that framing. The blueprint for this branch splits the overall transition into ordered changes, with the first change responsible for reorienting entry points and defaults toward `consistency-check`.

This change is intentionally upstream of the later contract, model, and pipeline work. It should make the repository readable as a consistency validation project before any deeper architectural work begins.

## Goals / Non-Goals

**Goals:**
- Reframe repository entry documentation around design-implementation consistency checking.
- Set the default workflow semantics to `consistency-check` and `analyze-only`.
- Make `work/design/README.md` the authoritative task contract for the first change boundary.
- Keep later architectural work unblocked by using stable terminology and clear file responsibilities.

**Non-Goals:**
- Do not implement the later OpenSpec/Skill/Profile contract changes in this change.
- Do not change runtime code paths, algorithms, or analysis logic.
- Do not remove legacy assets from the repository in this change.
- Do not introduce compatibility shims for old and new semantic names.

## Decisions

1. Use documentation and configuration updates, not code-level indirection, to change the project narrative.
   - Rationale: the problem here is semantic drift at the entry layer, not runtime behavior. Updating the user-facing contract is faster, clearer, and less risky than threading compatibility logic through the runtime.
   - Alternatives considered: add a translation layer between old and new terms, or leave the old docs and add a new entry file. Both would preserve ambiguity and split the source of truth.

2. Treat `consistency-check` as the default task mode and `analyze-only` as the default execution strategy.
   - Rationale: the blueprint explicitly wants a read-only baseline before any repair or mutation capability is considered.
   - Alternatives considered: retain migration defaults and override them later in profiles. That would keep the wrong baseline visible and invite accidental use of the old workflow.

3. Keep `work/design/README.md` as the contract anchor for the first change.
   - Rationale: the repository already uses this file as the authoritative design input. Rewriting it to match the new task model keeps downstream changes aligned without forcing extra discovery logic.
   - Alternatives considered: move the contract into a new location or duplicate it in multiple files. That would weaken the single-source-of-truth model and complicate later change sequencing.

4. Leave legacy C2Rust assets in place for now, but stop presenting them as the main path.
   - Rationale: the blueprint reserves legacy isolation and archival for a later cleanup change. Keeping the assets avoids unnecessary churn while reducing user confusion through the new entry narrative.
   - Alternatives considered: remove or relocate all legacy files immediately. That would broaden scope and risk disrupting the transition sequence.

## Risks / Trade-offs

- [Risk] Some docs may still contain legacy migration references after the first pass. → Mitigation: rewrite the root-facing entry points first, then clean up legacy references in the later isolation change.
- [Risk] Default configuration may diverge from future profile-specific execution. → Mitigation: keep the default baseline narrow and let later profile/guard changes define richer behavior.
- [Risk] `work/design/README.md` may not yet contain the final downstream contract details. → Mitigation: make it a stable first-step contract and expand exact stage semantics in the next change.

## Migration Plan

1. Update the repository root documentation and workspace README to foreground consistency checking.
2. Update `work/loopforge.config.yaml` defaults so new runs start in `consistency-check` / `analyze-only`.
3. Rewrite `work/design/README.md` to describe the first-change contract and expected outputs.
4. Validate that the new terminology is consistent across the three entry points.

Rollback strategy:
- Restore the previous documentation wording and default config values if the new baseline creates confusion, while leaving the repo structure intact.

## Open Questions

- Should legacy migration terminology remain in an archived subsection of the root README, or be fully removed from entry-facing text?
- Should the next change update any example profiles at the same time, or keep profile work isolated to Change 2?
- Is `analyze-only` sufficient as the default execution strategy, or should a more explicit read-only label be introduced in the next contract change?
