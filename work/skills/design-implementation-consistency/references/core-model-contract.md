# Core Model Contract

Authoritative Core types for shared stage artifacts:

- `03-design-model.json` aligns to `work.core.design_model.DesignModel`
- `04-implementation-model.json` aligns to `work.core.implementation_model.ImplementationModel`
- `05-traceability-matrix.json` aligns to `work.core.traceability_model.TraceabilityMatrix`
- `06-drift-analysis.*` uses `work.core.drift_taxonomy` categories and `work.core.report_model.DriftFinding`
- `07-risk-classification.*` uses `work.core.severity_policy.SeverityAssessment`
- `09-finalization` and final report assembly use `work.core.report_model.ConsistencyReport`

Shared invariants:

- Every canonical object carries a stable ID, neutral kind, name, summary, and evidence references.
- Adapter-specific metadata belongs in optional extension fields only.
- Findings and traceability artifacts must carry evidence from both sides or an explicit unavailable-evidence reason.
