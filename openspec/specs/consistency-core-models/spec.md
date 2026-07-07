# consistency-core-models Specification

## Purpose
Define the adapter-neutral core models that every design-implementation consistency stage shares for design extraction, implementation extraction, traceability, drift analysis, severity assessment, and final reporting.

## Requirements
### Requirement: Canonical design model
The system SHALL provide a language-neutral design model that can represent design capabilities, components, interfaces, data contracts, constraints, and declared relationships without encoding framework-specific terminology. Every design object SHALL include a stable identifier, object kind, human-readable name, summary, and one or more evidence references back to the design source.

#### Scenario: Design intake extracts a component contract
- **WHEN** the design analysis stages identify a component, endpoint contract, or business rule in the design source
- **THEN** the extracted artifact is recorded as a design-model object with a stable ID, neutral kind, descriptive fields, and evidence references to the originating design content

### Requirement: Canonical implementation model
The system SHALL provide a language-neutral implementation model that can represent modules, symbols, entrypoints, data shapes, configuration surfaces, dependencies, and test artifacts produced by any adapter. Every implementation object MUST include shared identity, kind, summary, and implementation evidence fields, and the model MUST preserve adapter provenance, normalization status, and optional extension metadata without allowing adapter-specific details to replace the common fields.

#### Scenario: Java adapter discovers controller-like behavior
- **WHEN** a language adapter detects a framework-specific implementation construct such as an HTTP entrypoint
- **THEN** the adapter records it as a neutral implementation-model object with shared fields, implementation evidence, adapter provenance, and may attach framework-specific metadata only as optional extensions

#### Scenario: Generic fallback emits a partial implementation object
- **WHEN** the generic adapter can identify a likely implementation object but cannot assign a fully precise language-specific classification
- **THEN** the implementation model records the object with the shared kind structure, explicit normalization or confidence metadata, and evidence sufficient for downstream traceability or drift analysis

### Requirement: Traceability and evidence contract
The system SHALL provide shared traceability and evidence models that can link design objects to implementation objects, record coverage state, and capture both positive matches and unresolved gaps. Every traceability link and drift candidate MUST reference the design evidence and implementation evidence or explicitly record why one side is unavailable.

#### Scenario: Coverage mapping identifies a missing implementation
- **WHEN** traceability analysis finds a design object with no corresponding implementation object
- **THEN** the system records a gap entry with the originating design evidence and an explicit missing-implementation status that downstream drift analysis can consume

### Requirement: Drift severity and report model
The system SHALL provide a shared drift taxonomy, severity policy, and report model for confirmed findings, summaries, and rollups. Each reported finding MUST include a taxonomy category, severity, status, traceability context, and evidence references so that final reports remain auditable across adapters and stages.

#### Scenario: Final report emits a confirmed inconsistency
- **WHEN** drift analysis confirms that an implementation diverges from a traced design expectation
- **THEN** the report model emits a finding that includes its taxonomy category, severity, supporting traceability context, and both design and implementation evidence references
