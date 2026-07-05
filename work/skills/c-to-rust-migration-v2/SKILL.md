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
| `SOURCE_ROOT` | context-package.json | `/home/lzw/loopforge-e2e/FlashDB` |
| `WORK_DIR` | context-package.json | `work/` |
| `OUTPUT_DIR` | context-package.json | `work/output/flashDB_rust/` |
| `OPENSPEC_CHANGE` | context-package.json | `c-to-rust-migration` |
| `PRIOR_OUTPUTS` | context-package.json | paths to source-inventory.json, call-graph.json, etc. |

All paths come from `logs/trace/execution-adapter/state/context-package.json`.

## Prerequisite: Data Preparation

Before Phase 0, the context package MUST exist. If `logs/trace/execution-adapter/state/context-package.json` is missing, run Stage 1 first:

```bash
SOURCE_ROOT="<path>" bash work/scripts/run.sh --run
```

This produces `AGENT_DELEGATION_READY` and writes the context package containing all absolute paths and analysis data needed for phases 0→10.

Read the context package before starting Phase 0:

```bash
cat logs/trace/execution-adapter/state/context-package.json
```

Key fields: `SOURCE_ROOT`, `WORK_DIR`, `OUTPUT_DIR`, `RESULT_DIR`, `LOG_DIR`, `PRIOR_OUTPUTS`, `ANALYSIS_SUMMARY`.

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
SOURCE_ROOT: <absolute path>
WORK_DIR: <absolute path>
OUTPUT_DIR: <absolute path>
OPENSPEC_CHANGE: <name>
PRIOR_OUTPUTS:
  <key>: <absolute file path from previous phase>
```

**All paths MUST be absolute.** The subagent's working directory is unpredictable (it may be the repo root, the user's home, or anywhere else). Relative paths will cause "file not found", permission errors, or writes to the wrong location. Before spawning a subagent:

1. Resolve `SOURCE_ROOT` to an absolute path (use `readlink -f`, `realpath`, or `pwd`)
2. Resolve `WORK_DIR` to an absolute path — typically `<repo_root>/work/`
3. Resolve `OUTPUT_DIR` to an absolute path — typically `<repo_root>/work/output/<project_name>/`
4. Resolve every `PRIOR_OUTPUTS` value to an absolute path

Pass ONLY absolute paths. The subagent prompts use these values directly in shell commands (`test -d "SOURCE_ROOT/tests"`, `python WORK_DIR/runtime/tools.py`, `cargo build --manifest-path "OUTPUT_DIR/Cargo.toml"`) and will fail on relative paths.

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
- Read `logs/trace/execution-adapter/state/context-package.json` for all paths
- Read `logs/trace/run-summary.json` for self-check and source analysis gate results
- Verify all `PRIOR_OUTPUTS` files exist on disk
- Verify `python tools.py` is functional: `python WORK_DIR/runtime/tools.py --help`
- If any check fails, return `PHASE_BLOCKED` immediately

### Phase 1 — Understand
- Data is already pre-computed: `PRIOR_OUTPUTS.source_inventory`, `PRIOR_OUTPUTS.public_api_map`, etc.
- The subagent reads these files (no need to re-run parse-source)
- Confirm `test_functions` from ANALYSIS_SUMMARY is populated

### Phase 2 — Design
- Requires `openspec` CLI for template
- If openspec unavailable, subagent creates design.md directly
- Output: `openspec/changes/<name>/design.md`

### Phase 3 — Spec
- **Delegate** to `work/subagent/c2r-03-spec.md`
- Main agent passes context variables (SOURCE_ROOT, WORK_DIR, OUTPUT_DIR, OPENSPEC_CHANGE) and PRIOR_OUTPUTS to subagent
- Subagent reads capability map, writes all spec files in isolation (one spec per module + `test-migration/spec.md`), returns gate token
- Main agent only receives `PHASE_PASS`/`PHASE_BLOCKED`/`PHASE_DEGRADED` + one-line summary

### Phase 4 — Plan
- **Delegate** to `work/subagent/c2r-04-plan.md`
- Main agent passes context variables (SOURCE_ROOT, WORK_DIR, OUTPUT_DIR, OPENSPEC_CHANGE) and PRIOR_OUTPUTS to subagent
- Subagent reads specs, writes `tasks.md` and `implement-plan.md` in isolation (each batch: 5-8 functions, independently buildable), returns gate token
- Main agent only receives gate token + one-line summary

### Phase 5 — Implement
- **Dynamic batch scheduling** with dependency-aware parallelism:
  1. Parse `implement-plan.md` → discover `{batch_id, priority, dependencies}` for all batches
  2. Group batches by priority level: P0, P1, P2
  3. For each priority level (P0 → P1 → P2):
     a. Find batches at current level with all dependencies satisfied
     b. Dispatch independent batches in parallel (one subagent per batch)
     c. Each subagent references `work/subagent/c2r-05-implement.md` by file path with only `BATCH_ID` and context variables (SOURCE_ROOT, OUTPUT_DIR, OPENSPEC_CHANGE)
     d. Wait for all dispatched subagents to return gate tokens
     e. Mark completed batches as done, advance to next priority level
- If `implement-plan.md` parsing fails, fall back to sequential execution
- **Do NOT** fabricate inline prompts embedding Rust signatures or batch contents
- Each batch subagent writes Rust code, runs `cargo build`, attempts internal fixes on build failure
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

## Context Safety Rules

**Code-writing prohibition**: The main agent MUST NOT write Rust source files (`src/**/*.rs`), Cargo.toml, Cargo.lock, spec files (`specs/**/*.md`), or plan files (`tasks.md`, `implement-plan.md`). These writes SHALL only occur inside subagents. The first Phase 5 batch subagent is responsible for project skeleton creation (Cargo.toml, lib.rs).

**Prompt file references**: Subagent prompts MUST reference the subagent prompt file by path (e.g., `work/subagent/c2r-05-implement.md`), not inline-construct prompts. The main agent passes only `BATCH_ID` and context variables — never embed Rust function signatures, C source mappings, or batch contents in the prompt field.

**Gate token compression**: All subagents MUST return only `PHASE_PASS`/`PHASE_BLOCKED`/`PHASE_DEGRADED` plus at most one line of summary (e.g., "6 modules implemented, 29 tests pass"). Subagents MUST NOT return full implementation reports, file listings, or test output summaries. The main agent discards verbose results and extracts only the gate token.

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
