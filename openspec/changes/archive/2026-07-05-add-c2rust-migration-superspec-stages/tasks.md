## 1. Create superspec header and metadata

- [x] 1.1 Write `superspec` top-level block: name, version, purpose, artifact_root (`logs/trace/c-to-rust`), final_report, subagent_required policy
- [x] 1.2 Write `artifact_metadata_contract` and `final_report_evidence` sections following `consistency-check-stages.yaml` convention

## 2. Define analysis stages (Phase 0-3)

- [x] 2.1 `00-preflight`: bind to `c2r-00-preflight.md`, input `INSTRUCTION.md` + `work/design/README.md`, no output file, gate `READY_FOR_UNDERSTAND`
- [x] 2.2 `01-understand`: bind to `c2r-01-understand.md`, input `SOURCE_ROOT/**`, output `logs/trace/c-to-rust/01-source-inventory.json`, gate `READY_FOR_DESIGN`
- [x] 2.3 `02-design`: bind to `c2r-02-design.md`, input prior inventory + `work/design/README.md`, output `openspec/changes/<name>/design.md`, gate `READY_FOR_SPEC`
- [x] 2.4 `03-spec`: bind to `c2r-03-spec.md`, input prior design + `SOURCE_ROOT/**`, output `openspec/changes/<name>/specs/`, gate `READY_FOR_PLAN`

## 3. Define planning and implementation stages (Phase 4-7)

- [x] 3.1 `04-plan`: bind to `c2r-04-plan.md`, input prior specs + design, output `openspec/changes/<name>/tasks.md` + `implement-plan.md`, gate `READY_FOR_IMPLEMENT`
- [x] 3.2 `05-implement`: bind to `c2r-05-implement.md`, `can_modify_code: true`, input prior plan + specs + `work/profiles/superpower/c-to-rust-migration-guards.yaml`, output `work/output/*/src/**/*.rs`, gate `READY_FOR_TEST`
- [x] 3.3 `06-test`: bind to `c2r-06-test.md`, `can_modify_code: true`, input prior src + test inventory, output `work/output/*/tests/**/*.rs`, gate `READY_FOR_REPAIR`
- [x] 3.4 `07-repair`: bind to `c2r-07-repair.md`, `can_modify_code: true`, input build/test errors from phases 5-6, output fixes to src/tests, gate `READY_FOR_SEMANTIC_AUDIT`

## 4. Define verification and finalize stages (Phase 8-10)

- [x] 4.1 `08-semantic-audit`: bind to `c2r-08-semantic-audit.md`, `can_modify_code: true`, input specs + `SOURCE_ROOT/**`, output invariant tests under `tests/`, gate `READY_FOR_QUALITY_GATES`
- [x] 4.2 `09-quality-gates`: bind to `c2r-09-quality-gates.md`, `can_modify_code: false`, input Rust project, no output file, gate `READY_FOR_FINALIZE`
- [x] 4.3 `10-finalize`: bind to `c2r-10-finalize.md`, `can_modify_code: false`, input all prior outputs, output `result/output.md` + `result/issues/00-summary.md`, gate `READY_FOR_EVALUATION`

## 5. Validate

- [x] 5.1 Verify YAML is syntactically valid
- [x] 5.2 Verify all `subagent` fields reference existing files in `work/subagent/`
- [x] 5.3 Verify zero project-specific content (no concrete project names, API names, or hardcoded paths)
- [x] 5.4 Verify `can_modify_code` is `true` only for phases 5, 6, 7, 8
