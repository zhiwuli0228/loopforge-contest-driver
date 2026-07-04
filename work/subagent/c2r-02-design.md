# c2r-02: Design

## Role

Create the technical design document for the C-to-Rust migration. Write phase — produces `design.md`.

## Context

You receive:
- `OPENSPEC_CHANGE` — the OpenSpec change name
- `SOURCE_ROOT` — path to the C source tree
- `WORK_DIR` — path to the work directory
- Phase 1 output: `source-inventory.json` location

## SuperPower Rules

Read `work/profiles/superpower/c-to-rust-migration-guards.yaml`, section `design`.

- **Allowed tools**: none (pure agent reasoning)
- **Allowed filesystem**: read `**`, write `openspec/changes/*/design.md`
- **Forbidden**: modify source code, modify tools.py, modify profiles

## Steps

1. Call `openspec instructions design --change "OPENSPEC_CHANGE" --json` to get the template and instructions
2. Read `WORK_DIR/source-inventory.json` for source analysis
3. Read the C source files to understand behavior, data structures, and I/O patterns
4. Create the design document following the template from openspec instructions
5. Write to the path specified in the instructions (`outputPath`)

## Output

Write `design.md` to the OpenSpec change directory. The design must cover:
- Context (current state, constraints)
- Goals / Non-Goals
- Key technical decisions with rationale
- Risks / Trade-offs
- Migration approach (crate layout, module mapping, error strategy)

## Gate

Return one of:
- `PHASE_PASS` — design document written successfully
- `PHASE_BLOCKED` — insufficient source information to create design
