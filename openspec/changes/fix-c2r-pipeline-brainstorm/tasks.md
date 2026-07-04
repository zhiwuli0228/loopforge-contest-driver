## 1. SuperSpec Stage Restructure

关联 spec: superspec-stage-restructure

- [ ] 1.1 Update `work/profiles/superspec/c-to-rust-migration-stages.yaml`: replace `01-understand` with `01a-inventory`, `01b-capability-analysis`, `01c-synthesize`
- [ ] 1.2 Define 01a-inventory stage: id, subagent path, input/output, gates, can_modify_code=false
- [ ] 1.3 Define 01b-capability-analysis stage: parallel=true, parallelism_key from inventory modules, input/output, gates
- [ ] 1.4 Define 01c-synthesize stage: input from all 01b outputs, output capability-map.json, gates
- [ ] 1.5 Update 02-design input to include `01c-capability-map.json`
- [ ] 1.6 Update 03-spec input to include `01c-capability-map.json`
- [ ] 1.7 Update 04-plan input to include `01c-capability-map.json`
- [ ] 1.8 Verify YAML syntax: `python -c "import yaml; yaml.safe_load(open('work/profiles/superspec/c-to-rust-migration-stages.yaml'))"`

## 2. SuperPower Guard Relaxation

关联 spec: superpower-guard-relaxation

- [ ] 2.1 Remove old `understand` phase guard entry from `work/profiles/superpower/c-to-rust-migration-guards.yaml`
- [ ] 2.2 Add `01a-inventory` guard: allowed_fs read ** + write logs/trace/c-to-rust/**
- [ ] 2.3 Add `01b-capability` guard: allowed_fs read ** + write logs/trace/c-to-rust/capabilities/**
- [ ] 2.4 Add `01c-synthesize` guard: allowed_fs read ** + write logs/trace/c-to-rust/** + write openspec/changes/*/
- [ ] 2.5 Verify all three new guards forbid: modify C source, modify tools.py, modify profiles
- [ ] 2.6 Verify YAML syntax

## 3. Brainstorm Subagents (New)

关联 spec: brainstorm-subagents

- [ ] 3.1 Create `work/subagent/c2r-01a-inventory.md`: mechanical parse-source, verify JSON fields, context ≤ 1.5K tokens
- [ ] 3.2 Create `work/subagent/c2r-01b-capability.md`: per-module deep analysis with mandatory output sections, autonomous judgment directives, context ≤ 5K tokens
- [ ] 3.3 Create `work/subagent/c2r-01c-synthesize.md`: cross-module synthesis, capability merging, priority assignment, JSON output template, context ≤ 3K tokens
- [ ] 3.4 Archive old `work/subagent/c2r-01-understand.md` (move to `work/subagent/archived/` or delete — it is replaced by 01a+01b+01c)

## 4. Downstream Subagent Updates

关联 spec: capability-driven-test-interleave

- [ ] 4.1 Update `work/subagent/c2r-02-design.md`: add step to read capability map, add Capability Mapping section requirement to design output
- [ ] 4.2 Update `work/subagent/c2r-03-spec.md`: change from per-module to per-capability spec creation, use capability map to drive file list
- [ ] 4.3 Update `work/subagent/c2r-04-plan.md`: define batches by capability ID from capability map, each batch = implement + test, dependency order follows capability dependency graph
- [ ] 4.4 Update `work/subagent/c2r-05-implement.md`: add mandatory "write unit tests for this batch" step, gate requires cargo test pass in addition to cargo build pass
- [ ] 4.5 Update `work/subagent/c2r-06-test.md`: re-scope to integration/cross-capability tests, add C test coverage verification step, add "do not duplicate unit tests" directive

## 5. Anti-Lazy Templates

关联 spec: anti-lazy-templates

- [ ] 5.1 Redesign `openspec/schemas/c2r-migration/templates/spec.md`: mandatory structured fields, 3 scenario slots per requirement, invariants section, no HTML comments
- [ ] 5.2 Redesign `openspec/schemas/c2r-migration/templates/tasks.md`: capability-level batch grouping, spec references, dependency declarations, implement+test checkboxes per batch
- [ ] 5.3 Redesign `openspec/schemas/c2r-migration/templates/design.md`: add Capability Mapping table between Goals and Decisions, mandatory Alternatives Considered per decision
- [ ] 5.4 Redesign `openspec/schemas/c2r-migration/templates/implement-plan.md`: mandatory function-level details, data structure mapping table, unit test list, completion criteria checklist per batch
- [ ] 5.5 Redesign `openspec/schemas/c2r-migration/templates/verification-report.md`: per-batch results table with build/test/unsafe columns, repair log subsections, capability coverage summary
- [ ] 5.6 Create `openspec/schemas/c2r-migration/templates/capability-map.json`: JSON template for 01c output with `REQUIRED_FIELD_NOT_SET` sentinel values

## 6. Schema Update

关联 spec: anti-lazy-templates

- [ ] 6.1 Update `openspec/schemas/c2r-migration/schema.yaml`: add `brainstorm` artifact (id, generates capability-map.json, template, instruction, requires [])
- [ ] 6.2 Update artifact dependencies: design.requires += brainstorm, specs.requires += brainstorm

## 7. Verification

- [ ] 7.1 Verify all YAML files parse without syntax errors
- [ ] 7.2 Verify all new subagent markdown files are valid and complete (no placeholder sections)
- [ ] 7.3 Verify old `understand` guard key is fully removed from guards YAML
- [ ] 7.4 Verify old `c2r-01-understand.md` is archived
- [ ] 7.5 Run `openspec validate fix-c2r-pipeline-brainstorm` and fix any issues
