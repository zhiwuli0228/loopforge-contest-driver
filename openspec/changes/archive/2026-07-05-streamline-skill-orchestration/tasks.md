## 1. Strip SKILL.md Phase-Specific Notes to scheduling-only

- [x] 1.1 Phase 0 (Preflight): keep inline verification, remove redundant subagent reference (Phase 0 is Keep inline)
- [x] 1.2 Phase 1 (Understand): reduce to — subagent path, output inventory.json, gate expectation
- [x] 1.3 Phase 2 (Design): reduce to — subagent path, output design.md, gate expectation
- [x] 1.4 Phase 3 (Spec): reduce to — Delegate marker, subagent path, output pattern, gate expectation
- [x] 1.5 Phase 4 (Plan): reduce to — Delegate marker, subagent path, output pattern, gate expectation
- [x] 1.6 Phase 5 (Implement): keep scheduling algorithm, remove build/test/fix implementation details
- [x] 1.7 Phase 6 (Test): reduce to — subagent path, output pattern, gate expectation
- [x] 1.8 Phase 7 (Repair): reduce to — subagent path, output pattern, gate + max rounds
- [x] 1.9 Phase 8 (Semantic Audit): reduce to — subagent path, output pattern, gate expectation
- [x] 1.10 Phase 9 (Quality Gates): reduce to — subagent path, checks list, gate expectation
- [x] 1.11 Phase 10 (Finalize): keep inline outputs, reduce to — output files, gate expectation

## 2. Add Subagent Dispatch Protocol to SKILL.md

- [x] 2.1 Replace current Context Safety Rules section with hardened "Subagent Dispatch Protocol" containing: (a) DO NOT read `work/subagent/c2r-*.md` into main context, (b) mandatory dispatch template format, (c) gate token compression rule (keep existing)

## 3. Fix loopforge-driver/SKILL.md Phase 3/4 marking

- [x] 3.1 Change line 132 from `Phase 0-4: preflight, understand, design, spec, plan (inline or subagent)` to separate inline/delegated lines matching the delegation table in INSTRUCTION.md
