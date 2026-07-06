## Context

The optimize-context change correctly marked Phase 3/4 as Delegate and added context safety rules to SKILL.md. However, E2E testing (`test02.md`) revealed the assistant subverts these rules by reading subagent prompt files into the main context before dispatching, then constructing 80+ line inline prompts that duplicate the subagent prompt content. The delegation intent is correct but the enforcement is too weak.

Additionally, SKILL.md Phase-Specific Notes contain execution details (steps, tool usage, edge cases) that duplicate content already in subagent prompt files. This adds unnecessary bulk to the orchestrator.

## Goals / Non-Goals

**Goals:**
- Reduce SKILL.md from ~239 lines to ~170 lines by removing duplicated execution details
- Enforce subagent prompt file path references with a hard "DO NOT read" rule
- Provide a concrete 2-3 line dispatch template for all subagent calls
- Fix loopforge-driver/SKILL.md line 132 delegation marking inconsistency

**Non-Goals:**
- Modifying subagent prompt files (c2r-*.md) — they are already complete
- Changing the 11-phase pipeline structure
- Reducing the number of phases or subagent calls

## Decisions

### Decision 1: Strip Phase-Specific Notes to scheduling-only

Each phase entry reduced to:
```
### Phase N — Name
- **Delegate** to `work/subagent/c2r-XX-name.md`
- Output: `<file pattern>`
- Gate: `PHASE_PASS`/`PHASE_BLOCKED`/`PHASE_DEGRADED`
```

**Rationale**: The execution steps (Step 1: Get template, Step 2: Read inventory, etc.) already exist in the subagent prompt files. Having them in both places adds ~70 lines of redundant content to SKILL.md without improving execution quality — the subagent reads its own prompt regardless.

**Alternatives considered**:
- Keeping current level of detail: Already proven insufficient to prevent context explosion (test02.md shows 80+ line inline prompts)
- Moving all detail to subagent prompts only: This is the chosen approach

### Decision 2: Hard "DO NOT read" rule with dispatch template

```
## Subagent Dispatch Protocol

1. DO NOT read `work/subagent/c2r-*.md` files into the main context.
2. Construct the Agent tool prompt using ONLY this format:

   Execute <subagent_prompt_path> with:
   KEY1=<value>
   KEY2=<value>

3. The subagent reads its own prompt file from disk. The main agent
   only receives back a gate token + one-line summary.
```

**Rationale**: The previous rule "Subagent prompts MUST reference the subagent prompt file by path" was interpreted as "read the file first, then reference it." The new rule explicitly prohibits reading and provides a mechanical template that eliminates the temptation to construct elaborate prompts.

### Decision 3: Fix loopforge-driver/SKILL.md Phase 3/4

Change line 132 from:
```
- Phase 0-4: preflight, understand, design, spec, plan (inline or subagent)
```
To:
```
- Phase 0, 2: preflight, design (inline)
- Phase 1, 3, 4: understand, spec, plan (delegated to subagent)
```

**Rationale**: The current text says "inline or subagent" which contradicts the Delegate mandate in INSTRUCTION.md and c-to-rust-migration-v2/SKILL.md. The assistant reads loopforge-driver/SKILL.md first and may treat "inline or subagent" as permission to choose inline execution.

## Risks / Trade-offs

- [Risk] Stricter rules may not be followed if the assistant's default behavior is to read referenced files → Mitigation: The "DO NOT read" rule is absolute and unambiguous. Combined with the dispatch template, it leaves no room for interpretation.
- [Trade-off] Removed detail from SKILL.md means main agent has less visibility into subagent internals → Acceptable: the main agent doesn't need execution detail; it only needs to know which subagent to dispatch and whether it passed/failed.
