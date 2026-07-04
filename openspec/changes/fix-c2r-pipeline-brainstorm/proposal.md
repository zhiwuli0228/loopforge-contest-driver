## Why

The V2 C-to-Rust migration pipeline diverged from its own blueprint. The blueprint's Phase 1 ("Understand: Agent reads source + JSON → proposal.md") was implemented as a mechanical parse-only step with `forbidden: any write operations`, stripping the agent of its ability to analyze C code and identify key functional scenarios. This cascaded: specs are file-level instead of capability-level, implementation and testing are strictly sequential (all implement → all test), and templates are HTML-comment shells that agents treat as optional. The result: no autonomous brainstorm, no scenario-driven spec granularity, no per-capability unit tests.

## What Changes

- **Restructure Understand phase** into three sub-stages: mechanical inventory (01a), parallel per-module capability analysis (01b), cross-module synthesis (01c) — each subagent context ≤ 5K tokens
- **Relax SuperPower guards** for understand stages: allow writing to `logs/trace/` and `openspec/changes/` while keeping the ban on modifying C source, tools.py, and profiles
- **Redesign all templates** replacing HTML comments with mandatory structured fields (tables, checklists, cross-references) to prevent agent laziness
- **Interleave implementation and testing** per capability: each batch = implement capability → write unit tests → verify, before moving to next capability
- **Update 11 subagent prompts** to enforce capability-driven workflow and autonomous decision-making
- **Add brainstorm artifact** to the c2r-migration schema pipeline

## Capabilities

### New Capabilities
- **superspec-stage-restructure**: 01a inventory → 01b parallel capability analysis → 01c synthesize, each with bounded context
- **superpower-guard-relaxation**: Allow understand phases to write analysis artifacts while protecting source code
- **brainstorm-subagents**: Three new subagent prompts (01a, 01b, 01c) with structured output templates and autonomous judgment requirements
- **anti-lazy-templates**: Redesigned templates for design, spec, tasks, implement-plan, verification-report with mandatory fields
- **capability-driven-test-interleave**: Each batch couples implementation and unit tests for one capability

### Modified Capabilities
- **c2rust-migration-superspec**: 11-stage YAML updated with 01a/01b/01c replacing 01-understand
- **c2r-migration-schema**: Artifact pipeline adds brainstorm artifact, reorders for capability-first flow

## Impact

- `work/profiles/superspec/c-to-rust-migration-stages.yaml` — 01 stage split into 3, with parallel marker on 01b
- `work/profiles/superpower/c-to-rust-migration-guards.yaml` — understand phases write permissions adjusted
- `work/subagent/c2r-01*.md` — 3 new files replacing c2r-01-understand.md
- `work/subagent/c2r-03-spec.md` through `c2r-06-test.md` — updated for capability-driven flow and test interleaving
- `openspec/schemas/c2r-migration/schema.yaml` — brainstorm artifact added
- `openspec/schemas/c2r-migration/templates/*.md` — all 5 templates redesigned
- Zero impact on tools.py — pure tool layer unchanged
- Zero impact on SuperPower core principle — still default-deny, still protects source/profile/tools
