# Minimal Patch Rules

## Scope

A patch must be directly traceable to `04-repair-plan.md`.

Do not modify files that are not listed in the repair plan unless the repair plan explicitly permits dependent changes.

## Allowed Changes

Allowed changes include:

1. small validation additions
2. small condition checks
3. controlled error handling
4. minimal helper method extraction when necessary
5. minimal test-support changes if allowed by the repair plan
6. small mapper or DTO changes if directly required

## Forbidden Changes

Forbidden changes include:

1. unrelated refactoring
2. broad formatting-only changes
3. package restructuring
4. class renaming
5. method signature changes not required by the repair plan
6. dependency upgrades
7. framework replacement
8. security check removal
9. configuration changes to bypass verification

## Patch Discipline

Before editing a file, confirm:

1. the file is listed in the repair plan
2. the file is allowed by SuperPower
3. the change is necessary for a listed drift
4. the change can be described in the patch summary

After editing a file, record:

1. what changed
2. why it changed
3. which repair-plan item it implements
4. whether it touches validation, logging, error handling, data access, or security-sensitive behavior
