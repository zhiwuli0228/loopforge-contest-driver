# Subagent Lease Rule

## Objective

Constrain code-writing scope for either the main agent or any coding subagent.

## Output File

`.loopforge/leases/lease-001.md`

## Required Template

```markdown
# Write Lease

## Lease ID

lease-001

## Assigned Task

## Allowed Files

- path/to/file

## Forbidden Files

- pom.xml
- build.gradle
- package-lock.json
- yarn.lock
- src/main/resources/**
- .github/**
- .git/**

## Max Changed Files

3

## Max Diff Lines

250

## Allowed Commands

- mvn test
- ./mvnw test
- mvn -q -DskipTests package

## Required Report

.loopforge/subagents/lease-001-report.md
```

## Enforcement

- Do not change forbidden files unless the task explicitly requires it and the lease is updated.
- Do not create a second independent workflow.
- Always require a subagent report after coding work.
