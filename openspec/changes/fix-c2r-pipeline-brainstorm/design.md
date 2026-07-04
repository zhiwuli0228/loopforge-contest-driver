## Context

The V2 C-to-Rust migration pipeline has three governance layers: OpenSpec (thinking framework), SuperSpec (stage definitions), and SuperPower (permission boundaries). The pipeline is defined in `work/profiles/superspec/c-to-rust-migration-stages.yaml` with 11 stages (00-10), each backed by a subagent prompt at `work/subagent/c2r-*.md` and permission boundaries at `work/profiles/superpower/c-to-rust-migration-guards.yaml`.

The V2 blueprint specified: "Phase 1: Understand → Agent reads source + JSON → proposal.md". The implementation diverged, making Phase 1 purely mechanical (parse-source only) with `forbidden: any write operations`. This broke the pipeline's ability to autonomously identify key functional scenarios before designing specs.

Additionally, all 5 templates under `openspec/schemas/c2r-migration/templates/` use HTML comments (`<!-- ... -->`) as placeholders, which agents interpret as optional, leading to shallow output. The test phase (06) is strictly after implementation (05), preventing per-capability unit test coverage.

## Goals / Non-Goals

**Goals:**
- Restructure the Understand phase (01) into three bounded-context sub-stages: 01a (mechanical inventory), 01b (parallel per-module analysis), 01c (cross-module synthesis)
- Each subagent instance context ≤ 5K tokens
- Relax SuperPower guards: understand phases may write analysis artifacts to `logs/trace/` and `openspec/changes/`
- Redesign all 5 templates with mandatory structured fields — no HTML comments as sole content
- Interleave implementation and unit testing per capability batch
- Update subagent prompts to enforce autonomous judgment ("do not ask user") and structured output

**Non-Goals:**
- Modifying tools.py — the pure tool layer is unchanged
- Modifying the SuperPower default-deny principle — core protections remain
- Merging or removing pipeline stages 02-10 — only 01 is restructured
- Adding new Python tools — all new behavior is agent-side, using existing tools
- Supporting non-C-to-Rust migration scenarios

## Decisions

### 1. Three-stage Understand decomposition (01a → 01b[parallel] → 01c)

```
01a-inventory (mechanical, ~1K ctx)
  │
  ├── 01b-capability (kvdb instance, ~2.5K ctx)
  ├── 01b-capability (tsdb instance, ~1.5K ctx)
  ├── 01b-capability (utils instance, ~1K ctx)
  └── 01b-capability (file instance, ~1K ctx)
  │
  └── 01c-synthesize (~3K ctx, reads only summaries)
```

**Rationale**: The V2 blueprint principle: "Agent must read on demand, not receive bulk data." A single agent analyzing all 5 C files would exceed 6K tokens in source alone. Splitting into per-module subagents keeps each ≤ 3-5K. The synthesize step only reads the per-module scenario summaries (~500 tokens each), not raw C source.

**Alternatives considered:**
- Single agent with all files: Context explosion, instruction degradation beyond ~8K tokens
- Two-level without parallel: Slower but same output quality; parallel is strictly better for latency
- Skip synthesize step: Loses cross-module capability identification (e.g., GC spans kvdb + utils + file)

### 2. 01b parallel instances driven by inventory module list

01b's subagent prompt is parameterized per module. The orchestrator reads `source-inventory.json`, extracts the module list (distinct source files grouped by directory), and spawns one 01b instance per module.

**Module grouping rule**: One 01b instance per `.c` file (with its corresponding `.h`). If a `.c` file exceeds 2000 lines, it may be further split by function group (e.g., `kvdb-core` vs `kvdb-gc`).

### 3. Capability identification rules (autonomous, no human)

Each 01b subagent MUST independently identify capabilities. Decision rules are embedded in the prompt:

- A function or group of functions with an independent state lifecycle = 1 capability
- A data structure with dedicated read/write/validate operations = 1 capability
- A multi-step algorithm with intermediate states = 1 capability
- Minimum 1 capability per module, maximum 5 per module
- If unsure about boundary: split (over-splitting is better than under-splitting; 01c can merge)

The 01c synthesize step: reads all 01b outputs, identifies capabilities that span multiple modules, merges near-duplicates, assigns priority (P0=foundational, P1=core, P2=auxiliary), and produces a dependency graph.

### 4. SuperPower guard relaxation: allow output, protect source

```
BEFORE (understand):                 AFTER (understand phases):
  forbidden:                           forbidden:
    - any write operations   →           - modify C source files
    - any source modification            - modify tools.py
                                         - modify profiles
                                       allowed writes:
                                         - logs/trace/c-to-rust/**
                                         - openspec/changes/*/ (01c only)
```

**Rationale**: The original "no write" guard conflated "don't corrupt source" with "don't produce artifacts." The V2 blueprint explicitly expected Phase 1 to produce `proposal.md`. The fix narrows the prohibition to what actually matters.

### 5. Template redesign: mandatory fields, no HTML comments

Every template field becomes one of:
- **Required table** (rows must be filled, empty table = incomplete)
- **Required checklist** (all items must have a status)
- **Required section** (must not be empty)

HTML comments (`<!-- ... -->`) are removed entirely. Placeholder text like "Description of the requirement" is replaced with fill-in prompts: `[Describe the behavior this requirement mandates. Include C source file and line number reference.]`

### 6. Test interleaving: batch = implement + test

```
BEFORE:                              AFTER:
  Phase 5 (implement ALL)              Batch 1: CRC32
  Phase 6 (test ALL)                     ├── implement calc_crc32
  Phase 7 (repair ALL)                   ├── write unit tests for calc_crc32
                                         └── cargo test crc32 → pass ✅
                                       Batch 2: Status Table
                                         ├── implement set/get/write/read status
                                         ├── write unit tests (6 WRITE_GRAN variants)
                                         └── cargo test status_table → pass ✅
                                       ...
```

Each batch in `implement-plan.md` now contains BOTH implementation and test tasks. The `c2r-05-implement.md` subagent is updated to include a mandatory "write unit tests for this batch" step before reporting success. The `c2r-06-test.md` subagent is re-scoped to integration tests and cross-capability coverage verification.

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| 01b parallel instances produce inconsistent formats | 01c can't synthesize | 01b prompt includes a strict output template; 01c validates format before synthesizing |
| Over-splitting capabilities creates too many specs | Spec maintenance burden | 01c merge step; P2 capabilities can be deferred or combined |
| Guard relaxation could allow accidental source modification | Data loss | Guards still forbid `SOURCE_ROOT/**` writes; only `logs/` and `openspec/` paths are allowed |
| New templates are too rigid for edge cases | Agent can't complete artifact | Templates have "if not applicable, explain why" escape hatches for each section |
| Subagent count increase slows overall pipeline | Longer migration time | 01b instances run in parallel; total time = slowest instance + 01c (~2 minutes typical) |

## Open Questions

1. **Module grouping for 01b**: Should test files get their own 01b instance, or be analyzed alongside their corresponding source module? Leaning toward: test files analyzed alongside source since test scenarios inform capability identification.

2. **Minimum capability threshold**: Should 01c reject a capability map with fewer than N capabilities? Leaning toward: minimum 3 capabilities, warn if fewer (might indicate insufficient analysis depth).

3. **Backward compatibility with existing changes**: The `c2r-flashdb` change has file-level specs. Should we archive it and start fresh with the new pipeline, or retrofit? Leaning toward: archive and start fresh — the existing Rust output is auto-transpiled garbage anyway.
