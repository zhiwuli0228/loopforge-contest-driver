## ADDED Requirements

### Requirement: Count unsafe code lines in Rust project
The system SHALL scan all `.rs` files in a Rust project directory and count `unsafe` keyword occurrences and total code lines, computing a ratio.

#### Scenario: Normal Rust project
- **WHEN** user runs `python tools.py check-unsafe --project-dir /path/to/rust-project`
- **THEN** system outputs JSON with `ok: true`, `data.total_files`, `data.unsafe_lines`, `data.total_code_lines`, `data.ratio`, and `data.per_file` array with per-file breakdown

#### Scenario: Project with no Rust files
- **WHEN** the project directory contains no `.rs` files
- **THEN** system outputs JSON with `ok: true` and `data.ratio: 0`, empty `per_file` array

### Requirement: No pass/fail threshold judgment
The system SHALL NOT determine whether the unsafe ratio is acceptable. It SHALL return the numeric ratio only.

#### Scenario: High unsafe ratio
- **WHEN** the project has 50% unsafe code
- **THEN** system outputs `ok: true` with `data.ratio: 0.5`; no error, no exit code change

### Requirement: Output to file option
The system SHALL support `--output` to write the unsafe ratio JSON to a file.

#### Scenario: File output
- **WHEN** user specifies `--output work/unsafe-ratio.json`
- **THEN** system writes results to the specified file
