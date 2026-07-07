## 1. Existing Contract Audit

- [x] 1.1 Inventory the existing consistency profiles, C2Rust Skill/stage/guard conventions, and Change 1 defaults that can be reused without carrying migration-specific semantics.
- [x] 1.2 Record the authoritative versus template/compatibility role of existing `consistency-check*.yaml` files and resolve conflicting defaults.

## 2. Main Skill Contract

- [x] 2.1 Create `work/skills/design-implementation-consistency/SKILL.md` with required inputs, profile resolution, ordered stage orchestration, file handoff, evidence requirements, and final statuses.
- [x] 2.2 Add focused reference documents for stage handoff, evidence completeness, and adapter-neutral behavior, and link them from the main Skill only where needed.
- [x] 2.3 Verify the Skill defaults to analyze-only execution and rejects confirmed findings that lack the required evidence contract.

## 3. Default Java Profile

- [x] 3.1 Create `work/profiles/examples/default-java-consistency.yaml` with automatic language detection, Java default adapter, Generic fallback, analysis dimensions, and framework/source patterns.
- [x] 3.2 Define profile-level verification command selection and read-only execution defaults consistent with `work/loopforge.config.yaml`.
- [x] 3.3 Validate both Java-selected and Generic-fallback profile resolution without changing downstream model or artifact paths.

## 4. Staged Execution Definition

- [x] 4.1 Create `work/profiles/superspec/design-implementation-consistency-stages.yaml` with ordered stage IDs `dic-00` through `dic-09` and their declared responsibilities.
- [x] 4.2 Declare each stage's file inputs, outputs under `logs/trace/consistency/`, gate conditions, and fail-soft/finalization behavior.
- [x] 4.3 Verify every stage consumes only declared predecessor artifacts and that failed gates preserve evidence and can reach final reporting when configured.

## 5. Permission Guards

- [x] 5.1 Create `work/profiles/superpower/design-implementation-consistency-guards.yaml` with deny-by-default policy and per-stage read/write allowlists.
- [x] 5.2 Encode unconditional source-write denial for analyze-only execution and restrict allowed writes to each stage's declared artifacts and final result paths.
- [x] 5.3 Exercise negative guard cases for unauthorized `SOURCE_ROOT` writes and cross-stage artifact writes, confirming denials are recorded as evidence.

## 6. Contract Validation

- [x] 6.1 Add or run structural validation for YAML/Markdown syntax, required stage count/order, profile adapter resolution, and guard coverage.
- [x] 6.2 Cross-check stage IDs, input/output paths, adapter names, execution defaults, and final statuses across the Skill, Java profile, superspec, guards, and Change 1 configuration.
- [x] 6.3 Document the produced contracts and the handoff assumptions required by Change 3 Core modeling and later pipeline implementation.
