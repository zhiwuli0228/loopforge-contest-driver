## 1. Update authoritative workflow contracts

- [x] 1.1 Rewrite `work/skills/design-implementation-consistency/SKILL.md` so the default workflow is repair-and-verify rather than analyze-only.
- [x] 1.2 Update `work/profiles/examples/default-java-consistency.yaml` to enable bounded repair defaults, retry limits, and contest-ordered verification commands.
- [x] 1.3 Update `work/profiles/superpower/design-implementation-consistency-guards.yaml` to allow writes only to `SUBMISSION_ROOT/code/**` and explicitly declared support assets while keeping design and black-box assets immutable.
- [x] 1.4 Rewrite `work/profiles/superspec/design-implementation-consistency-stages.yaml` so stages `dic-00` through `dic-09` match acceptance-baseline extraction, repair execution, build verification, black-box verification, retry, and final verdict semantics.

## 2. Rewrite stage packages

- [x] 2.1 Update `work/subagent/dic-00-preflight.md` and `dic-01-design-intake.md` to validate mutable support-asset policy and extract the acceptance baseline from `README.md` plus `design-docs/`.
- [x] 2.2 Update `work/subagent/dic-02-source-inventory.md`, `dic-03-design-model.md`, and `dic-04-repair-plan.md` to produce implementation inventory, gap modeling, and bounded repair batches rather than read-only audit artifacts.
- [x] 2.3 Rewrite `work/subagent/dic-05-traceability-map.md` into the bounded repair execution stage with declared source-write scope and repair evidence outputs.
- [x] 2.4 Rewrite `work/subagent/dic-06-drift-analysis.md`, `dic-07-risk-classification.md`, and `dic-08-repair-plan.md` into build verification, black-box verification, and targeted regression repair stages.
- [x] 2.5 Update `work/subagent/dic-09-finalize.md` so it emits delivery verdicts (`SUBMISSION_PASSED`, `SUBMISSION_PARTIAL`, `SUBMISSION_BLOCKED`, `SUBMISSION_INVALID`) with preserved repair and verification evidence.

## 3. Update runtime and validation tooling

- [x] 3.1 Update `work/runtime/tools.py` and any supporting runtime modules so the command surface supports repair-aware artifacts, ordered verification classes, and final delivery verdict inputs.
- [x] 3.2 Update `work/runtime/loopforge_runner.py` and related orchestration helpers to execute the revised stage flow, including bounded retry from failed verification evidence.
- [x] 3.3 Update repository validation scripts such as `work/scripts/validate_consistency_contracts.py` and any subagent contract checks so they enforce the new repair-and-verify defaults and stage/output alignment.

## 4. Refresh repository instructions and defaults

- [x] 4.1 Update `README.md`, `INSTRUCTION.md`, and `work/README.md` so repository-level documentation describes contest-default repair-and-verify behavior instead of analyze-only auditing.
- [x] 4.2 Update `work/design/README.md` and any authoritative contract references so they treat `README.md` frozen API and verification commands as first-class acceptance baseline inputs.
- [x] 4.3 Audit default entrypoints and compatibility pointers to ensure no authoritative workflow asset still resolves to old `SOURCE_ROOT`, advisory-only repair, or analyze-only final-status semantics.

## 5. Verify the redesign

- [x] 5.1 Run `openspec status --change contest-repair-workflow-redesign` and confirm proposal, design, specs, and tasks are apply-ready.
- [x] 5.2 Run repository contract validation and fix any contract mismatches introduced by the workflow redesign.
- [x] 5.3 Execute a representative self-check or dry-run path to confirm the repaired workflow resolves `SUBMISSION_ROOT`, preserves immutable boundaries, and reports the new delivery verdict model correctly.
