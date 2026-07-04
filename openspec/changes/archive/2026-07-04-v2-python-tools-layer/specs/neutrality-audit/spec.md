## ADDED Requirements

### Requirement: Scan files for forbidden terms
The system SHALL scan specified file paths for occurrences of forbidden terms and return a list of hits.

#### Scenario: No forbidden terms found
- **WHEN** user runs `python tools.py neutrality-audit --paths '["src/main.rs"]' --forbidden-terms '["hardcoded_name"]'`
- **THEN** system outputs JSON with `ok: true`, `data.hits: []`, `data.files_scanned: 1`

#### Scenario: Forbidden terms found
- **WHEN** a file contains a forbidden term
- **THEN** system outputs JSON with `ok: true`, `data.hits` containing entries with `file`, `line`, `term`, `context` (surrounding line)

### Requirement: Support glob patterns in paths
The system SHALL accept glob patterns in `--paths` and expand them to match files.

#### Scenario: Glob expansion
- **WHEN** user specifies `--paths '["src/**/*.rs"]'`
- **THEN** system expands the glob and scans all matching `.rs` files

### Requirement: No gate judgment on scan results
The system SHALL NOT determine whether the scan results constitute a pass or fail. It SHALL return the raw hit list only.

#### Scenario: Many hits found
- **WHEN** 50 occurrences of forbidden terms are found
- **THEN** system outputs `ok: true` with all 50 hits; no error, no exit code change
