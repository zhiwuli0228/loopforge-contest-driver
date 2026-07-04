---
name: c-to-rust-migration-v2
description: Agent-first C-to-Rust migration — 10-phase orchestration with subagent delegation, SuperPower enforcement, and tools.py data retrieval.
---

# C-to-Rust Migration V2

## Mission

Drive a C-to-Rust migration through 10 sequential phases. Each phase is delegated to a bounded subagent. The agent sequences phases, checks gates, and aborts on blockers.

## Inputs

The agent MUST have:
- `SOURCE_ROOT` — path to the C source tree (read-only)
- `WORK_DIR` — path to the work directory (default: `work/`)
- `OUTPUT_DIR` — path to the Rust output project (derived at runtime)
- OpenSpec change name (for `openspec instructions` calls)

## Phase Sequence

Execute phases 0→10 in order. Do NOT skip or reorder.

| Phase | Name | Subagent File | tools.py Command |
|-------|------|---------------|------------------|
| 0 | preflight | `work/subagent/c2r-00-preflight.md` | `self-check` |
| 1 | understand | `work/subagent/c2r-01-understand.md` | `parse-source` |
| 2 | design | `work/subagent/c2r-02-design.md` | — |
| 3 | spec | `work/subagent/c2r-03-spec.md` | — |
| 4 | plan | `work/subagent/c2r-04-plan.md` | — |
| 5 | implement | `work/subagent/c2r-05-implement.md` | `run-verification` |
| 6 | test | `work/subagent/c2r-06-test.md` | `run-verification` |
| 7 | repair | `work/subagent/c2r-07-repair.md` | `run-verification` |
| 8 | semantic-audit | `work/subagent/c2r-08-semantic-audit.md` | `run-verification` |
| 9 | quality-gates | `work/subagent/c2r-09-quality-gates.md` | `check-unsafe`, `fault-injection`, `neutrality-audit` |
| 10 | finalize | `work/subagent/c2r-10-finalize.md` | `write-report` |

## Phase Execution Protocol

For each phase N (0–10):

### 1. Read SuperPower Guards

Read `work/profiles/superpower/c-to-rust-migration-guards.yaml`. Extract the section for this phase. This defines allowed tools, allowed filesystem operations, and forbidden actions.

### 2. Prepare Subagent Context

Assemble the context to pass to the subagent:
- **Phase name**: the phase identifier (e.g., `preflight`, `implement`)
- **Subagent file path**: from the table above
- **SuperPower rules**: the extracted YAML section for this phase
- **OpenSpec change name**: the current change being worked on
- **SOURCE_ROOT**: path to the C source tree
- **WORK_DIR**: path to the work directory
- **OUTPUT_DIR**: path to the Rust output project
- **Prior phase outputs**: any data or file paths produced by previous phases

### 3. Spawn Subagent

Spawn a subagent using the subagent file path as the prompt. Inject the context from step 2.

The subagent will:
- Read its own prompt file for role definition and instructions
- Read SuperPower rules and enforce them
- Use `python tools.py <command>` for data retrieval (where applicable)
- Read source files, specs, and prior outputs as needed
- Produce its phase output
- Return a gate result

### 4. Check Gate Result

The subagent returns one of:

- **`PHASE_PASS`**: Phase completed successfully. Advance to next phase.
- **`PHASE_BLOCKED`**: Phase cannot proceed. STOP the migration. Report the blocker to the user.
- **`PHASE_DEGRADED`**: Phase completed with issues. Log the warning. Advance to next phase.

### 5. Record Progress

After each phase, update the phase status:
- Record which files were produced
- Record any warnings or degraded status
- Pass relevant output file paths to the next phase as context

## OpenSpec Integration

For phases that produce OpenSpec artifacts (design=2, spec=3, plan=4, implement-plan=5, verification-report=10):

1. Call `openspec instructions <artifact-id> --change "<change-name>" --json`
2. Pass the `template`, `instruction`, and `outputPath` to the subagent
3. The subagent uses these to create properly structured artifacts

## Data Flow

```
Phase 0 (preflight)
  → tools.py self-check → environment data
  → Gate: PHASE_PASS / PHASE_BLOCKED

Phase 1 (understand)
  → Discover test directories under SOURCE_ROOT
  → tools.py parse-source --source-root SOURCE_ROOT --test-dirs "tests,test" --work-dir WORK_DIR
  → source-inventory.json (includes test_functions list)
  → Test Migration Checklist: every C test function must have Rust equivalent
  → Gate: PHASE_PASS / PHASE_BLOCKED

Phase 2 (design)
  → openspec instructions design → template + context
  → Agent writes design.md
  → Gate: PHASE_PASS / PHASE_BLOCKED

Phase 3 (spec)
  → openspec instructions specs → template + context
  → Agent writes specs/<module>/spec.md per module
  → Agent writes specs/test-migration/spec.md (C test → Rust test mapping)
  → Gate: PHASE_PASS / PHASE_BLOCKED

Phase 4 (plan)
  → openspec instructions tasks → template + context
  → Agent writes tasks.md + implement-plan.md
  → Gate: PHASE_PASS / PHASE_BLOCKED

Phase 5 (implement) — per batch
  → Read implement-plan.md for batch assignments
  → Read specs for module requirements
  → Read C source for behavior
  → Write Rust source to OUTPUT_DIR/src/
  → tools.py run-verification --project-dir OUTPUT_DIR --commands '["cargo build --locked"]'
  → Gate: PHASE_PASS / PHASE_DEGRADED / PHASE_BLOCKED

Phase 6 (test) — per batch
  → Read specs/test-migration/spec.md for C test mapping
  → Read specs for test requirements
  → Read C test source for original test logic
  → Write Rust tests to OUTPUT_DIR/tests/ (one per C test + additional semantic tests)
  → Verify: every C test function has Rust equivalent or explicit N/A
  → tools.py run-verification --project-dir OUTPUT_DIR --commands '["cargo test --locked"]'
  → Gate: PHASE_PASS / PHASE_DEGRADED / PHASE_BLOCKED

Phase 7 (repair) — loop until clean or max retries
  → Read cargo errors from Phase 5/6
  → Diagnose and fix
  → tools.py run-verification --project-dir OUTPUT_DIR --commands '["cargo build --locked", "cargo test --locked"]'
  → Gate: PHASE_PASS / PHASE_BLOCKED

Phase 8 (semantic-audit)
  → Read specs for invariants
  → Write invariant tests to OUTPUT_DIR/tests/
  → tools.py run-verification --project-dir OUTPUT_DIR --commands '["cargo test --locked"]'
  → Gate: PHASE_PASS / PHASE_DEGRADED / PHASE_BLOCKED

Phase 9 (quality-gates)
  → tools.py check-unsafe --project-dir OUTPUT_DIR
  → tools.py fault-injection --trace-dir WORK_DIR
  → tools.py neutrality-audit --paths '[...]' --forbidden-terms '[...]'
  → Gate: PHASE_PASS / PHASE_DEGRADED / PHASE_BLOCKED

Phase 10 (finalize)
  → Aggregate all results
  → tools.py write-report --result-dir result --data '...'
  → Gate: PHASE_PASS / PHASE_BLOCKED
```

## Abort Conditions

STOP the migration and report to the user if:
- Phase 0 (preflight) returns `PHASE_BLOCKED`
- Phase 1 (understand) returns `PHASE_BLOCKED` (no source found)
- Phase 5 or 6 returns `PHASE_BLOCKED` (unrecoverable build failure)
- Phase 7 (repair) exhausts retries without passing
- Any subagent returns `PHASE_BLOCKED`

## Completion

Migration is complete when Phase 10 returns `PHASE_PASS`. Final outputs:
- `OUTPUT_DIR/` — the Rust project (Cargo.toml, src/, tests/)
- `result/output.md` — final report
- `result/issues/00-summary.md` — known issues
- `openspec/changes/<name>/verification-report.md` — verification record

Return `READY_FOR_EVALUATION` if all gates pass.
Return `BLOCKED_WITH_REPORT` if any phase blocked.
