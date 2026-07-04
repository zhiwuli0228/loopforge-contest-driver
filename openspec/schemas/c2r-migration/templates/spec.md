## ADDED Requirements

### Requirement: [capability-id] — [Requirement Name]

[Describe the behavior this requirement mandates. Reference the C source file and line numbers that define this behavior. Example: "The CRC32 function SHALL compute a 32-bit checksum using the standard table-driven algorithm as defined in fdb_utils.c:45-67."]

C source reference: [file:line]

#### Scenario: Normal path

- **GIVEN** [precondition state — what must be true before the operation]
- **WHEN** [operation is performed — the exact function call or event]
- **THEN** [expected result — return value, state change, side effects]

#### Scenario: Error path

- **GIVEN** [error precondition — invalid input, resource exhaustion, corrupted state]
- **WHEN** [operation is performed]
- **THEN** [error handling behavior — error return value, state preservation, logging]

#### Scenario: Boundary condition

- **GIVEN** [boundary state — empty, full, max value, min value, edge case]
- **WHEN** [operation is performed]
- **THEN** [expected boundary behavior]

[If a scenario type is truly not applicable, write: "N/A — [specific reason why this scenario type does not apply to this requirement]"]

---

### Invariants

- **INV-[capability-id]-001**: [State an invariant. Before/after a specific operation, a specific state SHALL hold. Example: "After `set_status`, the status byte at the written index SHALL equal FDB_BYTE_WRITTEN and SHALL NOT revert to FDB_BYTE_ERASED."]
- **INV-[capability-id]-002**: [State another invariant. Minimum 1 invariant per capability.]
- **INV-[capability-id]-003**: [If no additional invariants, write: "N/A — [reason]"]
