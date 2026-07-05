# c2r-01a: Mechanical Source Inventory

## Role

Run `tools.py parse-source` to produce a structured source inventory. Mechanical-only phase — you do NOT read C source files. Your only job is to run the parse command and verify the output has the required fields.

## Context You Receive

- `SOURCE_ROOT` — absolute path to C source tree
- `WORK_DIR` — absolute path to work directory

## SuperPower Rules (this phase only)

- **Allowed tools**: `parse-source`
- **Allowed filesystem**: read `**`, write `logs/trace/c-to-rust/**`
- **Forbidden**: modify C source files, modify tools.py, modify profiles, modify openspec/, modify work/output/

## Steps

### 1. Discover Test Directories

Search under `SOURCE_ROOT` for test directories. Common patterns:

```
tests/  test/  unit/  spec/  t/  testing/
```

Check each with:

```
test -d "SOURCE_ROOT/tests" && echo "tests/"
test -d "SOURCE_ROOT/test" && echo "test/"
test -d "SOURCE_ROOT/unit" && echo "unit/"
```

Build a comma-separated list of discovered test directory names. If no test directories found, proceed without `--test-dirs`.

### 2. Run parse-source

```
python WORK_DIR/runtime/tools.py parse-source \
  --source-root "SOURCE_ROOT" \
  --test-dirs "tests,test" \
  --work-dir "WORK_DIR" \
  --output "WORK_DIR/logs/trace/c-to-rust/01a-source-inventory.json"
```

If no test dirs found, omit `--test-dirs`.

### 3. Verify Output Completeness

Read `WORK_DIR/logs/trace/c-to-rust/01a-source-inventory.json`. Verify these fields:

| Field | Expected | Action if empty |
|-------|----------|-----------------|
| `files` | Non-empty list of .c/.h paths | BLOCKED — no C source found |
| `functions` | List of function objects | Warning — may indicate parse failure |
| `public_apis` | List of public API declarations | Warning |
| `test_functions` | List of test function names | Warning — no C tests to migrate |
| `types` | List of struct/enum/typedef | Warning |
| `parse_failures` | List of failed files | Warning per failure |

### 4. Count Modules

From the `files` list, count distinct C source modules (`.c` files, excluding test files). This count determines how many 01b parallel instances will be spawned.

Report in your return summary:
```
Module count: N
Module list: fdb_kvdb.c, fdb_tsdb.c, ...
Test function count: M
Parse failures: 0 (or list each)
```

## Output

The parse-source tool writes `logs/trace/c-to-rust/01a-source-inventory.json`. You do not write additional files.

## Gate

- `PHASE_PASS` — `files` is non-empty, `functions` is non-empty, JSON is valid
- `PHASE_BLOCKED` — `files` is empty (no C source found) or parse-source command failed
- `PHASE_DEGRADED` — parse failures on some files, or no test functions found
