## MODIFIED Requirements

### Requirement: Heavy-output phases delegated to subagents

Phase 3 (Spec) and Phase 4 (Plan) SHALL be delegated to subagents via `work/subagent/c2r-03-spec.md` and `work/subagent/c2r-04-plan.md` respectively. The main agent MUST NOT write spec files or plan files inline. The main agent MUST NOT read subagent prompt files — it SHALL pass only the prompt file path reference and context variables.

#### Scenario: Phase 3 writes 10+ spec files
- **WHEN** the capability map contains 10 or more capabilities
- **THEN** all spec files are written inside the c2r-03-spec subagent's isolated context, and the main agent sees only a gate token (`PHASE_PASS` or `PHASE_BLOCKED`)

#### Scenario: Phase 4 writes implement-plan.md
- **WHEN** Phase 4 generates `tasks.md` and `implement-plan.md`
- **THEN** both files are written inside the c2r-04-plan subagent's isolated context, and the main agent sees only a gate token

#### Scenario: Main agent attempts inline spec write
- **WHEN** the main agent attempts to write a spec file directly instead of delegating to c2r-03-spec
- **THEN** the SKILL.md rules SHALL classify this as a delegation violation, and the action is forbidden

#### Scenario: Main agent reads subagent prompt file
- **WHEN** the main agent invokes `read` on any `work/subagent/c2r-*.md` file
- **THEN** the SKILL.md rules SHALL classify this as a delegation violation

### Requirement: Subagent prompt files referenced by path

The main agent SHALL reference subagent prompt files by their file path only. The main agent MUST NOT read subagent prompt files, fabricate inline prompts that embed execution steps, or duplicate subagent prompt content in the Agent tool `prompt` field. The Agent tool `prompt` field SHALL contain only the 2-3 line dispatch format: `Execute <path> with: KEY=VALUE ...`.

#### Scenario: Phase 5 dispatch
- **WHEN** dispatching a Phase 5 implementation batch
- **THEN** the Agent tool prompt field SHALL contain exactly the dispatch format with `BATCH_ID` and context variables

#### Scenario: Inline prompt fabrication detected
- **WHEN** the main agent constructs a prompt that includes embedded Rust type definitions, function signatures, or duplicated subagent execution steps
- **THEN** this SHALL be considered a context leak, and the SKILL.md rules SHALL forbid it

#### Scenario: Subagent prompt file read detected
- **WHEN** the main agent reads a `work/subagent/c2r-*.md` file into the main context
- **THEN** this SHALL be considered a delegation violation — the subagent reads its own prompt in isolation

## ADDED Requirements

### Requirement: SKILL.md Phase-Specific Notes are scheduling-only

The Phase-Specific Notes section of SKILL.md SHALL contain only: (a) subagent prompt file path, (b) list of output files, (c) gate expectation. Execution steps, detailed instructions, tool usage guidance, and rationale SHALL be removed and are delegated to the subagent prompt files.

#### Scenario: Phase 3 entry
- **WHEN** a reader inspects the Phase 3 entry in Phase-Specific Notes
- **THEN** it SHALL contain the subagent path, output pattern, and gate expectation only — no execution steps

#### Scenario: Phase 5 entry
- **WHEN** a reader inspects the Phase 5 entry in Phase-Specific Notes  
- **THEN** it SHALL contain the scheduling algorithm, subagent path, and output pattern only — no build/test/implementation steps
