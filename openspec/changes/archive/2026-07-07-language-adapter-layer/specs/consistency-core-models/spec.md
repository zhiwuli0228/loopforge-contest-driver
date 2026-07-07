## MODIFIED Requirements

### Requirement: Canonical implementation model
The system SHALL provide a language-neutral implementation model that can represent modules, symbols, entrypoints, data shapes, configuration surfaces, dependencies, and test artifacts produced by any adapter. Every implementation object MUST include shared identity, kind, summary, and implementation evidence fields, and the model MUST preserve adapter provenance, normalization status, and optional extension metadata without allowing adapter-specific details to replace the common fields.

#### Scenario: Java adapter discovers controller-like behavior
- **WHEN** a language adapter detects a framework-specific implementation construct such as an HTTP entrypoint
- **THEN** the adapter records it as a neutral implementation-model object with shared fields, implementation evidence, adapter provenance, and may attach framework-specific metadata only as optional extensions

#### Scenario: Generic fallback emits a partial implementation object
- **WHEN** the generic adapter can identify a likely implementation object but cannot assign a fully precise language-specific classification
- **THEN** the implementation model records the object with the shared kind structure, explicit normalization or confidence metadata, and evidence sufficient for downstream traceability or drift analysis
