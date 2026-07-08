## MODIFIED Requirements

### Requirement: Ten stage package assets
The system SHALL provide exactly ten stage package assets under `work/subagent/` named `dic-00-preflight.md` through `dic-09-finalize.md`, with a one-to-one mapping to the ordered design-implementation consistency stages. Each stage package MUST declare its stage objective, allowed inputs, required outputs, gate conditions, and failure-handling behavior using the same stage identifier used by the execution contract, and the declared package inputs MUST distinguish between `SUBMISSION_ROOT/README.md`, `SUBMISSION_ROOT/design-docs/`, `SUBMISSION_ROOT/code/`, mutable support assets, and `SUBMISSION_ROOT/test-cases/` when those assets are relevant. The stage-package sequence MUST support acceptance-baseline extraction, repair execution, build verification, black-box verification, targeted retry, and final verdict assembly.

#### Scenario: Stage package lookup succeeds
- **WHEN** the orchestrator resolves stage `dic-05`
- **THEN** it finds exactly one corresponding `work/subagent/dic-05-*.md` stage package whose declared stage ID is `dic-05`, whose purpose matches bounded repair execution, and whose allowed inputs align with the standard submission package contract

### Requirement: File-based handoff only
Each stage package SHALL require cross-stage handoff through declared files under `logs/trace/consistency/` rather than through unbounded orchestrator context accumulation. A stage MUST consume only declared upstream artifacts, summaries, and evidence references, and MUST emit its own stage summary plus any required structured artifacts before the next stage can proceed. Submission-package path resolution MUST happen through declared stage artifacts rather than by passing unbounded package context across stage boundaries, even when a downstream stage applies repairs or retries verification.

#### Scenario: Downstream stage consumes upstream output
- **WHEN** `dic-06` starts after `dic-05` completes
- **THEN** it reads only the declared repair outputs, summaries, and evidence references produced under `logs/trace/consistency/` and does not require the orchestrator to inline the full upstream submission-package context

### Requirement: Gate and failure preservation semantics
Every stage package SHALL define an explicit gate outcome and a failure-preservation path. When a stage cannot satisfy its gate, it MUST write the failure status, preserved evidence, and next-step disposition to its declared trace path so the orchestrator can either stop safely, continue to targeted retry, or continue to finalization when `always_finalize=true`.

#### Scenario: Stage gate fails with preserved evidence
- **WHEN** `dic-07` cannot produce a passing black-box verification result
- **THEN** the stage package writes its failure reason, verification evidence, and gate result to the declared trace location so execution can route to targeted retry or finalize without losing auditability

### Requirement: Read-only repair planning
The repair-planning and retry stages SHALL support executable contest repair rather than advisory-only output while preserving immutable package baselines. `dic-04` MUST generate bounded repair batches and verification intent as artifacts under declared output paths, `dic-05` MUST consume those batches and apply repairs only within declared mutable targets, and `dic-08` MUST consume failed verification evidence to perform targeted regression repair or declare an explicit retry blockage. None of these stages may require or assume write access to `SUBMISSION_ROOT/README.md`, `SUBMISSION_ROOT/design-docs/`, or `SUBMISSION_ROOT/test-cases/`.

#### Scenario: Repair batches are executed
- **WHEN** `dic-04` produces repair batches and `dic-05` receives them
- **THEN** the repair stage applies bounded changes only to declared mutable targets, emits repair evidence under the declared non-source trace outputs, and preserves any blocked patch attempt as execution evidence

#### Scenario: Targeted retry is generated from failed verification
- **WHEN** `dic-08` receives failed build or black-box verification evidence
- **THEN** it limits further repair scope to the failing interfaces, rules, or build paths referenced by that evidence and does not reopen unrelated submission-package scope

### Requirement: Finalization consumes partial pipeline results
The finalization stage package SHALL be able to consume successful and failed intermediate stage outputs to produce a terminal delivery summary. When earlier stages fail but finalization is still invoked, `dic-09` MUST summarize completed stages, blocked stages, preserved evidence paths, remaining risks, verification outcomes, and the final delivery verdict without inventing missing evidence.

#### Scenario: Finalization runs after an earlier failure
- **WHEN** execution invokes `dic-09` after `dic-07` failed and preserved its trace artifacts
- **THEN** the finalization package produces a final summary that reports the failure boundary, references the preserved evidence, distinguishes unavailable downstream outputs from confirmed findings, and records whether the submission is passed, partial, blocked, or invalid
