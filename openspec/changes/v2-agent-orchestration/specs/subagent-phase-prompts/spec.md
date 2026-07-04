## ADDED Requirements

### Requirement: Each subagent prompt is a self-contained file

Each subagent prompt SHALL be a standalone markdown file under `work/subagent/` named `c2r-NN-<phase>.md` where NN is the two-digit phase number (00-10).

#### Scenario: File naming convention
- **WHEN** subagent files are listed
- **THEN** files are named `c2r-00-preflight.md`, `c2r-01-understand.md`, `c2r-02-design.md`, `c2r-03-spec.md`, `c2r-04-plan.md`, `c2r-05-implement.md`, `c2r-06-test.md`, `c2r-07-repair.md`, `c2r-08-semantic-audit.md`, `c2r-09-quality-gates.md`, `c2r-10-finalize.md`

#### Scenario: Self-contained context
- **WHEN** a subagent reads its prompt file
- **THEN** the file contains all role definition, allowed tools, write scope, expected output, and gate criteria — no external context required beyond what SKILL.md injects

### Requirement: Each subagent prompt defines bounded context (~2K tokens)

Each subagent prompt SHALL be approximately 2K tokens, containing only the information needed for its specific phase.

#### Scenario: Context budget
- **WHEN** a subagent prompt is measured
- **THEN** it is under 2500 tokens (approximately 2K with tolerance)

#### Scenario: No cross-phase leakage
- **WHEN** a subagent reads its prompt
- **THEN** it contains no logic or instructions for other phases

### Requirement: Each subagent reads its SuperPower guards

Each subagent prompt SHALL instruct the agent to read the relevant phase section from `work/profiles/superpower/c-to-rust-migration-guards.yaml` and enforce the allowed/forbidden rules.

#### Scenario: SuperPower enforcement
- **WHEN** a subagent begins execution
- **THEN** it reads the SuperPower YAML, extracts its phase's rules, and constrains its actions to the allowed set

#### Scenario: Forbidden action rejection
- **WHEN** a subagent attempts an action listed as forbidden in its SuperPower rules
- **THEN** the subagent refuses the action and reports the violation

### Requirement: Each subagent uses tools.py for data operations

Each subagent prompt SHALL specify the exact `python tools.py <command>` invocation for its phase's data needs.

#### Scenario: Phase-specific tools.py commands
- **WHEN** subagent c2r-00 (preflight) runs
- **THEN** it calls `python tools.py self-check`
- **WHEN** subagent c2r-01 (understand) runs
- **THEN** it calls `python tools.py parse-source`
- **WHEN** subagent c2r-05 (implement) or c2r-06 (test) or c2r-07 (repair) runs
- **THEN** it calls `python tools.py run-verification`
- **WHEN** subagent c2r-09 (quality-gates) runs
- **THEN** it calls `python tools.py check-unsafe`, `python tools.py fault-injection`, and `python tools.py neutrality-audit`

### Requirement: Each subagent returns a structured gate result

Each subagent SHALL return one of three statuses: `PHASE_PASS`, `PHASE_BLOCKED`, or `PHASE_DEGRADED`, accompanied by a brief report (under 500 tokens).

#### Scenario: Successful phase completion
- **WHEN** a subagent completes all its requirements
- **THEN** it returns `PHASE_PASS` with a summary of what was produced

#### Scenario: Phase cannot proceed
- **WHEN** a subagent encounters a blocking issue (e.g., preflight fails, build irreparably broken)
- **THEN** it returns `PHASE_BLOCKED` with a description of the blocker

#### Scenario: Phase completes with issues
- **WHEN** a subagent completes but with known issues (e.g., some tests failing, degraded coverage)
- **THEN** it returns `PHASE_DEGRADED` with a description of the issues

### Requirement: Subagent prompts are generic with zero project-specific hardcoding

Each subagent prompt SHALL NOT contain any project-specific paths, file names, or hardcoded values. All paths SHALL be derived from the OpenSpec change directory, `SOURCE_ROOT`, and `work/` conventions.

#### Scenario: No hardcoded paths in subagent prompts
- **WHEN** any subagent prompt is inspected
- **THEN** it contains no absolute paths, no project-specific file references, and no hardcoded directory structures

### Requirement: Subagent read/write scope is explicitly defined

Each subagent prompt SHALL define its allowed read paths and allowed write paths, aligned with the SuperPower guards for its phase.

#### Scenario: Write scope matches SuperPower
- **WHEN** a subagent's write scope in its prompt is compared to its SuperPower guards
- **THEN** they are consistent — the subagent only writes to paths its SuperPower rules allow

#### Scenario: Read scope is broad, write scope is narrow
- **WHEN** a subagent's scope is evaluated
- **THEN** read scope is `**` (everything) while write scope is limited to phase-specific output paths
