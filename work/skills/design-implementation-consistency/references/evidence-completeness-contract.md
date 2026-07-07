# Evidence Completeness Contract

A confirmed finding requires this minimum record:

- `finding_id`
- `stage_id`
- `design_evidence`
- `implementation_evidence`
- `traceability_link`
- `risk_level`
- `summary`

If design or implementation evidence is missing, the finding must instead record:

- `unavailable_evidence_reason`
- `next_best_observable_signal`

Invalid finding cases:

- only design evidence is present
- only implementation evidence is present
- evidence points outside declared inputs
- risk level is missing

Invalid findings remain draft observations and must not be promoted into confirmed drift output.
