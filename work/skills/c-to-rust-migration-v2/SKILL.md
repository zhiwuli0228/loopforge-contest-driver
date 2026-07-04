---
name: c-to-rust-migration-v2
description: Agent-first C-to-Rust migration — 10-phase orchestration with subagent delegation, SuperPower enforcement, and tools.py data retrieval.
---

# C-to-Rust Migration V2 — Agent Orchestrator

## Mission

Drive a complete C-to-Rust migration through 10 sequential phases. Each phase is delegated to a bounded subagent. The orchestrator sequences phases, enforces SuperPower guards, checks gates, and aborts on blockers.

## Inputs

| Variable | Source | Example |
|----------|--------|---------|
| `SOURCE_ROOT` | Environment | `E:/001code/csource/FlashDB` |
| `WORK_DIR` | Fixed | `work/` |
| `OUTPUT_DIR` | Derived | `work/output/flashDB_rust/` |
| `OPENSPEC_CHANGE` | Derived | `c-to-rust-migration` |

## Phase Sequence

Execute phases 0→10 in strict order. Do not skip, do not reorder.

| # | Phase | Subagent | tools.py | Writes |
|---|-------|----------|----------|--------|
| 0 | preflight | `c2r-00-preflight.md` | — | — |
| 1 | understand | `c2r-01-understand.md` | `parse-source` | `source-inventory.json` |
| 2 | design | `c2r-02-design.md` | — | `design.md` |
| 3 | spec | `c2r-03-spec.md` | — | `specs/*/spec.md` |
| 4 | plan | `c2r-04-plan.md` | — | `tasks.md`, `implement-plan.md` |
| 5 | implement | `c2r-05-implement.md` | `run-verification` | `src/**/*.rs` |
| 6 | test | `c2r-06-test.md` | `run-verification` | `tests/**/*.rs` |
| 7 | repair | `c2r-07-repair.md` | `run-verification` | fixes to `src/`, `tests/` |
| 8 | semantic-audit | `c2r-08-semantic-audit.md` | `run-verification` | invariant tests |
| 9 | quality-gates | `c2r-09-quality-gates.md` | `check-unsafe`, `fault-injection`, `neutrality-audit` | — |
| 10 | finalize | `c2r-10-finalize.md` | `write-report` | `result/`, `issues/` |

## Execution Protocol (per phase)

### Step 1: Prepare Subagent Context

Assemble a context block with these fields and pass it to the subagent:

```
SOURCE_ROOT: <path>
WORK_DIR: <path>
OUTPUT_DIR: <path>
OPENSPEC_CHANGE: <name>
PRIOR_OUTPUTS:
  <key>: <file path from previous phase>
```

Include only outputs that actually exist from prior phases. Do not invent paths.

### Step 2: Spawn Subagent

Use the Agent tool with the subagent file path from `work/subagent/`. The subagent prompt file contains its role, SuperPower rules, steps, output format, and gate criteria.

The subagent:
- Reads its own prompt for role definition
- Reads prior-phase output files as needed
- Reads C source files as needed
- Calls `python tools.py <command>` for data retrieval
- Produces its phase output files
- Returns a gate result

### Step 3: Check Gate

Each subagent returns exactly one gate token:

| Gate | Meaning | Action |
|------|---------|--------|
| `PHASE_PASS` | Phase completed successfully | Advance to next phase |
| `PHASE_BLOCKED` | Unrecoverable failure | **STOP.** Report blocker. |
| `PHASE_DEGRADED` | Completed with issues | Log warning. Advance. |

### Step 4: Record Progress

After each phase, record:
- Phase name and gate result
- Files produced
- Warnings or degraded notices
- Key metrics (file count, test count, etc.)

Pass relevant output file paths to the next phase via `PRIOR_OUTPUTS`.

## Phase-Specific Notes

### Phase 0 — Preflight
- Verify `python tools.py` works before spawning subagent
- If tools.py is broken, abort immediately — do not proceed

### Phase 1 — Understand
- The subagent discovers test directories under SOURCE_ROOT
- Pass discovered test dirs to `--test-dirs`
- Confirm `test_functions` list is populated — this is the C test inventory
- Output: `WORK_DIR/source-inventory.json`

### Phase 2 — Design
- Requires `openspec` CLI for template
- If openspec unavailable, subagent creates design.md directly
- Output: `openspec/changes/<name>/design.md`

### Phase 3 — Spec
- One spec per module + one `test-migration/spec.md`
- test-migration spec must map every C test function → Rust test (or N/A)
- Output: `openspec/changes/<name>/specs/`

### Phase 4 — Plan
- Produces `tasks.md` (checkbox list) and `implement-plan.md` (batch assignments)
- Each batch: 5-8 functions, independently buildable
- Output: `openspec/changes/<name>/tasks.md`, `implement-plan.md`

### Phase 5 — Implement
- Run one subagent per batch from implement-plan
- Each batch subagent writes Rust code, runs `cargo build`
- If a batch fails build, the subagent attempts fixes internally
- Output: Rust source files under `OUTPUT_DIR/src/`

### Phase 6 — Test
- Run one subagent per batch
- Each batch subagent writes tests, verifies C test coverage
- Uses the C test inventory from Phase 1 and test-migration spec from Phase 3
- Output: Rust test files under `OUTPUT_DIR/tests/`

### Phase 7 — Repair
- Single subagent that reads all errors from phases 5-6
- Fix → build → test loop, max 5 rounds (from config: `max_repair_rounds`)
- Must not weaken or delete tests to make them pass
- Output: fixed source/test files + repair log

### Phase 8 — Semantic Audit
- Reads specs for behavioral invariants
- Writes invariant tests (boundary, error path, state preservation, reset)
- Runs tests; failures are recorded, not silenced
- Output: invariant test files + audit report

### Phase 9 — Quality Gates
- Three checks in sequence: unsafe ratio, fault injection, neutrality audit
- Unsafe ratio threshold: < 10%
- Neutrality: 0 hits expected
- Output: gate summary (no files written)

### Phase 10 — Finalize
- Aggregates all phase results
- Writes `result/output.md`, `result/issues/00-summary.md`
- Writes verification report via openspec
- Returns `READY_FOR_EVALUATION` or `BLOCKED_WITH_REPORT`

## Abort Conditions

STOP the migration immediately if:
- Phase 0 returns `PHASE_BLOCKED` — environment not ready
- Phase 1 returns `PHASE_BLOCKED` — no parseable C source
- Any phase returns `PHASE_BLOCKED` — unrecoverable failure

Continue with warning if:
- Any phase returns `PHASE_DEGRADED` — log and proceed

## Data Flow Between Phases

```
Phase 0 ──→ (no file output)
Phase 1 ──→ source-inventory.json (includes test_functions)
Phase 2 ──→ design.md
Phase 3 ──→ specs/<module>/spec.md + specs/test-migration/spec.md
Phase 4 ──→ tasks.md + implement-plan.md
Phase 5 ──→ src/**/*.rs (Rust source)
Phase 6 ──→ tests/**/*.rs (Rust tests)
Phase 7 ──→ (fixes to src/ and tests/)
Phase 8 ──→ tests/**/*.rs (invariant tests, added to existing)
Phase 9 ──→ (no file output)
Phase 10 ─→ result/output.md, result/issues/00-summary.md
```

## Completion

When Phase 10 returns `PHASE_PASS`:
- `OUTPUT_DIR/` contains a complete Rust project
- `cargo build --locked` succeeds
- `cargo test --locked` succeeds
- `result/output.md` points to the Rust project
- `result/issues/00-summary.md` lists known issues

Return `READY_FOR_EVALUATION`.

If any phase blocked, return `BLOCKED_WITH_REPORT` with the blocker details.
