## ADDED Requirements

### Requirement: Write structured data to formatted report file
The system SHALL accept structured JSON data via stdin or `--data` parameter and write it as a formatted markdown report to the specified output path.

#### Scenario: Write report from inline data
- **WHEN** user runs `python tools.py write-report --result-dir result --data '{"status":"complete","metrics":{}}'`
- **THEN** system writes a formatted markdown file to `result/output.md` containing the data

#### Scenario: Write report from stdin
- **WHEN** user pipes JSON into `python tools.py write-report --result-dir result`
- **THEN** system reads JSON from stdin and writes formatted report to `result/output.md`

### Requirement: Support custom report template
The system SHALL accept a `--template` parameter specifying a markdown template file.

#### Scenario: Custom template
- **WHEN** user specifies `--template templates/report.md`
- **THEN** system uses the template to format the output, substituting placeholders with data values

#### Scenario: Default template
- **WHEN** user omits `--template`
- **THEN** system uses a built-in default template that presents data as key-value sections

### Requirement: Return output path on success
The system SHALL output JSON to stdout confirming the written file path.

#### Scenario: Successful write
- **WHEN** report is written successfully
- **THEN** system outputs `{"ok": true, "data": {"output_path": "result/output.md"}}`
