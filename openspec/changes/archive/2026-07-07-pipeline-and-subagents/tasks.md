## 1. Stage package scaffold

- [x] 1.1 Create or normalize `work/subagent/dic-00-preflight.md` through `work/subagent/dic-09-finalize.md` so each stage package has a consistent structure for objective, inputs, outputs, gate, and failure handling.
- [x] 1.2 Add a stable stage-to-file mapping strategy so the orchestrator or Skill can resolve each `dic-0x` stage ID to exactly one stage package asset.
- [x] 1.3 Document the stage package boundary in the authoritative Skill so stage execution uses package files instead of inline monolithic prompts.

## 2. File-based handoff and gate behavior

- [x] 2.1 Define the required `logs/trace/consistency/` handoff artifacts, summary files, and evidence index paths for each stage transition.
- [x] 2.2 Update stage packages to consume only declared upstream files and emit explicit gate results, preserved evidence, and next-step disposition metadata.
- [x] 2.3 Ensure `dic-08` emits advisory-only repair plan artifacts and that `dic-09` can finalize from partial upstream outputs when earlier gates fail.

## 3. Contract alignment

- [x] 3.1 Align `work/profiles/superspec/design-implementation-consistency-stages.yaml` with the actual stage package filenames, output paths, and failure/finalize semantics.
- [x] 3.2 Align `work/profiles/superpower/design-implementation-consistency-guards.yaml` so every declared stage output path is writable and business source paths remain read-only under `analyze-only`.
- [x] 3.3 Update any related Skill or profile references so stage IDs, adapter outputs, Core artifact names, and stage package handoff terminology remain consistent across contracts.

## 4. Validation

- [x] 4.1 Add a focused validation check or fixture that verifies all ten stage IDs resolve to package files and that their declared outputs match the superspec and guard contracts.
- [x] 4.2 Verify a fail-soft path where an intermediate stage preserves evidence and `always_finalize=true` still allows `dic-09` to produce a terminal summary.
- [x] 4.3 Verify the pipeline remains `analyze-only`, never writes business source files, and hands downstream stages only declared file paths and summaries rather than full source context.
