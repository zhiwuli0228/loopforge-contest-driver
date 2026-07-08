## MODIFIED Requirements

### Requirement: Ten stage package assets
The system SHALL provide exactly ten stage package assets under `work/subagent/` named `dic-00-preflight.md` through `dic-09-finalize.md`, with a one-to-one mapping to the ordered design-implementation consistency stages. Each stage package MUST declare its stage objective, allowed inputs, required outputs, gate conditions, and failure-handling behavior using the same stage identifier used by the execution contract, and the declared package inputs MUST distinguish between `SUBMISSION_ROOT/README.md`, `SUBMISSION_ROOT/design-docs/`, `SUBMISSION_ROOT/code/`, and `SUBMISSION_ROOT/test-cases/` when those assets are relevant.

#### Scenario: Stage package lookup succeeds
- **WHEN** the orchestrator resolves stage `dic-05`
- **THEN** it finds exactly one corresponding `work/subagent/dic-05-*.md` stage package whose declared stage ID is `dic-05`, whose purpose matches traceability mapping, and whose allowed inputs align with the standard submission package contract

### Requirement: File-based handoff only
Each stage package SHALL require cross-stage handoff through declared files under `logs/trace/consistency/` rather than through unbounded orchestrator context accumulation. A stage MUST consume only declared upstream artifacts, summaries, and evidence references, and MUST emit its own stage summary plus any required structured artifacts before the next stage can proceed. Submission-package path resolution MUST happen through declared stage artifacts rather than by passing unbounded package context across stage boundaries.

#### Scenario: Downstream stage consumes upstream output
- **WHEN** `dic-06` starts after `dic-05` completes
- **THEN** it reads only the declared traceability artifacts, summaries, and evidence references produced under `logs/trace/consistency/` and does not require the orchestrator to inline the full upstream submission-package context

### Requirement: Read-only repair planning
The repair planning stage package SHALL be advisory only while the default workflow remains `analyze-only`. `dic-08` MUST generate repair recommendations, candidate patches, or verification suggestions as artifacts under declared output paths, MUST target mutable implementation paths under `SUBMISSION_ROOT/code/` when it names future patch locations, and MUST NOT require or assume write access to `SUBMISSION_ROOT/README.md`, `SUBMISSION_ROOT/design-docs/`, or `SUBMISSION_ROOT/test-cases/`.

#### Scenario: Repair plan is generated
- **WHEN** `dic-08` receives confirmed drift findings and risk classifications
- **THEN** it emits an advisory repair plan artifact and any related recommendations under declared non-source output paths without modifying immutable submission-package assets and without naming non-`code/` targets as valid future patch locations
