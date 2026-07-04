## Context

V2 architecture defines a 10-phase C-to-Rust migration workflow:
- Phases 0-4: Thinking (preflight, understand, design, spec, plan) — driven by OpenSpec
- Phases 5-10: Execution (implement, test, repair, semantic-audit, quality-gates, finalize) — driven by subagents

Change 1 delivered `work/runtime/tools.py` with 6 CLI commands. Change 2 delivered the `c2r-migration` schema (with `implement-plan` and `verification-report` artifacts) and SuperPower permission guards. This change (Change 3) creates the agent-facing layer: the SKILL.md orchestration prompt and 11 phase-specific subagent prompts.

Current state: existing `work/skills/c-to-rust-migration/SKILL.md` and old subagent files exist but are V1 patterns — monolithic prompts, no schema integration, no SuperPower enforcement. V2 needs clean replacements.

## Goals / Non-Goals

**Goals:**
- SKILL.md as single entry point: agent reads it, follows the 10-phase sequence, delegates each phase to a subagent
- Each subagent prompt is self-contained (~2K tokens): reads its own context, enforces SuperPower, returns bounded output
- Subagents use `openspec instructions <artifact> --change <name> --json` to get artifact templates and dependency context
- Phase transitions are explicit: SKILL.md checks subagent output before proceeding
- All prompts are generic (zero project-specific paths or hardcoding)

**Non-Goals:**
- No Python code changes
- No changes to tools.py, schema, or SuperPower YAML
- No runtime execution logic — these are prompt files only
- No Windows compatibility

## Decisions

**1. SKILL.md as linear sequencer, not state machine**

SKILL.md follows a fixed 0→10 phase sequence. Each phase: read SuperPower guards for that phase, spawn subagent with bounded context, check output gate, proceed or abort.

Alternatives considered:
- State machine with conditional transitions: over-engineered for a linear workflow
- Event-driven: harder for agent to follow deterministically

**2. Subagent prompts as separate files, not embedded in SKILL.md**

Each `c2r-NN-<phase>.md` file is a standalone prompt. SKILL.md references them by path. Benefits: subagents can be tested independently, context isolation is explicit, prompts can be iterated without touching SKILL.md.

**3. Two-tier context injection: SKILL.md provides phase context, subagent reads its own files**

SKILL.md passes: phase name, SuperPower rules excerpt, OpenSpec change name, and the subagent file path. The subagent itself reads source files, specs, and tools.py output. This keeps SKILL.md context small (~3K tokens) and subagent context bounded (~5-8K tokens).

**4. Output gate pattern: every subagent returns a structured result**

Each subagent returns one of: `PHASE_PASS`, `PHASE_BLOCKED`, `PHASE_DEGRADED` with a brief report. SKILL.md checks this before proceeding. This is the same gate pattern from the existing subagent files, formalized.

**5. v2 files coexist with v1, not replace**

New files go to `work/skills/c-to-rust-migration-v2/SKILL.md` and `work/subagent/c2r-*.md`. Old files remain untouched. This allows gradual migration and A/B comparison.

**6. Subagent numbering: c2r-00 through c2r-10**

Numeric prefix matches the V2 blueprint phases (0-10). This makes it obvious which subagent handles which phase. Existing subagent files use descriptive names (e.g., `c-to-rust-implementation-subagent.md`); v2 uses numbered names for ordering clarity.

## Risks / Trade-offs

- **[Risk] Subagent context may exceed ~8K tokens for complex source trees** → Mitigation: subagent reads only files it needs, not entire source tree; tools.py `parse-source` pre-digests source into structured JSON
- **[Risk] SKILL.md may become too long if it includes all phase details** → Mitigation: SKILL.md is a sequencer; phase logic lives in subagent files
- **[Trade-off] Separate files = more files to manage vs. single-file simplicity** → Chosen: separation enables independent testing and bounded context
- **[Trade-off] Fixed sequence vs. dynamic phase skipping** → Chosen: fixed sequence is simpler and more predictable; agent can abort early but shouldn't skip phases

## Migration Plan

1. Create `work/skills/c-to-rust-migration-v2/SKILL.md`
2. Create 11 subagent files `work/subagent/c2r-00-preflight.md` through `c2r-10-finalize.md`
3. Validate: run `openspec new change --schema c2r-migration test-change` and trace through SKILL.md manually
4. Old files remain; no migration needed for v1 prompts

## Open Questions

- Should SKILL.md include inline SuperPower excerpts or reference the YAML file? (Decision: reference by path, subagent reads the relevant section)
- Should subagent prompts include the tools.py command syntax inline or reference `tools.py --help`? (Decision: include the specific command for each phase — reduces subagent round-trips)
