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
| `SOURCE_ROOT` | context-package.json | `/path/to/c/source/tree` |
| `WORK_DIR` | context-package.json | `work/` |
| `OUTPUT_DIR` | context-package.json | `work/output/<project>_rust/` |
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
| 3 | spec | `c2r-03-spec.md` | — | `specs/<cap>/spec-part-N.md` (sub-batched) |
| 4 | plan | `c2r-04-plan.md` | — | `tasks.md`, `implement-plan.md`, `specs/test-migration/spec.md` |
| 5a | implement | `c2r-05a-implement.md` | `run-verification` | `src/**/*.rs` |
| 5b | unit-test | `c2r-05b-unit-test.md` | `run-verification` | `tests/<capability>_tests.rs` |
| 6 | test | `c2r-06-test.md` | `run-verification` | integration `tests/**/*.rs` |
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
- **Clean stale artifacts**: Delete all subagent-generated outputs from `openspec/changes/<OPENSPEC_CHANGE>/` — `design.md` (Phase 2), `specs/` (Phase 3), `tasks.md` and `implement-plan.md` (Phase 4). These must be regenerated with the current subagent prompts; stale formats will break downstream phases. Keep `.openspec.yaml`.
- Verify all `PRIOR_OUTPUTS` files exist on disk
- Verify `python WORK_DIR/runtime/tools.py --help` succeeds
- Gate: `PHASE_PASS`/`PHASE_BLOCKED` — stop on blocked

### Phase 1 — Understand
- Subagent: `work/subagent/c2r-01-understand.md`
- Output: `source-inventory.json`
- Gate: `PHASE_PASS`/`PHASE_BLOCKED`/`PHASE_DEGRADED`

### Phase 2 — Design
- Subagent: `work/subagent/c2r-02-design.md`
- Output: `openspec/changes/<name>/design.md`
- Gate: `PHASE_PASS`/`PHASE_BLOCKED`/`PHASE_DEGRADED`

### Phase 3 — Spec (Grouped by Source File, Sub-Batched by Function Count)

- Subagent: `work/subagent/c2r-03-spec.md`
- **Batch scheduling** from `01c-capability-map.json`:
  1. **Group by C source file**: The raw capability map has 1 capability per API (e.g., 44 capabilities for FlashDB). Read all capabilities and group them by `evidence[0].file` (the C source file). Each file-group becomes one logical capability.
     - Example: `src/fdb_kvdb.c` → group of 15 APIs → logical capability `fdb_kvdb`
     - Example: `src/fdb.c` → group of 4 APIs → logical capability `fdb`
  2. **Merge to reduce cardinality**: Instead of 44 subagents (one per API), only dispatch per source-file group. After grouping, a typical C project yields 3–6 file-groups.
  3. **Auto-split large groups**: If a file-group has >4 APIs, split into sub-batches of 3–4 functions each. `fdb_kvdb` with 15 APIs → 4–5 sub-batches. `fdb` with 4 APIs → 1 sub-batch.
  4. Each sub-batch receives:
     - `CAPABILITY_ID` — derived from source file name (e.g., `fdb_kvdb` from `src/fdb_kvdb.c`)
     - `FUNCTION_SUBSET` — JSON array of 2–4 API/function names assigned to this sub-batch
     - `PART_INDEX` — 1-based part number
     - `TOTAL_PARTS` — total parts for this file-group
  5. Part 1 writes shared sections (Overview, Data Structures, Invariants, Dependencies). Parts 2+ write only their function Requirements + Test Specifications.
  6. **All sub-batches from all file-groups dispatch in parallel** — each writes a unique file `specs/<capability_id>/spec-part-<N>.md`, no file conflicts.
  7. Wait for all sub-batches to return gates.
- Each subagent reads only the C source files for its file-group, and only deeply analyzes the functions in its `FUNCTION_SUBSET`
- Does NOT write `test-migration/spec.md` — that is done by Phase 4
- Output: `specs/<capability_id>/spec-part-<N>.md` — Phase 4 reads all parts as one logical spec
- Gate: `PHASE_PASS`/`PHASE_BLOCKED`/`PHASE_DEGRADED`

### Phase 4 — Plan (+ Test-Migration Spec)

- Subagent: `work/subagent/c2r-04-plan.md`
- Reads all capability specs + capability map + source inventory
- Creates `tasks.md` + `implement-plan.md` (batch plan for 5a/5b)
- Also creates `specs/test-migration/spec.md` — C→Rust test mapping table (consumed by Phase 6)
- Output: `tasks.md`, `implement-plan.md`, `specs/test-migration/spec.md`
- Gate: `PHASE_PASS`/`PHASE_BLOCKED`/`PHASE_DEGRADED`

### Phase 5a — Implement (Code + Compile)

- Subagent: `work/subagent/c2r-05a-implement.md`
- **Dynamic batch scheduling** from `implement-plan.md`:
  1. Parse batches → `{batch_id, capability, priority, dependencies, rust_target, features}`
  2. **Designate scaffold batch**: Identify the lowest `batch_id` at P0 priority — this is the **scaffold batch**. The scaffold batch writes complete `lib.rs`, `Cargo.toml`, and `types.rs` before writing its own capability code. All other batches SHALL NOT modify these infrastructure files.
  3. **File isolation verification**: Check that no two batches at the same priority level share a `rust_target` file. If conflicts are detected, mark affected batches for sequential execution in `batch_id` order within that priority level.
  4. Group by priority: P0 → P1 → P2. Batches with no `rust_target` conflicts at the same level dispatch in parallel.
  5. **Dispatch**: For each priority level, dispatch batches according to conflict resolution. The scaffold batch is dispatched as part of P0 — it writes infrastructure files before other batches read them.
  6. Wait for all batches at the current priority level to return gates before advancing.
- Output: `src/**/*.rs` — `lib.rs`, `Cargo.toml`, and `types.rs` written only by scaffold batch; each capability module file owned by exactly one batch (declared in `rust_target`)
- Each subagent reads spec's REQ/INV sections (ignores Test Specification), reads C source, writes Rust code, compiles, fixes compile errors (≤3 attempts)
- Gate: `PHASE_PASS`/`PHASE_BLOCKED`/`PHASE_DEGRADED`

### Phase 5b — Unit Test (Test + Debug)

- Subagent: `work/subagent/c2r-05b-unit-test.md`
- Uses the SAME batch definitions from `implement-plan.md` as Phase 5a
- Runs AFTER all Phase 5a batches complete (all priority levels)
- **Dispatch**: Same P0→P1→P2 grouping as 5a, but without scaffold batch concerns (infrastructure files already written)
- Each subagent reads the spec's **Test Specification** section (concrete inputs/outputs), reads the compiled Rust source (NOT C source), writes unit tests, runs tests, fixes bugs (≤3 attempts for test + implementation bugs)
- Output: `tests/<capability>_tests.rs` — one test file per capability
- Gate: `PHASE_PASS`/`PHASE_BLOCKED`/`PHASE_DEGRADED`

### Phase 6 — Test (Integration)
- Subagent: `work/subagent/c2r-06-test.md`
- Runs AFTER all Phase 5b batches complete
- Writes integration tests that span multiple capabilities — unit tests were already written per-capability in Phase 5b
- Output: `tests/**/*.rs`
- Gate: `PHASE_PASS`/`PHASE_BLOCKED`/`PHASE_DEGRADED`

### Phase 7 — Repair
- Subagent: `work/subagent/c2r-07-repair.md`
- Output: fixed source/test files + repair log
- Max rounds: 5
- Gate: `PHASE_PASS`/`PHASE_BLOCKED`/`PHASE_DEGRADED`

### Phase 8 — Semantic Audit
- Subagent: `work/subagent/c2r-08-semantic-audit.md`
- Output: invariant test files + audit report
- Gate: `PHASE_PASS`/`PHASE_BLOCKED`/`PHASE_DEGRADED`

### Phase 9 — Quality Gates
- Subagent: `work/subagent/c2r-09-quality-gates.md`
- Checks: unsafe ratio, fault injection, neutrality audit
- Gate: `PHASE_PASS`/`PHASE_BLOCKED`/`PHASE_DEGRADED`

### Phase 10 — Finalize
- Output: `result/output.md`, `result/issues/00-summary.md`
- Gate: `READY_FOR_EVALUATION`/`BLOCKED_WITH_REPORT`

## Subagent Dispatch Protocol

1. DO NOT read `work/subagent/c2r-*.md` files into the main context.
2. Construct the Agent tool prompt using ONLY this format:

```
Execute <subagent_prompt_path> with:
KEY1=VALUE1
KEY2=VALUE2
```

3. The subagent reads its own prompt file from disk. The main agent only receives back a gate token + one-line summary.

**Gate token compression**: All subagents MUST return only `PHASE_PASS`/`PHASE_BLOCKED`/`PHASE_DEGRADED` plus at most one line of summary. The main agent discards verbose results and extracts only the gate token.

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
Phase 3 ──→ specs/<capability_id>/spec-part-<N>.md (sub-batched by function count)
Phase 4 ──→ tasks.md + implement-plan.md + specs/test-migration/spec.md
Phase 5a ──→ src/**/*.rs (Rust source, compiled)
Phase 5b ──→ tests/<capability>_tests.rs (unit tests)
Phase 6 ──→ tests/**/*.rs (integration tests)
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
