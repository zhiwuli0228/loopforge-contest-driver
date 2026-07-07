## ADDED Requirements

### Requirement: Deterministic adapter selection and fallback
The system SHALL provide a language-adapter contract that selects `java` as the default adapter when Java project detection succeeds and falls back to `generic` when Java detection does not satisfy the declared criteria. Adapter selection MUST emit auditable evidence describing the signals that triggered the selected adapter or the reasons the preferred adapter was rejected.

#### Scenario: Java adapter is selected
- **WHEN** source inventory detects declared Java project signals such as supported build files, source layout, or framework markers
- **THEN** the system selects the `java` adapter, records the matched signals as selection evidence, and schedules implementation extraction with the Java adapter contract

#### Scenario: Generic fallback is selected
- **WHEN** the source does not satisfy the Java adapter's detection criteria or required Java scanning inputs are unavailable
- **THEN** the system selects the `generic` adapter, records the fallback reason as selection evidence, and continues the pipeline without changing downstream artifact names

### Requirement: Java adapter canonical extraction
The system SHALL provide a Java adapter that scans project structure, HTTP entrypoints, data shapes, configuration surfaces, dependencies, and test artifacts, then normalizes those findings into the canonical implementation model defined by the Core capability. Java-specific details MUST be attached only as optional extension metadata and MUST NOT replace the shared object kinds or evidence fields.

#### Scenario: Java adapter discovers an endpoint contract
- **WHEN** the Java adapter identifies an HTTP-exposed implementation construct in source code or configuration
- **THEN** it emits a canonical implementation object of the shared entrypoint kind with source evidence and may attach Java-specific annotation or framework metadata as optional extensions

### Requirement: Generic adapter partial extraction
The system SHALL provide a Generic adapter that can extract implementation objects from files, symbols, configuration artifacts, and tests even when language-specific semantics are incomplete. Generic extraction MUST preserve partial coverage by marking uncertain objects with explicit confidence or partial-status metadata instead of silently dropping them.

#### Scenario: Generic adapter scans a non-Java repository
- **WHEN** the selected adapter is `generic` for a repository without supported Java signals
- **THEN** the adapter emits canonical implementation objects for discovered files, symbols, configuration surfaces, and tests, and marks any approximate classifications with explicit uncertainty metadata

### Requirement: Adapter output compatibility
Every language adapter SHALL emit implementation artifacts, evidence references, and adapter provenance that are directly consumable by traceability analysis without adapter-specific reshaping. The emitted artifact set MUST use the same shared object names, relationship semantics, and evidence structure regardless of which adapter produced it.

#### Scenario: Traceability consumes adapter output
- **WHEN** traceability analysis receives implementation artifacts from either the Java or Generic adapter
- **THEN** it can load the artifacts through the shared implementation-model contract without branching on adapter-specific field names
