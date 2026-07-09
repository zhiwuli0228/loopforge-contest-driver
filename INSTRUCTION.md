# LoopForge Official Linux Evaluation Entry

This file is the Linux backup of the official root `INSTRUCTION.md`.

## Prerequisites

Required in `PATH`: `bash`, `python3`, `cargo`, `rustc`, and `node` (for OpenSpec).

## Toolchain Setup

The workflow uses [OpenSpec](https://www.npmjs.com/package/@fission-ai/openspec) for schema-driven artifact management. If `openspec` is not globally installed, the bundled fallback handles it automatically.

### Quick check

```bash
bash work/scripts/openspec.sh --version
```

### If openspec is not available globally

The wrapper auto-installs from the bundled tarball when Node.js is present:

```bash
bash work/vendor/openspec/install.sh
```

Verify:

```bash
bash work/scripts/openspec.sh schemas --json
```

### Fallback mode (no Node.js)

If Node.js is unavailable, `work/scripts/openspec.sh` falls back to a bash-based parser that supports: `schemas`, `status`, `instructions`. This is sufficient for the agent to drive the workflow, but with reduced fidelity.

## SuperPower Guards

Before each migration phase, the agent MUST read the permission boundaries:

```text
work/profiles/superpower/c-to-rust-migration-guards.yaml
```

This file defines allowed tools, filesystem access patterns, and forbidden actions per phase. Default-deny: anything not explicitly allowed is forbidden.

## Project Skills

Custom skills are defined under `work/skills/`. The agent should read the relevant skill definition before starting work:

| Skill | Path | Purpose |
|-------|------|---------|
| c-to-rust-migration-v2 | `work/skills/c-to-rust-migration-v2/SKILL.md` | Agent-first 11-phase orchestration with subagent delegation |
| loopforge-driver | `work/skills/loopforge-driver/SKILL.md` | Contest driver entry — reads design README, resolves SOURCE_ROOT, drives unattended run |
| code-implementation | `work/skills/code-implementation/SKILL.md` | Minimal safe code changes from a repair plan, with SuperPower enforcement |

## Subagent Delegation

Heavy phases that read C source, specs, and design docs MUST be delegated to subagents via the Agent tool. Running them inline will cause context explosion. See [Official execution](#official-execution-two-stage-unattended-pipeline) for the phase-by-phase delegation table.

The main context must NOT read C source files, write Rust code, or run cargo commands — those are subagent responsibilities. It only sees gate summaries.

**Why not put the entire loop in one subagent?** A single subagent that spans all 11 phases is fragile: if it fails at Phase 7, there is no checkpoint to resume from. The main context, driving one phase at a time, naturally preserves progress after each phase and can resume from the last completed gate.

## Official execution (two-stage unattended pipeline)

### Stage 1 — Data Preparation (Python, subagent)

Spawn `run.sh` as a subagent. This runs deterministic data extraction only:

```bash
SOURCE_ROOT="E:\001code\csource\FlashDB" bash work/scripts/run.sh --run
```

Stage 1 writes:
- `logs/trace/execution-adapter/state/context-package.json` — all absolute paths and analysis summary
- `result/output.md` — status `AGENT_DELEGATION_READY`
- `logs/trace/run-summary.json` — self-check, source analysis, semantic planning gate results

If Stage 1 returns `BLOCKED_WITH_REPORT`, stop. Do not proceed.

### Stage 2 — Agent Judgment (SKILL.md, main context)

After Stage 1 subagent returns, immediately read the orchestrator skill and execute phases 0→10:

1. Read `work/skills/c-to-rust-migration-v2/SKILL.md`
2. Read `logs/trace/execution-adapter/state/context-package.json` for all paths
3. Execute Phase 0 (preflight) inline — verify context package integrity
4. Execute Phase 1→10, delegating heavy phases as subagents:

| Phase | Delegate? | Reason |
|-------|-----------|--------|
| 0 — Preflight | Keep inline | Lightweight — reads context package, verifies tools |
| 1 — Understand | **Delegate** to `c2r-01-understand.md` | Reads C source + writes capability map — 100K+ tokens |
| 2 — Design | Keep inline | Reads prior summaries, not raw source |
| 3 — Spec | **Delegate** to `c2r-03-spec.md` | Writes one spec per capability — can produce 10+ files |
| 4 — Plan | **Delegate** to `c2r-04-plan.md` | Produces tasks.md and implement-plan.md — content scales with batch count |
| 5 — Implement (per batch) | **Delegate** to `c2r-05-implement.md` | One subagent per batch, parallel at same priority level, prompt file reference only |
| 6 — Test (per batch) | **Delegate** to `c2r-06-test.md` | Reads C tests + writes Rust tests |
| 7 — Repair | **Delegate** to `c2r-07-repair.md` | Reads errors + iterative fix loop |
| 8 — Semantic Audit | **Delegate** to `c2r-08-semantic-audit.md` | Reads C source + specs + writes invariant tests |
| 9 — Quality Gates | **Delegate** to `c2r-09-quality-gates.md` | Read-only data processing |
| 10 — Finalize | Keep inline | Aggregates results + writes reports |

5. After Phase 10, `result/output.md` status is `READY_FOR_EVALUATION` or `BLOCKED_WITH_REPORT`.

Requirements come from the preloaded `work/design/README.md`. The harness does not require a README under `SOURCE_ROOT` and never writes into it.

## Generated Rust project

General location:

```text
work/output/<output_project_name>/
```

Current task:

```text
work/output/flashDB_rust/
```

Manual verification:

```bash
cd work/output/flashDB_rust
cargo build
cargo test -- --nocapture
```

## tools.py — Unified Data Layer

All data retrieval goes through `python work/runtime/tools.py`. It returns raw JSON, never makes pass/fail judgments:

```bash
python work/runtime/tools.py parse-source --source-root /path --work-dir work
python work/runtime/tools.py run-verification --project-dir /path --commands '["cargo build"]'
python work/runtime/tools.py check-unsafe --project-dir /path
python work/runtime/tools.py fault-injection --project-dir /path --trace-dir logs/trace
python work/runtime/tools.py neutrality-audit --paths '["src/**/*.rs"]' --forbidden-terms '["term1","term2"]'
python work/runtime/tools.py write-report --result-dir result --data '{"status":"READY"}'
```

## Reports and completion

```text
result/output.md
result/issues/00-summary.md
logs/interaction.md
logs/trace/
logs/trace/c-to-rust/semantic-audit-report.md
```

Completion status is `READY_FOR_EVALUATION` or `BLOCKED_WITH_REPORT`.

When READY, `result/output.md` should point to:

```text
rust_project: work/output/flashDB_rust
cargo_toml: work/output/flashDB_rust/Cargo.toml
semantic_audit_report: logs/trace/c-to-rust/semantic-audit-report.md
```
