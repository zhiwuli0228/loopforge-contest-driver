# Output

- status: `BLOCKED_WITH_REPORT`
- source_root: `.code/FlashDB`
- selected_source_readme: `.code/FlashDB/README.md`
- resolved_project_root: `.code/FlashDB`
- rust_project: `flashDB_rust`
- cargo_build: `True`
- cargo_test: `True`
- unsafe_gate: `True`
- semantic_gate: `False`

## Summary

- The execution orchestrator analyzed `FlashDB Local Fallback`, generated or refreshed `flashDB_rust`, executed the repair loop, and evaluated semantic/test-mapping gates before declaring READY.

## Blocking Details

- `semantic_gate_failed`: semantic checks failed: semantic_claim_gate
