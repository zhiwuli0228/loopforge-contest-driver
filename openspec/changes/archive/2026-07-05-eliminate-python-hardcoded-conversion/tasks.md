## 1. Clean source_analysis.py — remove body_kind logic

- [x] 1.1 Remove SUPPORTED_BODY_KINDS constant and all body_kind classification code from source_analysis.py
- [x] 1.2 Remove translation_status field emission from all function entries
- [x] 1.3 Remove body_value field emission from all function entries
- [x] 1.4 Remove unsupported_reason field emission from function entries
- [x] 1.5 Verify tools.py parse-source output no longer contains body_kind/translation_status/body_value fields
- [x] 1.6 Update tools.py cmd_parse_source to remove any body_kind-related field extraction

## 2. Delete hardcoded Python conversion files

- [x] 2.1 Delete work/runtime/c2rust_project_generator.py (930 lines of hardcoded C-to-Rust rendering)
- [x] 2.2 Delete work/runtime/c2rust_analysis.py (body_kind classifier, translation_status marker)
- [x] 2.3 Delete work/runtime/c2rust_repair.py (Python repair loop)
- [x] 2.4 Delete work/runtime/c2rust_semantic_repair.py (Python semantic repair)
- [x] 2.5 Delete work/runtime/c2rust_semantic_audit.py (hardcoded semantic audit)
- [x] 2.6 Delete work/runtime/c2rust_invariant_tests.py (hardcoded invariant test rendering)
- [x] 2.7 Delete work/runtime/opencode_repair_provider.py (V1 opencode bridge)
- [x] 2.8 Delete work/runtime/generation_agent_provider.py (V1 LLM bridge)
- [x] 2.9 Delete corresponding test files: test_c2rust_analysis.py, test_c2rust_semantic_repair.py, test_generation_agent_provider.py, test_rust_project_generation.py, test_semantic_planning.py, test_self_healing_loop.py (if they solely test deleted functions)

## 3. Rewrite loopforge_runner.py as thin orchestration layer

- [x] 3.1 Strip all imports of deleted modules (c2rust_project_generator, c2rust_analysis, c2rust_repair, c2rust_semantic_repair, c2rust_semantic_audit, c2rust_invariant_tests, opencode_repair_provider, generation_agent_provider)
- [x] 3.2 Keep imports for tools.py commands, semantic_planning.py, rust_project_generation.py validation, test_migration_validation.py, agent_task_packet.py, c_project_root_resolver.py, self_healing_loop.py, check_unsafe_ratio.py
- [x] 3.3 Remove generate_project() call and surrounding generation logic
- [x] 3.4 Remove run_repair_loop() call and repair logic
- [x] 3.5 Remove evaluate_semantic_equivalence() call and semantic audit logic
- [x] 3.6 Remove run_semantic_repair_loop() call
- [x] 3.7 Keep self_check(), ensure_outputs(), create_agent_task_packet()
- [x] 3.8 Add context package output: write all resolved paths (SOURCE_ROOT, WORK_DIR, OUTPUT_DIR, trace files) as structured JSON for Agent consumption
- [x] 3.9 Output instructions telling the Agent to read and execute work/skills/c-to-rust-migration-v2/SKILL.md
- [x] 3.10 Keep final report generation: result/output.md, result/issues/00-summary.md, trace artifacts
- [x] 3.11 Verify runner completes without importing any deleted module

## 4. Update subagent prompts for agent-first generation

- [x] 4.1 Update work/subagent/c2r-05-implement.md: remove any reference to body_kind or Python generation; clarify Agent reads C source directly
- [x] 4.2 Update work/subagent/c2r-06-test.md: remove reference to _render_tests(); clarify Agent reads C test source directly
- [x] 4.3 Update work/subagent/c2r-07-repair.md: remove reference to Python repair functions; clarify Agent fixes code by editing files directly
- [x] 4.4 Update work/subagent/c2r-08-semantic-audit.md: remove reference to render_invariant_tests(); clarify Agent derives invariants from C source reading

## 5. Update SKILL.md orchestrator

- [x] 5.1 Update work/skills/c-to-rust-migration-v2/SKILL.md: remove any reference to Python generation functions
- [x] 5.2 Ensure SKILL.md context block passes all absolute paths (SOURCE_ROOT, WORK_DIR, OUTPUT_DIR, PRIOR_OUTPUTS)
- [x] 5.3 Verify SKILL.md phase sequence references correct subagent files

## 6. Update SuperPower guards

- [x] 6.1 Update work/profiles/superpower/c-to-rust-migration-guards.yaml: add subagent field to each phase
- [x] 6.2 Remove any allowed_tools entries that reference deleted Python generation functions
- [x] 6.3 Ensure implement/test phases only allow run-verification as tools.py command

## 7. Clean up loopforge_runner.py trace artifact logic

- [x] 7.1 Remove references to deleted trace artifacts (repair-rounds.json, semantic-invariant-test-map.json, etc. that were produced by deleted Python functions)
- [x] 7.2 Keep trace artifacts produced by tools.py and semantic_planning.py
- [x] 7.3 Ensure verify_generated() does not depend on deleted module outputs

## 8. End-to-end verification

- [x] 8.1 Run tools.py parse-source against FlashDB (SOURCE_ROOT) and verify clean output without body_kind fields
- [x] 8.2 Run semantic_planning.py against parse-source output and verify migration plan is generated
- [x] 8.3 Execute full V2 pipeline via SKILL.md: Phase 0 (preflight) through Phase 10 (finalize)
- [x] 8.4 Verify cargo build --locked passes on generated Rust project
- [x] 8.5 Verify cargo test --locked passes on generated Rust project
- [x] 8.6 Verify result/output.md reports READY_FOR_EVALUATION
- [x] 8.7 Verify result/issues/00-summary.md exists and is well-formed
