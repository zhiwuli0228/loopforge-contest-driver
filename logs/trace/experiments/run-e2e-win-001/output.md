# Output

- status: `BLOCKED_WITH_REPORT`
- source_root: `work/code/FlashDB`
- selected_source_readme: `work/code/FlashDB/README.md`
- resolved_project_root: `missing`
- rust_project: `work/output/flashDB_rust`
- cargo_toml: `work/output/flashDB_rust/Cargo.toml`
- semantic_audit_report: `work/logs/trace/c-to-rust/semantic-audit-report.md`
- source_analysis_gate: `False`
- cargo_build: `False`
- cargo_test: `False`
- unsafe_gate: `False`
- semantic_gate: `False`

## Summary

- The execution orchestrator analyzed `Introduction`, generated or refreshed `work/output/flashDB_rust`, executed the repair loop, and evaluated semantic/test-mapping gates before declaring READY.

## Blocking Details

- `source_layout_missing`: Expected source/test directories under E:\009workspace\codex\loopforge-contest-driver\work\code\FlashDB or an immediate child directory
- `source_files_missing`: No C source files were detected in the resolved source directories
- `test_files_missing`: No C test files were detected in the resolved test directories
- `semantic_template_missing`: The source tree does not expose a usable C source/test layout for migration
- `source_analysis_gate_failed`: failed stages: requirement, structure, capability, test_coverage
