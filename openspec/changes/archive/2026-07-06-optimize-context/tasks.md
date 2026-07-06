## 1. Update delegation strategy in SKILL.md

- [x] 1.1 Change Phase 3 (Spec) description from inline to delegated: add "Delegate to `work/subagent/c2r-03-spec.md`", remove inline spec-writing instructions, specify main agent only passes context variables and receives gate token
- [x] 1.2 Change Phase 4 (Plan) description from inline to delegated: add "Delegate to `work/subagent/c2r-04-plan.md`", remove inline plan-writing instructions
- [x] 1.3 Replace Phase 5 (Implement) description with dynamic scheduling algorithm: parse `implement-plan.md` for batch discovery, group by priority (P0/P1/P2), dispatch one subagent per batch, parallel dispatch for independent batches at same priority level, each subagent references `c2r-05-implement.md` by file path with only BATCH_ID and context variables
- [x] 1.4 Add context-safety rule block: "The main agent MUST NOT write Rust source files, Cargo.toml, spec files, or plan files. These writes SHALL only occur inside subagents. Subagent prompts MUST reference the subagent prompt file by path, not inline-construct prompts."
- [x] 1.5 Add gate token compression rule: all subagents MUST return only `PHASE_PASS`/`PHASE_BLOCKED`/`PHASE_DEGRADED` plus one-line summary

## 2. Update delegation table in INSTRUCTION.md

- [x] 2.1 Change Phase 3 row from "Keep inline" to "Delegate" with rationale: "Writes one spec per capability — can produce 10+ files"
- [x] 2.2 Change Phase 4 row from "Keep inline" to "Delegate" with rationale: "Produces tasks.md and implement-plan.md — content scales with batch count"
- [x] 2.3 Update Phase 5 row to include dynamic scheduling note: "One subagent per batch, parallel at same priority level, prompt file reference only"

## 3. Update SuperPower guards

- [x] 3.1 Remove `write` operations from the `spec` phase guard in `work/profiles/superpower/c-to-rust-migration-guards.yaml` (main agent delegates, subagent has its own rules)
- [x] 3.2 Remove `write` operations from the `plan` phase guard (same rationale)

## 4. Validation

- [x] 4.1 Verify all referenced subagent prompt files (c2r-03-spec.md, c2r-04-plan.md, c2r-05-implement.md) exist and are complete
- [x] 4.2 Review SKILL.md changes for internal consistency: Phase 0, 1, 2, 10 remain inline; Phase 3, 4, 5, 6, 7, 8, 9 are delegated; delegation strategy is consistent across SKILL.md and INSTRUCTION.md
