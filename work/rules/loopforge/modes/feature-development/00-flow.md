# Feature Development Flow

## Applies To

- new user-facing features
- new CLI capabilities
- internal engineering capabilities that still require acceptance criteria
- security or reliability features that start from a requirement rather than a failing test

## Flow

`REQUIREMENT_EXPAND -> BRAINSTORM -> DESIGN_DRAFT -> TESTCASE_DESIGN -> IMPLEMENTATION_PLAN -> CODE_GENERATE -> VERIFY -> FINAL_REPORT`

## Phase Outcomes

- `REQUIREMENT_EXPAND`: convert the request into explicit scope, boundaries, and acceptance criteria
- `BRAINSTORM`: explore options and choose the smallest defensible design
- `DESIGN_DRAFT`: capture interfaces, behavior, and constraints before editing code
- `TESTCASE_DESIGN`: define how success will be checked
- `IMPLEMENTATION_PLAN`: choose a concrete patch sequence
- `CODE_GENERATE`: apply the implementation only inside `SOURCE_ROOT`
- `VERIFY`: run configured commands
- `FINAL_REPORT`: summarize scope, evidence, and remaining gaps

