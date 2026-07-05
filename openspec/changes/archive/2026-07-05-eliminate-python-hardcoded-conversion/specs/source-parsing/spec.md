## ADDED Requirements

### Requirement: Parse result must not contain body_kind or translation_status

The parse-source command output SHALL NOT include `body_kind`, `translation_status`, or `body_value` fields for any function entry. These fields belong to the deleted Python hardcoded conversion layer.

#### Scenario: Clean function data
- **WHEN** user runs `python tools.py parse-source --source-root /path/to/c-src`
- **THEN** each function entry in the output SHALL contain only: name, file, line, return_type, params, decl_kind (declaration/definition), and call_edges
- **THEN** no `body_kind` field SHALL appear in any function entry
- **THEN** no `translation_status` field SHALL appear in any function entry
- **THEN** no `body_value` field SHALL appear in any function entry

### Requirement: Parse must remain zero-judgment

The parse-source command SHALL NOT classify functions as "supported" or "unsupported" for translation. It SHALL return raw structural data only.

#### Scenario: No translation judgment
- **WHEN** parse-source processes any C file
- **THEN** it SHALL extract function signatures, types, and call relationships
- **THEN** it SHALL NOT emit any `unsupported_reason` field
- **THEN** it SHALL NOT emit any `can_translate` or equivalent boolean judgment

## REMOVED Requirements

### Requirement: SUPPORTED_BODY_KINDS constant
**Reason**: body_kind classification was a Python hardcoded conversion artifact. Agent reads C source directly and does not need pre-computed body classification.
**Migration**: Remove SUPPORTED_BODY_KINDS from source_analysis.py. No replacement needed.

### Requirement: Function body analysis for translation
**Reason**: Python-based C function body analysis (classifying loops, assignments, return patterns) was only used by the hardcoded c2rust_project_generator.py. Agent performs this understanding directly from C source.
**Migration**: Remove body analysis logic from source_analysis.py. Remove body_kind/body_value fields from parse-source output.
