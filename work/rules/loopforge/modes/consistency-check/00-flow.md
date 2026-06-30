# Consistency Check Flow

## Applies To

- design versus implementation analysis
- contract drift checks
- API or schema consistency review
- cases where repair is optional and analysis is the default output

## Flow

`DESIGN_READ -> IMPLEMENTATION_MAPPING -> TRACEABILITY_MATRIX -> DRIFT_REPORT -> REPAIR_PLAN -> OPTIONAL_CONTROLLED_REPAIR -> VERIFICATION_EVIDENCE -> FINAL_REPORT`

## Phase Outcomes

- `DESIGN_READ`: extract the intended behavior or structure
- `IMPLEMENTATION_MAPPING`: map the design onto actual code
- `TRACEABILITY_MATRIX`: record requirement-to-implementation links
- `DRIFT_REPORT`: classify mismatches, omissions, and ambiguities
- `REPAIR_PLAN`: define the smallest acceptable repair scope and verification path
- `OPTIONAL_CONTROLLED_REPAIR`: apply bounded repair only if explicitly enabled
- `VERIFICATION_EVIDENCE`: run configured verification or record a degraded reason with evidence
- `FINAL_REPORT`: deliver findings, controlled changes, and artifact references

## Mandatory Sequence Rules

- Read frozen design sources before inspecting candidate implementation files.
- Build explicit design-to-code mappings before labeling drift.
- Produce a repair plan before changing any code.
- Run only `verification.commands` from `loopforge.config.yaml`.
- Keep all execution artifacts under `logs/trace/plan/` or another runner-compatible directory referenced by the final report.

