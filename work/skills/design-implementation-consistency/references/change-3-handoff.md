# Change 3 Handoff Assumptions

This change produces the contract surface that Change 3 may rely on:

- stable stage IDs `dic-00` through `dic-09`
- stable design model path `logs/trace/consistency/03-design-model.json`
- stable implementation model path `logs/trace/consistency/04-implementation-model.json`
- stable traceability path `logs/trace/consistency/05-traceability-matrix.json`
- stable drift path `logs/trace/consistency/06-drift-analysis.md`
- stable risk path `logs/trace/consistency/07-risk-classification.md`

Assumptions for later pipeline work:

- Core models remain language-neutral and must not encode Java-only concepts.
- Adapters may enrich extraction detail, but they must populate the same artifact locations.
- Shared artifact schemas align to `work.core.design_model.DesignModel`, `work.core.implementation_model.ImplementationModel`, `work.core.traceability_model.TraceabilityMatrix`, and `work.core.report_model.ConsistencyReport`.
- Guard denials are evidence and must remain machine-readable at `logs/trace/consistency/guard-denials.jsonl`.
- `dic-09` finalization must tolerate partial upstream evidence when `always_finalize=true`.
