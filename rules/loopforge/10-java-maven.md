# Java Maven Rule

## Detection

Identify a Java Maven project when any of the following exist:

- `pom.xml`
- `mvnw`
- `mvnw.cmd`

## Verification Intent

When verification support is enabled, prefer:

1. `./mvnw test`
2. `mvn test`
3. `mvn -q -DskipTests package`

## Current Status

Project detection and Maven verification execution are implemented in the runner.
