# Maven Adapter

## Command Authority

- Maven verification commands come only from `loopforge.config.yaml`.
- Do not guess `mvn test`, `mvn package`, `mvn verify`, wrapper commands, profiles, or extra flags.
- Respect the configured command order exactly as written.

## Project Recognition

- Detect Maven from `pom.xml`, `mvnw`, or `mvnw.cmd`.
- Distinguish between a single-module build and a root aggregator with `<modules>`.
- Inspect parent POM relationships, packaging type, declared modules, and inter-module dependencies before proposing a repair.

## Multi-module Execution Rules

- Support module-scoped verification commands such as `mvn -pl <module> -am ...` when supplied by configuration.
- When a target module depends on shared code, allow repairs in the target module and the smallest required common module set.
- Do not widen the repair scope just because the Maven workspace contains many modules.

## Verification Discipline

- Prefer compile or package verification before broader test execution when that is how the human configured the task.
- If verification is blocked by missing infrastructure, external services, credentials, or environment-only dependencies, keep the configured command unchanged and record a degraded reason.
- Do not modify static LoopForge root assets, `code/docs/`, or verification commands to force a green build.
- Do not bypass a real business defect by changing only tests or by disabling meaningful assertions.

## Failure Recording

- For every failed verification attempt, preserve:
  - the exact command
  - the working directory
  - the exit code
  - stdout/stderr tail evidence
  - the reasoned failure classification
- If multiple configured commands exist, stop on the first success and otherwise report all failed attempts.
