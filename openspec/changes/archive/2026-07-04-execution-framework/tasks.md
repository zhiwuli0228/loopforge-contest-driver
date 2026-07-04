## 1. Schema Creation

- [x] 1.1 Run `openspec schema init c2r-migration --artifacts proposal,specs,design,tasks --default` to scaffold project-local schema
- [x] 1.2 Edit `openspec/schemas/c2r-migration/schema.yaml` to add `implement-plan` artifact (requires: tasks, generates: implement-plan.md)
- [x] 1.3 Edit `openspec/schemas/c2r-migration/schema.yaml` to add `verification-report` artifact (requires: implement-plan, generates: verification-report.md)
- [x] 1.4 Edit `openspec/schemas/c2r-migration/schema.yaml` to set `apply.requires: [verification-report]` and `apply.tracks: tasks.md`

## 2. Artifact Templates

- [x] 2.1 Create `openspec/schemas/c2r-migration/templates/implement-plan.md` with sections: Batch Overview, Batch Details, Execution Order
- [x] 2.2 Create `openspec/schemas/c2r-migration/templates/verification-report.md` with sections: Build Results, Test Results, Repair Log, Semantic Audit, Quality Gates, Final Assessment

## 3. SuperPower Guards File

- [x] 3.1 Create directory `work/profiles/superpower/`
- [x] 3.2 Create `work/profiles/superpower/c-to-rust-migration-guards.yaml` with top-level `phases` key and all 11 phase definitions (preflight through finalize)

## 4. Validation

- [x] 4.1 Run `openspec schema validate c2r-migration` — verify no errors
- [x] 4.2 Run `openspec schemas` — verify c2r-migration appears in list
- [x] 4.3 Verify SuperPower YAML parses without errors
- [x] 4.4 Verify no project-specific paths in either file
