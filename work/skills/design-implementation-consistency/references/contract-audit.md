# Contract Audit

## Reusable Inputs

- `work/archived/c-to-rust/skills/c-to-rust-migration/SKILL.md`
  Historical input only. It informed input ordering, explicit write scope, and final status discipline before archival.
- `work/archived/c-to-rust/profiles/superspec/c-to-rust-migration-stages.yaml`
  Historical input only. It informed stable ordered stage identifiers and declared handoff artifacts before archival.
- `work/archived/c-to-rust/profiles/superpower/c-to-rust-migration-guards.yaml`
  Historical input only. It informed deny-by-default guard structure before archival.
- `work/loopforge.config.yaml`
  Reuse `consistency-check`, `always_finalize`, `fail_soft`, and unattended execution defaults.

## Legacy Roles

- `work/profiles/examples/default-java-consistency.yaml`
  Authoritative default contract for this repository.
- `work/profiles/examples/consistency-check.yaml`
  Compatibility example only. It illustrates the old generic shape and must not override the default contract.
- `work/profiles/examples/java-consistency-check.yaml`
  Compatibility example only. It retains older Java-oriented wording and must not override the default contract.
- `work/profiles/templates/consistency-check.yaml`
  Template only. It remains a reusable starter and is non-authoritative by definition.
- `work/profiles/superspec/consistency-check-stages.yaml`
  Legacy eight-stage repair-capable reference. It is not the default staged contract for consistency analysis.
- `work/profiles/superpower/consistency-check-guards.yaml`
  Legacy repair-capable guard reference. It allows source writes and therefore cannot serve the analyze-only default.

## Conflicting Defaults Resolved Here

- Default profile path resolves to `profiles/examples/default-java-consistency.yaml`.
- Default adapter resolves to `java`.
- Fallback adapter resolves to `generic`.
- Default execution resolves to `analyze-only`.
- Default source-write policy resolves to deny all writes under `SOURCE_ROOT`.
- Default stage graph resolves to `dic-00` through `dic-09`.
