## ADDED Requirements

### Requirement: Heavy-output phases delegated to subagents

Phase 3 (Spec) and Phase 4 (Plan) SHALL be delegated to subagents via `work/subagent/c2r-03-spec.md` and `work/subagent/c2r-04-plan.md` respectively. The main agent MUST NOT write spec files or plan files inline.

#### Scenario: Phase 3 writes 10+ spec files
- **WHEN** the capability map contains 10 or more capabilities
- **THEN** all spec files are written inside the c2r-03-spec subagent's isolated context, and the main agent sees only a gate token (`PHASE_PASS` or `PHASE_BLOCKED`)

#### Scenario: Phase 4 writes implement-plan.md
- **WHEN** Phase 4 generates `tasks.md` and `implement-plan.md`
- **THEN** both files are written inside the c2r-04-plan subagent's isolated context, and the main agent sees only a gate token

#### Scenario: Main agent attempts inline spec write
- **WHEN** the main agent attempts to write a spec file directly instead of delegating to c2r-03-spec
- **THEN** the SKILL.md rules SHALL classify this as a delegation violation, and the action is forbidden

### Requirement: Subagent prompt files referenced by path

The main agent SHALL reference subagent prompt files by their file path (e.g., `work/subagent/c2r-05-implement.md`). The main agent MUST NOT fabricate inline prompts that embed Rust function signatures, batch contents, or C source mappings in the tool call input.

#### Scenario: Phase 5 dispatch
- **WHEN** dispatching a Phase 5 implementation batch
- **THEN** the Agent tool prompt field SHALL contain a reference to `work/subagent/c2r-05-implement.md` plus only `BATCH_ID` and context variables (SOURCE_ROOT, OUTPUT_DIR, etc.)

#### Scenario: Inline prompt fabrication detected
- **WHEN** the main agent constructs a prompt that includes embedded Rust type definitions or function signatures
- **THEN** this SHALL be considered a context leak, and the SKILL.md rules SHALL forbid it

### Requirement: Subagent gate token response

Every subagent SHALL return exactly one gate token: `PHASE_PASS`, `PHASE_BLOCKED`, or `PHASE_DEGRADED`, followed by at most one line of summary. Subagents MUST NOT return full implementation reports, file listings, or test output summaries.

#### Scenario: Successful subagent completion
- **WHEN** a subagent successfully completes its phase
- **THEN** it SHALL return `PHASE_PASS` followed by a one-line summary (e.g., "6 modules implemented, 29 tests pass")

#### Scenario: Verbose subagent result
- **WHEN** a subagent returns a multi-paragraph summary with file lists and test counts
- **THEN** the main agent SHALL discard the details and extract only the gate token for phase tracking

### Requirement: Main agent code-writing prohibition

The main agent MUST NOT write Rust source files, Cargo.toml, or run cargo commands. Project skeleton creation SHALL be the responsibility of the first Phase 5 implementation batch subagent.

#### Scenario: Project skeleton created inline
- **WHEN** the main agent writes Cargo.toml, lib.rs, or any Rust source file directly
- **THEN** this is a delegation violation and the action is forbidden

#### Scenario: Project skeleton created by subagent
- **WHEN** Batch 0 or Batch 1 of Phase 5 executes in a subagent
- **THEN** that subagent SHALL create Cargo.toml and lib.rs as part of its implementation scope
