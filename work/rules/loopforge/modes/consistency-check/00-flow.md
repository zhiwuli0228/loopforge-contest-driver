# Consistency Check Flow

## Applies To

- design versus implementation analysis
- contract drift checks
- API or schema consistency review
- cases where repair is optional and analysis is the default output

## Flow

`DESIGN_READ -> IMPLEMENTATION_MAPPING -> TRACEABILITY_MATRIX -> DRIFT_REPORT -> OPTIONAL_CONTROLLED_REPAIR -> FINAL_REPORT`

## Phase Outcomes

- `DESIGN_READ`: extract the intended behavior or structure
- `IMPLEMENTATION_MAPPING`: map the design onto actual code
- `TRACEABILITY_MATRIX`: record requirement-to-implementation links
- `DRIFT_REPORT`: classify mismatches, omissions, and ambiguities
- `OPTIONAL_CONTROLLED_REPAIR`: apply bounded repair only if explicitly enabled
- `FINAL_REPORT`: deliver findings and any controlled changes
