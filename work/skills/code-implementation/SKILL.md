---
name: code-implementation
description: Implement minimal, safe, maintainable code changes from a repair plan. Use this skill during patch implementation stages, especially when a SuperSpec stage declares a coding skill for controlled repair execution.
---

# Code Implementation Skill

Implement code changes from a validated repair plan.

Keep changes minimal, safe, traceable, and aligned with the current task scope.

Preserve this stable interface so LoopForge can replace or enhance the skill later without changing orchestration.

## Mandatory Inputs

Read:

1. `logs/trace/consistency/04-repair-plan.md`
2. `profiles/superpower/consistency-check-guards.yaml`
3. the target files explicitly listed in the repair plan

Read these references when present and relevant:

1. `skills/code-implementation/references/java-secure-coding.md`
2. `skills/code-implementation/references/minimal-patch-rules.md`
3. `skills/code-implementation/references/patch-summary-template.md`

## Execution Rules

1. Modify only files allowed by the repair plan.
2. Modify only files allowed by SuperPower.
3. Keep the patch minimal.
4. Preserve existing architecture and coding style.
5. Avoid unrelated refactoring.
6. Avoid broad rewrites.
7. Preserve existing public API behavior unless the repair plan requires a change.
8. Preserve existing transaction boundaries unless explicitly required.
9. Preserve existing validation, security, and error handling behavior unless the repair plan explicitly changes it.
10. Write a patch summary after modification.

## Forbidden Actions

Do not modify:

- `INSTRUCTION.md`
- `loopforge.config.yaml`
- `skills/**`
- `rules/**`
- `profiles/**`
- `runtime/**`
- `scripts/**`
- design documents or frozen inputs under `SOURCE_ROOT`

Do not execute:

- `git add`
- `git commit`
- `git push`
- pull request creation

Do not:

- perform unrelated refactoring
- rename unrelated classes or methods
- rewrite large modules
- change unrelated business behavior
- bypass validation to make verification pass
- modify configuration to hide implementation failures

## Secure Coding Baseline

When modifying implementation code:

1. Validate external inputs before business processing.
2. Prefer allowlist checks for enum-like fields.
3. Validate numeric ranges where required by the design.
4. Preserve authorization and access-control checks.
5. Avoid unsafe dynamic execution and command execution.
6. Avoid unsafe query construction with untrusted input.
7. Avoid logging sensitive values.
8. Avoid returning raw exception details to callers.
9. Avoid swallowing exceptions silently.
10. Avoid hardcoded credentials or secrets.

## Patch Summary Output

After patch implementation, write:

`logs/trace/consistency/05-patch-summary.md`

The patch summary must include:

1. applied skill path
2. modified files
3. repair-plan items implemented
4. files intentionally not modified
5. security-sensitive areas touched
6. validation changes
7. error handling changes
8. logging changes
9. deviations from the repair plan, if any
10. final gate status

Allowed gate values:

- `READY_FOR_VERIFICATION`
- `BLOCKED_WITH_REPORT`
- `DEGRADED_BUT_READY_FOR_VERIFICATION`

## Replacement Contract

This skill is intentionally generic.

A stronger coding skill may replace this skill later without changing LoopForge orchestration, as long as it preserves:

1. the same input contract
2. the same output artifact path
3. the same gate values
4. the same write-scope restrictions
5. the requirement to write `logs/trace/consistency/05-patch-summary.md`

