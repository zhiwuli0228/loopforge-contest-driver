## Context

The repository's current authoritative contract treats design-implementation consistency as an analyze-only audit workflow. That contract was appropriate when the primary outcome was evidence, drift reports, and advisory repair suggestions. The active contest, however, requires the driver to repair business code under `SUBMISSION_ROOT/code/`, preserve frozen design and API baselines from `README.md` and `design-docs/`, keep the project buildable, and prove conformance using black-box tests under `test-cases/`.

The mismatch is structural rather than cosmetic. The current skill, default profile, stage packages, runtime commands, and final statuses all assume a read-only execution posture. The redesign therefore needs to change the default contest workflow semantics while preserving the standard submission package model, stage-scoped handoff discipline, adapter neutrality outside Java-specific extraction, and immutable design/test boundaries.

## Goals / Non-Goals

**Goals:**

- Make the default authoritative workflow repair-and-verify rather than analyze-only.
- Preserve `README.md` and `design-docs/` as the authoritative acceptance baseline, with `README.md` elevated as a first-class frozen API and verification contract.
- Allow bounded writes to `SUBMISSION_ROOT/code/**` and narrowly scoped contest support assets required to execute verification.
- Split verification into build/project verification and black-box verification so the workflow reflects the contest's required Maven command order.
- Retain ten stages, file-based handoff, evidence preservation, and fail-soft finalization.
- Change final statuses from audit-oriented outcomes to delivery-oriented verdicts.

**Non-Goals:**

- Replace the standard submission package layout or reintroduce arbitrary repository adaptation.
- Make `design-docs/`, `test-cases/`, or frozen `README.md` baselines mutable.
- Remove Java-first adapter detection or generic fallback support.
- Define every code-level implementation detail for runtime helpers or subagent prompts in this design artifact.

## Decisions

### Decision 1: Keep the existing capability family and change its default execution semantics

The repository will continue to use the `design-implementation-consistency` capability family and its existing paths, but its default behavior will change from audit-only to contest repair-and-verify delivery.

Rationale:
- This minimizes repository churn and preserves already established entrypoints.
- Existing contracts already model the correct authoritative inputs, stage IDs, and trace locations.
- The core issue is default behavior, write scope, and end-state semantics, not capability naming.

Alternatives considered:
- Introduce a brand-new capability family such as `design-implementation-consistency-repair`. Rejected because it would duplicate most existing contracts and create a longer migration path.
- Keep analyze-only as the default and add repair as an optional profile. Rejected because the current contest requires repair behavior by default, and leaving the wrong default visible invites invalid runs.

### Decision 2: Redefine the ten-stage pipeline around acceptance-baseline extraction, repair execution, and verification loops

The workflow will retain stages `dic-00` through `dic-09`, but the later-stage responsibilities will change to:

- `dic-00`: submission preflight
- `dic-01`: acceptance baseline extraction
- `dic-02`: implementation inventory
- `dic-03`: gap modeling
- `dic-04`: repair batch planning
- `dic-05`: repair execution
- `dic-06`: build and project-owned verification
- `dic-07`: black-box verification
- `dic-08`: targeted regression repair
- `dic-09`: final verdict assembly

Rationale:
- Keeping ten stages preserves cross-artifact alignment and existing orchestration structure.
- The new stage meanings directly map to the contest's delivery expectations.
- Separating `dic-06` and `dic-07` mirrors the required install-then-black-box flow in the contest README.

Alternatives considered:
- Collapse repair and verification into fewer stages. Rejected because it hides the contest-required command ordering and makes evidence harder to preserve.
- Keep advisory repair planning as a terminal stage. Rejected because the contest requires applied fixes, not recommendations.

### Decision 3: Treat `README.md` as an acceptance-baseline source, not just package metadata

The redesigned workflow will explicitly extract frozen API URLs, methods, request and response fields, success statuses, error-code contracts, modification boundaries, and verification commands from `SUBMISSION_ROOT/README.md`, then combine that with `design-docs/` into a canonical acceptance baseline.

Rationale:
- The contest README contains binding contract material that is not merely explanatory.
- Many failure modes in this repository stem from underweighting README constraints compared with design-docs and source code.
- A merged baseline model gives later stages a clearer target than a generic design summary.

Alternatives considered:
- Continue treating README as a lightweight entry contract only. Rejected because it would leave frozen API and command semantics under-modeled.
- Push README-specific extraction entirely into Java adapter logic. Rejected because the README baseline is package-contract logic, not language-adapter logic.

### Decision 4: Allow bounded write access to `code/**` and narrowly scoped verification support assets

The guard model will continue to deny writes by default, but the default contest profile will enable patching and code generation within `SUBMISSION_ROOT/code/**`. The contract will also allow narrow exceptions for contest support assets such as `SUBMISSION_ROOT/maven-settings.xml` when such mutation is necessary to execute authoritative verification without altering business behavior.

Rationale:
- The contest requires code repair and build/test execution.
- `maven-settings.xml` is explicitly mentioned by the contest README as environment support, not a design baseline.
- Narrow exceptions preserve the important immutable boundary around design and black-box assets.

Alternatives considered:
- Permit writes anywhere under `SUBMISSION_ROOT`. Rejected because it weakens the contest boundary too far.
- Forbid changes to support assets like Maven settings. Rejected because it could block valid verification in constrained environments.

### Decision 5: Change final statuses to delivery verdicts

The final workflow will report terminal statuses such as `SUBMISSION_PASSED`, `SUBMISSION_PARTIAL`, `SUBMISSION_BLOCKED`, and `SUBMISSION_INVALID`, while still preserving traceability, drift evidence, and verification details.

Rationale:
- Audit-only states such as `FINALIZED_WITH_FINDINGS` do not answer the evaluator's actual question: did the repaired submission satisfy the contest contract?
- Delivery verdicts better align runtime reporting, result summaries, and implementation priorities.

Alternatives considered:
- Keep old statuses and reinterpret them informally. Rejected because it would preserve semantic ambiguity in both code and reports.

## Risks / Trade-offs

- [Spec churn across multiple capabilities] -> Mitigation: keep the existing capability family and only change the requirements that control defaults, stage semantics, and reporting.
- [Runtime implementation may lag behind the new contract] -> Mitigation: define stage and runtime deltas explicitly in tasks so the authoritative assets can be updated in dependency order.
- [Allowing writes to support assets could widen mutation scope] -> Mitigation: restrict exceptions to explicitly named support files and keep design, README contract text, and black-box tests immutable.
- [Delivery verdicts may reduce visibility into detailed drift analysis] -> Mitigation: preserve the existing evidence and traceability artifacts as inputs to the final verdict rather than removing them.
- [Keeping the existing capability name may still cause some conceptual ambiguity] -> Mitigation: rewrite the authoritative skill, profile, and README text so the default behavior is unmistakable.

## Migration Plan

1. Update the OpenSpec requirements for execution contracts, stage packages, runtime reporting, and submission package boundaries.
2. Rewrite the authoritative skill, default profile, superspec stages, and superpower guards to match the new execution defaults and write boundaries.
3. Rewrite stage packages `dic-01` through `dic-09` to reflect acceptance-baseline extraction, repair execution, build verification, black-box verification, retry, and final verdict behavior.
4. Update runtime orchestration and report rendering so the declared command surface and final statuses match the new specs.
5. Refresh repository-level instructions and run validation so the new default contract is the only authoritative path.

Rollback strategy:
- Revert the change set and restore the previous archived audit-oriented contract if the repository must temporarily return to analyze-only semantics.

## Open Questions

- Should `maven-settings.xml` be the only mutable support asset exception in the first iteration, or should the contract allow a small class of toolchain support files?
- Should `dic-08` permit more than one bounded retry round by default, or should the first implementation hard-cap retries at one until runtime behavior is proven stable?
