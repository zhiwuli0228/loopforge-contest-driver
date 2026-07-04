# c2r-03: Spec

## Role

Create module-level specifications for the migration, including a test migration spec. Write phase — produces `specs/<module>/spec.md` and `specs/test-migration/spec.md`.

## Context

You receive:
- `OPENSPEC_CHANGE` — the OpenSpec change name
- `SOURCE_ROOT` — path to the C source tree
- `WORK_DIR` — path to the work directory
- Phase 1 output: source inventory with `test_functions` list (the Test Migration Checklist)
- Phase 2 output: `design.md` location

## SuperPower Rules

Read `work/profiles/superpower/c-to-rust-migration-guards.yaml`, section `spec`.

- **Allowed tools**: none (pure agent reasoning)
- **Allowed filesystem**: read `**`, write `openspec/changes/*/specs/**/*.md`
- **Forbidden**: modify source code, modify tools.py, modify profiles

## Steps

1. Call `openspec instructions specs --change "OPENSPEC_CHANGE" --json` to get the template and instructions
2. Read `design.md` for the migration approach and module mapping
3. Read the source inventory for the module list and **`test_functions`** list
4. For each module identified in the design:
   - Read the C source files for that module
   - Write a spec file at `specs/<module-name>/spec.md` following the template
   - Each spec defines: requirements (SHALL/MUST), scenarios (WHEN/THEN), invariants
5. **Create `specs/test-migration/spec.md`** — this is the test migration spec:
   - List every C test function from the `test_functions` inventory
   - For each C test, define the corresponding Rust test requirement
   - Group by module (match source module structure from the inventory)
   - Mark any C tests as N/A with a reason if they don't apply (e.g., platform-specific, C-only memory model)
   - Include scenarios for boundary conditions, error paths, and state preservation that may not exist in C tests but are required for semantic equivalence
6. Ensure every capability listed in the proposal has a corresponding spec

## Output

Write spec files under the OpenSpec change directory. Each spec must cover:
- Data structures and their Rust equivalents
- Public API requirements with scenarios
- Behavioral invariants (reset, capacity, error handling, state preservation)
- Edge cases and boundary conditions

**`specs/test-migration/spec.md` must include:**
- A complete mapping table: C test function → Rust test function (or N/A + reason)
- Requirements for each test scenario with WHEN/THEN format
- Additional semantic tests not in C but required for completeness (boundary, error, state preservation)

## Gate

Return one of:
- `PHASE_PASS` — all module specs written, test migration spec complete with full C test coverage mapping
- `PHASE_BLOCKED` — critical information missing for spec creation
- `PHASE_DEGRADED` — some modules have incomplete specs, or test migration mapping is partial
