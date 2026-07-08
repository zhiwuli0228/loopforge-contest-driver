## MODIFIED Requirements

### Requirement: Deterministic adapter selection and fallback
The system SHALL provide a language-adapter contract that selects `java` as the default adapter when Java project detection succeeds within `SUBMISSION_ROOT/code/` and falls back to `generic` when Java detection does not satisfy the declared criteria. Adapter selection MUST emit auditable evidence describing the signals that triggered the selected adapter or the reasons the preferred adapter was rejected, and the evidence MUST show that detection was scoped to the standard package's mutable implementation area rather than the package root at large.

#### Scenario: Java adapter is selected
- **WHEN** source inventory detects declared Java project signals such as supported build files, source layout, or framework markers inside `SUBMISSION_ROOT/code/`
- **THEN** the system selects the `java` adapter, records the matched signals as selection evidence, and schedules implementation extraction with the Java adapter contract

#### Scenario: Generic fallback is selected
- **WHEN** `SUBMISSION_ROOT/code/` does not satisfy the Java adapter's detection criteria or required Java scanning inputs are unavailable
- **THEN** the system selects the `generic` adapter, records the fallback reason as selection evidence, and continues the pipeline without changing downstream artifact names

### Requirement: Java adapter canonical extraction
The system SHALL provide a Java adapter that scans the mutable implementation area of the standard submission package, including project structure, HTTP entrypoints, data shapes, configuration surfaces, dependencies, and test artifacts under `SUBMISSION_ROOT/code/`, then normalizes those findings into the canonical implementation model defined by the Core capability. Java-specific details MUST be attached only as optional extension metadata and MUST NOT replace the shared object kinds or evidence fields.

#### Scenario: Java adapter discovers an endpoint contract
- **WHEN** the Java adapter identifies an HTTP-exposed implementation construct in source code or configuration under `SUBMISSION_ROOT/code/`
- **THEN** it emits a canonical implementation object of the shared entrypoint kind with source evidence and may attach Java-specific annotation or framework metadata as optional extensions

### Requirement: Generic adapter partial extraction
The system SHALL provide a Generic adapter that can extract implementation objects from files, symbols, configuration artifacts, and tests within `SUBMISSION_ROOT/code/` even when language-specific semantics are incomplete. Generic extraction MUST preserve partial coverage by marking uncertain objects with explicit confidence or partial-status metadata instead of silently dropping them.

#### Scenario: Generic adapter scans a non-Java repository
- **WHEN** the selected adapter is `generic` for a repository whose mutable implementation area under `SUBMISSION_ROOT/code/` lacks supported Java signals
- **THEN** the adapter emits canonical implementation objects for discovered files, symbols, configuration surfaces, and tests, and marks any approximate classifications with explicit uncertainty metadata
