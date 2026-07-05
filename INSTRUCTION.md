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

## Subagent Delegation (Required)

The main context acts as a lightweight orchestrator — it sequences phases, passes `PRIOR_OUTPUTS`, checks gate results, and aborts on blockers.

Heavy phases that read C source, specs, and design docs MUST be delegated to subagents via the Agent tool. Running them inline will cause context explosion.

| Phase | Delegate? | Reason |
|-------|-----------|--------|
| 0 — Preflight | Keep inline | Lightweight — env checks only, < 2K tokens |
| 1 — Understand | **Delegate** to `c2r-01-understand.md` | Reads all C source + writes capability map — 100K+ tokens |
| 2 — Design | Keep inline | Reads prior summaries, not raw source |
| 3 — Spec | Keep inline | Reads capability map + writes specs — moderate but structured |
| 4 — Plan | Keep inline | Reads specs + writes task lists — moderate |
| 5 — Implement (per batch) | **Delegate** to `c2r-05-implement.md` | Reads C source + specs + writes Rust code — highest load |
| 6 — Test (per batch) | **Delegate** to `c2r-06-test.md` | Reads C tests + writes Rust tests — high load |
| 7 — Repair | **Delegate** to `c2r-07-repair.md` | Reads all errors + iterative fix loop |
| 8 — Semantic Audit | **Delegate** to `c2r-08-semantic-audit.md` | Reads C source + specs + writes invariant tests |
| 9 — Quality Gates | **Delegate** to `c2r-09-quality-gates.md` | Read-only data processing but heavy |
| 10 — Finalize | Keep inline | Aggregates gate results + writes reports |

The main context must NOT read C source files, write Rust code, or run cargo commands — those are subagent responsibilities. It only sees gate summaries.

**Why not put the entire loop in one subagent?** A single subagent that spans all 11 phases is fragile: if it fails at Phase 7, there is no checkpoint to resume from. The main context, driving one phase at a time, naturally preserves progress after each phase and can resume from the last completed gate.

## Official execution

The orchestrator spawns `run.sh` as a subagent to keep the main context clean. After it returns, the orchestrator drives phases 0→10 sequentially from the main context, delegating only heavy phases as listed above.

```bash
SOURCE_ROOT="/home/lzw/loopforge-e2e/FlashDB" bash work/scripts/run.sh --run
```

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
