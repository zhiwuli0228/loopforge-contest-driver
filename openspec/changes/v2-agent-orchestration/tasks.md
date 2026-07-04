## 1. SKILL.md Orchestration Prompt

- [x] 1.1 Create `work/skills/c-to-rust-migration-v2/SKILL.md` with the 10-phase sequencing logic, subagent delegation pattern, gate checking, and tools.py integration

## 2. Thinking Phase Subagents (Phases 0-4)

- [x] 2.1 Create `work/subagent/c2r-00-preflight.md` — environment check, tools.py self-check, file existence verification
- [x] 2.2 Create `work/subagent/c2r-01-understand.md` — source parsing via `tools.py parse-source`, source inventory generation
- [x] 2.3 Create `work/subagent/c2r-02-design.md` — technical design document creation using OpenSpec instructions
- [x] 2.4 Create `work/subagent/c2r-03-spec.md` — module-level spec generation using OpenSpec instructions
- [x] 2.5 Create `work/subagent/c2r-04-plan.md` — implementation task list and batch plan using OpenSpec instructions

## 3. Execution Phase Subagents (Phases 5-8)

- [x] 3.1 Create `work/subagent/c2r-05-implement.md` — Rust code generation per batch, `tools.py run-verification` for build
- [x] 3.2 Create `work/subagent/c2r-06-test.md` — test writing per batch, `tools.py run-verification` for test
- [x] 3.3 Create `work/subagent/c2r-07-repair.md` — build/test failure diagnosis and repair loop
- [x] 3.4 Create `work/subagent/c2r-08-semantic-audit.md` — invariant test writing and execution

## 4. Finalization Phase Subagents (Phases 9-10)

- [x] 4.1 Create `work/subagent/c2r-09-quality-gates.md` — unsafe ratio, fault injection, neutrality audit via tools.py
- [x] 4.2 Create `work/subagent/c2r-10-finalize.md` — result aggregation, final report generation via `tools.py write-report`
