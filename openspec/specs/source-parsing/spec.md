## ADDED Requirements

### Requirement: Parse C source directory into structured inventory
The system SHALL parse a C/C++ source directory and produce a structured JSON inventory containing file list, public API declarations, type definitions, call graph, global state, and preprocessor variants.

#### Scenario: Successful parse of valid C source
- **WHEN** user runs `python tools.py parse-source --source-root /path/to/c-src --work-dir work`
- **THEN** system outputs JSON to stdout with `ok: true` and `data` containing source inventory fields (files, public_apis, types, call_graph, globals, preprocessor_variants)

#### Scenario: Source directory does not exist
- **WHEN** user runs `python tools.py parse-source --source-root /nonexistent`
- **THEN** system exits with code 1 and outputs JSON with `ok: false` and `error` describing the missing path

### Requirement: No pass/fail judgment on parse results
The system SHALL NOT make any pass/fail determination about the parsed source. It SHALL return raw data only.

#### Scenario: Empty source directory
- **WHEN** user points to a directory with no C files
- **THEN** system outputs JSON with `ok: true` and empty/zero-valued data fields (no error, no failure)

### Requirement: Output written to file when --output specified
The system SHALL write the inventory JSON to the specified file path instead of stdout when `--output` is provided.

#### Scenario: File output mode
- **WHEN** user runs `python tools.py parse-source --source-root /path --work-dir work --output work/source-inventory.json`
- **THEN** system writes inventory to `work/source-inventory.json` and outputs confirmation JSON to stdout
