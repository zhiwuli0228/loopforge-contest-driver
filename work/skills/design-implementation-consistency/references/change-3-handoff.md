# Change 3 Handoff Assumptions

This change produces the contract surface that Change 3 may rely on:

- stable stage IDs `dic-00` through `dic-09`
- stable acceptance baseline path `logs/trace/consistency/01-acceptance-baseline.json`
- stable gap model path `logs/trace/consistency/03-gap-model.json`
- stable repair batch path `logs/trace/consistency/04-repair-batches.json`
- stable build verification path `logs/trace/consistency/06-build-verification.json`
- stable black-box verification path `logs/trace/consistency/07-black-box-verification.json`
- stable retry repair path `logs/trace/consistency/08-retry-repair.json`

Assumptions for later pipeline work:

- Core models remain language-neutral and must not encode Java-only concepts.
- Adapters may enrich extraction detail, but they must populate the same artifact locations.
- Shared artifact schemas align to the acceptance-baseline, gap-model, repair, verification, and final-report contracts used by the repository runtime.
- Guard denials are evidence and must remain machine-readable at `logs/trace/consistency/guard-denials.jsonl`.
- `dic-09` finalization must tolerate partial upstream evidence when `always_finalize=true`.
