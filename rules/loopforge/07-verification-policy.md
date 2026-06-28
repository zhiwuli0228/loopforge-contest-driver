# Verification Policy

## Current Milestone Scope

This repository version implements Java Maven verification in the runner and keeps other language flows as documented future paths.

## Java Maven Verification Order

1. `./mvnw test`
2. `mvn test`
3. `mvn -q -DskipTests package`

## Python Verification Order

1. `pytest`
2. `python -m pytest`
3. `python3 -m pytest`
4. `python -m compileall .`
5. `python3 -m compileall .`

## Node Verification Order

1. `npm test`
2. `npm run test`
3. `npm run build`

## Go Verification Order

1. `go test ./...`

## Behavior

- Verification failures must not hard block by default.
- The system should record gate events and continue into repair or degrade flows.
- Verification evidence must be preserved for final reporting.
