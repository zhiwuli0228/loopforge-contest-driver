## ADDED Requirements

### Requirement: Understand phases may write analysis artifacts

The SuperPower guards at `work/profiles/superpower/c-to-rust-migration-guards.yaml` SHALL allow the understand phases (01a, 01b, 01c) to write analysis artifacts while maintaining strict protection of source code, tools, and profiles.

#### Scenario: 01a-inventory has write permission for logs

- **WHEN** the `01a-inventory` guard is defined
- **THEN** `allowed_fs` SHALL include `write` operation with `path_pattern: "logs/trace/c-to-rust/**"`
- **AND** `forbidden` SHALL include: modify C source files, modify tools.py, modify profiles
- **AND** `forbidden` SHALL NOT include "any write operations"

#### Scenario: 01b-capability has write permission for capabilities directory

- **WHEN** the `01b-capability` guard is defined
- **THEN** `allowed_fs` SHALL include `write` operation with `path_pattern: "logs/trace/c-to-rust/capabilities/**"`
- **AND** `forbidden` SHALL include: modify C source files, modify tools.py, modify profiles
- **AND** `forbidden` SHALL NOT include "any write operations"

#### Scenario: 01c-synthesize has write permission for logs and openspec

- **WHEN** the `01c-synthesize` guard is defined
- **THEN** `allowed_fs` SHALL include `write` operation with `path_pattern: "logs/trace/c-to-rust/**"`
- **AND** `allowed_fs` MAY include `write` operation with `path_pattern: "openspec/changes/*/"`
- **AND** `forbidden` SHALL include: modify C source files, modify tools.py, modify profiles, modify work/output/

#### Scenario: Source code remains protected across all understand phases

- **WHEN** any understand phase (01a, 01b, 01c) attempts to write to `SOURCE_ROOT/**`
- **THEN** the operation SHALL be forbidden
- **AND** the guard SHALL enforce this by not listing `SOURCE_ROOT` in `allowed_fs` write operations

#### Scenario: Existing guards for other phases are unchanged

- **WHEN** phases 02 through 10 are evaluated
- **THEN** their SuperPower guards SHALL remain identical to the current definitions
- **AND** only phases 01a, 01b, 01c SHALL have modified guards

### Requirement: Guard definitions map to the three new phase names

The guards YAML SHALL define separate entries for `01a-inventory`, `01b-capability`, and `01c-synthesize` replacing the single `understand` entry.

#### Scenario: Guard phase keys match stage IDs

- **WHEN** the guards YAML is inspected
- **THEN** it SHALL contain phase keys `01a-inventory`, `01b-capability`, and `01c-synthesize`
- **AND** it SHALL NOT contain the old `understand` phase key
- **AND** each phase key SHALL match exactly the `id` field of the corresponding stage in the SuperSpec YAML
