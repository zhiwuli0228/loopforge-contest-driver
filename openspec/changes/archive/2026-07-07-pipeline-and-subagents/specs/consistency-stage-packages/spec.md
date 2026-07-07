## ADDED Requirements

### Requirement: Ten stage package assets
The system SHALL provide exactly ten stage package assets under `work/subagent/` named `dic-00-preflight.md` through `dic-09-finalize.md`, with a one-to-one mapping to the ordered design-implementation consistency stages. Each stage package MUST declare its stage objective, allowed inputs, required outputs, gate conditions, and failure-handling behavior using the same stage identifier used by the execution contract.

#### Scenario: Stage package lookup succeeds
- **WHEN** the orchestrator resolves stage `dic-05`
- **THEN** it finds exactly one corresponding `work/subagent/dic-05-*.md` stage package whose declared stage ID is `dic-05` and whose purpose matches traceability mapping

### Requirement: File-based handoff only
Each stage package SHALL require cross-stage handoff through declared files under `logs/trace/consistency/` rather than through unbounded orchestrator context accumulation. A stage MUST consume only declared upstream artifacts, summaries, and evidence references, and MUST emit its own stage summary plus any required structured artifacts before the next stage can proceed.

#### Scenario: Downstream stage consumes upstream output
- **WHEN** `dic-06` starts after `dic-05` completes
- **THEN** it reads only the declared traceability artifacts, summaries, and evidence references produced under `logs/trace/consistency/` and does not require the orchestrator to inline the full upstream working context

### Requirement: Gate and failure preservation semantics
Every stage package SHALL define an explicit gate outcome and a failure-preservation path. When a stage cannot satisfy its gate, it MUST write the failure status, preserved evidence, and next-step disposition to its declared trace path so the orchestrator can either stop safely or continue to finalization when `always_finalize=true`.

#### Scenario: Stage gate fails with preserved evidence
- **WHEN** `dic-04` cannot produce a valid implementation model
- **THEN** the stage package writes its failure reason, available extraction evidence, and gate result to the declared trace location so execution can halt or finalize without losing auditability

### Requirement: Read-only repair planning
The repair planning stage package SHALL be advisory only. `dic-08` MUST generate repair recommendations, candidate patches, or verification suggestions as artifacts under declared output paths, and MUST NOT require or assume write access to business source files while the default workflow remains `analyze-only`.

#### Scenario: Repair plan is generated
- **WHEN** `dic-08` receives confirmed drift findings and risk classifications
- **THEN** it emits an advisory repair plan artifact and any related recommendations under declared non-source output paths without modifying files under `SOURCE_ROOT`

### Requirement: Finalization consumes partial pipeline results
The finalization stage package SHALL be able to consume successful and failed intermediate stage outputs to produce a terminal audit summary. When earlier stages fail but finalization is still invoked, `dic-09` MUST summarize completed stages, blocked stages, preserved evidence paths, and outstanding risks without inventing missing evidence.

#### Scenario: Finalization runs after an earlier failure
- **WHEN** execution invokes `dic-09` after `dic-06` failed and preserved its trace artifacts
- **THEN** the finalization package produces a final summary that reports the failure boundary, references the preserved evidence, and distinguishes unavailable downstream outputs from confirmed findings
