# Implementation Plan: fix-c2r-pipeline-brainstorm

## Overview

Fix the V2 C-to-Rust migration pipeline by: (1) restructuring the Understand phase into 3 bounded-context sub-stages, (2) relaxing SuperPower guards to allow analysis artifact output, (3) creating new subagent prompts with mandatory structured output, (4) redesigning all templates to prevent agent laziness, (5) interleaving implementation and testing per capability.

**Output**: Updated YAML configs, 3 new subagent files, 5 updated subagent files, 6 redesigned templates, 1 updated schema.

---

## Batch 1: SuperSpec + SuperPower Config Updates

**Capability**: superspec-stage-restructure + superpower-guard-relaxation

**Spec reference**: specs/superspec-stage-restructure/spec.md, specs/superpower-guard-relaxation/spec.md

**Files to modify**:
- `work/profiles/superspec/c-to-rust-migration-stages.yaml`
- `work/profiles/superpower/c-to-rust-migration-guards.yaml`

**Implementation tasks**:

1. Replace `01-understand` stage with `01a-inventory`, `01b-capability-analysis`, `01c-synthesize` in stages YAML
2. Update 02-design, 03-spec, 04-plan input lists to include `01c-capability-map.json`
3. Replace `understand` guard with `01a-inventory`, `01b-capability`, `01c-synthesize` in guards YAML
4. Set correct `allowed_fs` write patterns and `forbidden` lists per guard

**Verification**:
```bash
python -c "import yaml; yaml.safe_load(open('work/profiles/superspec/c-to-rust-migration-stages.yaml'))"
python -c "import yaml; yaml.safe_load(open('work/profiles/superpower/c-to-rust-migration-guards.yaml'))"
```

**Completion criteria**:
- [ ] Both YAML files parse without errors
- [ ] 01a, 01b, 01c stages are defined with correct gates
- [ ] 02-04 inputs include capability map
- [ ] Guards allow writes to logs/ and openspec/ but forbid source modification

---

## Batch 2: New Subagent Files (01a, 01b, 01c)

**Capability**: brainstorm-subagents

**Spec reference**: specs/brainstorm-subagents/spec.md

**Files to create**:
- `work/subagent/c2r-01a-inventory.md`
- `work/subagent/c2r-01b-capability.md`
- `work/subagent/c2r-01c-synthesize.md`

**File to archive**:
- `work/subagent/c2r-01-understand.md` → `work/subagent/archived/c2r-01-understand.md`

**Implementation tasks**:

1. Create 01a-inventory.md: discover test dirs, run parse-source, verify JSON fields, status summary (≤ 1.5K tokens)
2. Create 01b-capability.md: deep per-module analysis, autonomous capability identification, mandatory output sections, fill-in prompts (≤ 5K tokens per instance)
3. Create 01c-synthesize.md: read 01b summaries, merge cross-module capabilities, assign priorities, output capability-map.json (≤ 3K tokens)
4. Move old c2r-01-understand.md to archived/

**Verification**:
- Read each new file and check: no HTML comments, all sections have content, autonomous judgment directives present

**Completion criteria**:
- [ ] 01a prompt ≤ 1.5K tokens, only mechanical steps
- [ ] 01b has "MUST independently decide" directive, mandatory output template with fill-in prompts
- [ ] 01c has "Do NOT read C source files" directive, JSON output structure defined
- [ ] Old 01-understand.md archived

---

## Batch 3: Downstream Subagent Updates (02-06)

**Capability**: capability-driven-test-interleave

**Spec reference**: specs/capability-driven-test-interleave/spec.md

**Files to modify**:
- `work/subagent/c2r-02-design.md`
- `work/subagent/c2r-03-spec.md`
- `work/subagent/c2r-04-plan.md`
- `work/subagent/c2r-05-implement.md`
- `work/subagent/c2r-06-test.md`

**Implementation tasks**:

1. c2r-02-design: add step to read capability map, require Capability Mapping section in design output
2. c2r-03-spec: change from per-module to per-capability, read capability map IDs, one spec per capability
3. c2r-04-plan: define batches by capability, each batch = implement + test, order by dependency graph
4. c2r-05-implement: add "write unit tests" step, update gate to require cargo test pass
5. c2r-06-test: re-scope to integration tests, add C test coverage verification, add "do not duplicate" directive

**Verification**:
- Read each modified file and verify the key changes are present

**Completion criteria**:
- [ ] 02-design reads capability map as input
- [ ] 03-spec creates one spec per capability ID
- [ ] 04-plan uses dependency graph for batch order
- [ ] 05-implement gate requires cargo test pass
- [ ] 06-test scope is integration/cross-capability only

---

## Batch 4: Template Redesign

**Capability**: anti-lazy-templates

**Spec reference**: specs/anti-lazy-templates/spec.md

**Files to modify**:
- `openspec/schemas/c2r-migration/templates/spec.md`
- `openspec/schemas/c2r-migration/templates/tasks.md`
- `openspec/schemas/c2r-migration/templates/design.md`
- `openspec/schemas/c2r-migration/templates/implement-plan.md`
- `openspec/schemas/c2r-migration/templates/verification-report.md`

**Files to create**:
- `openspec/schemas/c2r-migration/templates/capability-map.json`

**Implementation tasks**:

1. Redesign spec.md: mandatory fields, 3 scenario slots per requirement, invariants section, no HTML comments
2. Redesign tasks.md: capability-level batch groups, spec references, dependency declarations
3. Redesign design.md: Capability Mapping table, mandatory Alternatives Considered
4. Redesign implement-plan.md: function-level detail, data structure table, unit test list, completion checklist
5. Redesign verification-report.md: per-batch results table, repair log subsections
6. Create capability-map.json template with sentinel values

**Verification**:
- Search all templates for `<!--` — must be zero occurrences
- Each template has at least 3 mandatory structured fields

**Completion criteria**:
- [ ] Zero HTML comments across all templates
- [ ] Each template has fill-in prompts, not optional comments
- [ ] capability-map.json has `REQUIRED_FIELD_NOT_SET` sentinels

---

## Batch 5: Schema Update + Final Verification

**Capability**: anti-lazy-templates

**Spec reference**: specs/anti-lazy-templates/spec.md

**Files to modify**:
- `openspec/schemas/c2r-migration/schema.yaml`

**Implementation tasks**:

1. Add `brainstorm` artifact to schema (id, generates, template, instruction, requires)
2. Update `design.requires` to include brainstorm
3. Update `specs.requires` to include brainstorm
4. Run `openspec validate fix-c2r-pipeline-brainstorm`

**Verification**:
```bash
openspec validate fix-c2r-pipeline-brainstorm
```

**Completion criteria**:
- [ ] schema.yaml parses without errors
- [ ] brainstorm artifact is defined with template reference
- [ ] design and specs artifacts require brainstorm
- [ ] openspec validate passes

---

## Batch Dependency Graph

```
Batch 1 (config YAMLs)
  └─► Batch 2 (new subagents 01a/01b/01c)
       └─► Batch 3 (updated subagents 02-06)
            ├─► Batch 4 (templates)
            └─► Batch 5 (schema + verify)
                 (depends on 4)
```

Batches 4 and 5 can be developed in parallel after Batch 3.
