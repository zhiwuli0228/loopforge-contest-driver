## Why

E2E session analysis (`test02.md`) revealed the optimize-context delegation rules are being subverted: the assistant reads every subagent prompt file (c2r-03-spec.md, c2r-04-plan.md, etc.) into the main context before dispatching, then constructs massive inline prompts (80+ lines) duplicating the subagent prompt content. This defeats the entire delegation strategy — subagent prompt content enters main context regardless. Additionally, SKILL.md Phase-Specific Notes duplicate execution details already present in subagent prompt files, adding unnecessary orchestrator bulk.

## What Changes

- **SKILL.md Phase-Specific Notes stripped to scheduling-only**: Each phase entry reduced to subagent file path + output file names + gate expectation. Execution steps, detailed instructions, and rationale removed (already in subagent prompt files).
- **Hard prompt-file-reference rule**: "DO NOT read subagent prompt files into the main context. The Agent tool prompt field SHALL contain only: `Execute <subagent_prompt_path> with: KEY=VALUE, ...`. The subagent reads the prompt file from disk in its own context."
- **Subagent dispatch template**: Concrete 2-3 line dispatch format replacing the free-form inline prompt construction.
- **loopforge-driver/SKILL.md:132**: Phase 3/4 corrected from "inline or subagent" to "delegated to subagent".

## Capabilities

### New Capabilities

- `prompt-file-reference`: Rule and template enforcing subagent prompt files are referenced by disk path only, never read or duplicated into main-agent context. The Agent tool prompt field SHALL be 2-3 lines of `KEY=VALUE` assignments.

### Modified Capabilities

- `context-safe-delegation`: Strengthen prompt file reference from "MUST reference by path" to "DO NOT read subagent prompt files into main context." Add concrete dispatch template.

## Impact

- `work/skills/c-to-rust-migration-v2/SKILL.md` — Phase-Specific Notes stripped down, new hard rule block
- `work/skills/loopforge-driver/SKILL.md` — line 132 Phase 3/4 delegation marking corrected
