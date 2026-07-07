## MODIFIED Requirements

### Requirement: Cross-artifact contract consistency
The Skill, default Java profile, stage definition, guard definition, language-adapter capability, stage-package capability, and runtime-reporting capability SHALL use consistent stage identifiers, adapter names, execution defaults, artifact paths, and Core model terminology. Existing generic consistency profiles SHALL be explicitly aligned, referenced as templates, or marked non-authoritative so that the repository exposes one unambiguous default contract, every stage that emits a shared model artifact SHALL reference the same canonical model names used by the Core and language-adapter capabilities, every declared stage output SHALL be writable under both the superspec and the matching stage guard, the authoritative runtime commands SHALL resolve to the same final trace and result paths used by the staged workflow, and no authoritative consistency-check entrypoint SHALL require or implicitly resolve to archived `c-to-rust` or `c2r` assets.

#### Scenario: Contract artifacts are validated
- **WHEN** repository validation compares the authoritative contract artifacts
- **THEN** every referenced stage exists, every stage ID resolves to one stage package, every stage output is permitted by its guard, Java fallback resolves to `generic`, adapter identifiers align across profile and stage definitions, all default execution settings remain read-only, shared model artifact names align with the Core, language-adapter, and stage-package capabilities, runtime/report outputs align to `logs/trace/consistency/`, `logs/trace/final-report.md`, `result/output.md`, and `result/issues/00-summary.md`, and no authoritative skill/profile/stage/guard/runner reference resolves to archived C2Rust assets

#### Scenario: Legacy consistency or migration assets remain present
- **WHEN** legacy consistency-adjacent or C2Rust migration assets remain in the repository for historical compatibility
- **THEN** their role is documented as archived or non-authoritative so they cannot silently override the default consistency contract, contradict the adapter-selection contract, diverge from the declared stage-package handoff model, or reintroduce legacy migration paths into the authoritative runtime/report flow
