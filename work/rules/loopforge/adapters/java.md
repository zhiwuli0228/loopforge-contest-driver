# Java Adapter

## Detection Scope

- Detect a Java codebase from `pom.xml`, `src/main/java`, `src/test/java`, or a stable Java package tree under `code/`.
- When both Java and another language are present, follow `task.language.primary` from `loopforge.config.yaml` and treat the rest as supporting context only.
- For consistency-check runs, treat design documents, API contracts, package layout, and persistence model definitions as first-class evidence.

## Maven Multi-module Recognition

- If a root `pom.xml` contains `<modules>`, treat the repository as a Maven multi-module workspace.
- Identify the root aggregator, target business module, and only the directly required dependency modules.
- Recognize per-module source roots such as `module/src/main/java`, `module/src/test/java`, `module/src/main/resources`, and `module/pom.xml`.
- Read parent-child `pom.xml` relationships before proposing changes to build logic, dependency scope, or packaging.

## Implementation Mapping Expectations

- Map design requirements onto the smallest relevant set of Java artifacts.
- Recognize common Spring or layered structures including:
  - `Controller`
  - `Service`
  - `ServiceImpl`
  - `Repository`, `Mapper`, or DAO-style persistence classes
  - `Entity`, `PO`, `DO`, `DTO`, `VO`
  - request/response payload classes
  - shared `Result`, `R`, `ErrorCode`, `BizCodeEnum`, and exception types in common modules
- Treat annotations, request mappings, validation rules, transaction boundaries, and conversion logic as evidence, not noise.

## Controlled Repair Scope

- Keep repairs inside the target module plus the smallest necessary shared module set, typically a `common` module required by the target flow.
- Do not spread a local repair into unrelated modules such as other services, gateways, generators, or admin applications unless the design evidence proves they are in scope.
- Prefer minimal edits to existing classes over introducing new abstraction layers.
- Do not perform large-scale package moves, broad renames, dependency graph cleanup, or style-only rewrites.
- Do not alter frozen design documents to make implementation appear compliant.
- Do not add Git operations such as `commit`, `push`, `merge`, or PR creation.

## Consistency-check Behavior

- Build an explicit trace from design statements to Java implementation points before classifying drift.
- Separate confirmed drift from ambiguous design gaps.
- If repair is enabled, modify only code under `code/` and preserve traceability to the triggering drift item.
- If verification fails, record the exact command source, exit code, and failure reason instead of guessing alternate Java entrypoints.
