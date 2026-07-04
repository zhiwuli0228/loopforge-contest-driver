# c2r-01: Understand

## Role

Parse the C source tree AND test tree, produce a structured source inventory and test inventory. Read-only phase — no writes allowed.

## Context

You receive:
- `SOURCE_ROOT` — path to the C source tree
- `WORK_DIR` — path to the work directory

## SuperPower Rules

Read `work/profiles/superpower/c-to-rust-migration-guards.yaml`, section `understand`.

- **Allowed tools**: `parse-source`
- **Allowed filesystem**: read `**` (everything)
- **Forbidden**: any write operations, any source modification

## Steps

1. **Discover test directories**: Look under `SOURCE_ROOT` for directories named `tests`, `test`, `unit`, `spec`, or similar. Common patterns: `tests/`, `tests/unit/`, `test/`.
2. Run `python tools.py parse-source --source-root SOURCE_ROOT --test-dirs "dir1,dir2" --work-dir WORK_DIR`
   - Pass all discovered test directories as comma-separated values to `--test-dirs`
   - If no test directory found, omit `--test-dirs` but report this as a warning
3. Read the generated output. Confirm both `source_tests` (test file list) and `test_functions` (individual test function names) are populated.
4. Review the inventory: public APIs, structs, macros, include graph, file and I/O boundaries
5. **Review the test inventory**: For each `test_function`, note its name and source file. This becomes the **Test Migration Checklist** — every entry must have a Rust equivalent or an explicit N/A reason.

## Output

The tools.py command produces structured JSON. Your job is to:
- Confirm the source inventory is complete and accurate
- Confirm the test inventory is complete: count C test functions, list them all
- Flag any ambiguities (e.g., unclear public API boundaries, conditional compilation)
- Summarize key findings including the **Test Migration Checklist**

The test migration checklist is critical — it is the contract that Phase 6 (test) will verify against.

## Gate

Return one of:
- `PHASE_PASS` — source and test inventories complete, test functions extracted
- `PHASE_BLOCKED` — no C source found, or parse failed critically
- `PHASE_DEGRADED` — partial parse (e.g., some files had parse errors, test functions partially extracted)
