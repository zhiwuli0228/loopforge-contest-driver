# Core Model Contract

Authoritative Core types for shared stage artifacts:

- `01-acceptance-baseline.json` aligns to the canonical design model family and captures frozen API, error-code, and verification-command baselines.
- `02-source-inventory.json` and `02-adapter-selection.json` align to the implementation-inventory and adapter-selection contract.
- `03-gap-model.json` captures evidence-backed discrepancies between the acceptance baseline and implementation scope.
- `04-repair-batches.json` captures bounded repair intent and target ownership.
- `05-repair-execution.json`, `06-build-verification.json`, `07-black-box-verification.json`, and `08-retry-repair.json` capture repair and verification evidence for final verdict assembly.
- `09-finalization` and final report assembly use `work.core.report_model.ConsistencyReport`.

Shared invariants:

- Every canonical object carries a stable ID, neutral kind, name, summary, and evidence references.
- Adapter-specific metadata belongs in optional extension fields only.
- Findings, repair batches, and verification artifacts must carry evidence from both sides or an explicit unavailable-evidence reason.
