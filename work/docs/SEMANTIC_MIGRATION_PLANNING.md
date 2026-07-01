# Semantic Migration Planning

The planner is driven only by verified evidence produced for the current runtime source tree. The submission contains no target-project profile, revision, capability table, API-name classifier, error defaults, or infrastructure-port defaults.

It publishes `semantic-migration-planning/v3` evidence:

- `behavior-contracts.json`: source signatures, result-space obligations, and source-observable effect obligations.
- `state-transitions.json`: structural API transition obligations.
- `semantic-invariants.json`: source call-edge preservation assertions.
- `rust-migration-plan.json`: type/state/call mappings, source-derived external ports, and implementation obligations.
- `semantic-planning-verification.json`: independently recomputed denominators and gate results.

Target modules come from definition-file identity. A port is produced only for a call target that is not resolved as an internal definition, and it retains the original call-edge evidence. Names such as `set`, `get`, or any project prefix have no semantic effect.

All documents share planning run ID, parent analysis run ID, source digest, semantic IR digest, and input digest. Customized v1 and profile-driven v2 evidence are rejected and must be regenerated.

```powershell
python -m unittest work.runtime.tests.test_semantic_planning -v
python -m unittest discover -s work/runtime/tests -p "test_*.py"
```
