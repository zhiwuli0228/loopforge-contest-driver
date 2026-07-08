## Why

The current authoritative workflow is optimized for analyze-only design-implementation drift auditing, but the active contest requires the driver to repair implementation code, preserve frozen design and API contracts, keep the project buildable, and prove progress with black-box verification. As a result, the repository's default workflow contract now conflicts with the contest's required delivery behavior.

## What Changes

- **BREAKING** Change the default contest workflow semantics from analyze-only consistency auditing to repair-and-verify execution for standard submission packages.
- Redefine the staged workflow so it extracts an acceptance baseline from `README.md` plus `design-docs/`, performs bounded code repair under `SUBMISSION_ROOT/code/`, runs build verification, runs black-box verification, and supports targeted retry loops before finalization.
- Replace advisory-only repair planning with an executable repair stage and a bounded regression-repair stage.
- Update runtime reporting so final verdicts reflect delivery outcomes such as pass, partial pass, blocked, or invalid submission rather than audit-only finding states.
- Expand submission-package contract handling to recognize contest-level frozen API and error-code baselines from `README.md`, plus narrowly scoped mutable support assets such as `maven-settings.xml` when required for verification.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `consistency-execution-contracts`: Change the authoritative skill, profile defaults, stage ordering semantics, write boundaries, and terminal statuses from analyze-only auditing to contest repair-and-verify delivery.
- `consistency-stage-packages`: Redefine stage package responsibilities so later stages execute bounded repairs, build verification, black-box verification, targeted retry, and final verdict assembly.
- `consistency-runtime-reporting`: Replace the analyze-only runtime command surface and reporting assumptions with repair-aware verification and delivery verdict reporting.
- `consistency-submission-package-contract`: Clarify that `README.md` contains authoritative frozen API, error-code, and verification-command baselines and define narrow mutable exceptions for contest support assets needed to complete verification.

## Impact

Affected areas include `work/skills/design-implementation-consistency/`, default profile and guard contracts under `work/profiles/`, stage definitions under `work/profiles/superspec/`, stage packages under `work/subagent/`, runtime orchestration and reporting under `work/runtime/` and `work/scripts/`, and repository-level contest run instructions in `README.md` and `INSTRUCTION.md`.
