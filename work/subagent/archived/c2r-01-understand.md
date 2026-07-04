# c2r-01: Understand

## Role

Parse the C source tree and test tree into a structured inventory. Read-only phase. Produces `source-inventory.json`.

## Context You Receive

- `SOURCE_ROOT` — path to C source tree
- `WORK_DIR` — path to work directory (write inventory here)

## SuperPower Rules (this phase only)

- **Allowed tools**: `parse-source`
- **Allowed filesystem**: read `**` (everything under SOURCE_ROOT)
- **Forbidden**: any write operations (tools.py writes the inventory, not you), any source modification

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

Build a comma-separated list of discovered test directory names (not full paths — tools.py resolves them relative to SOURCE_ROOT).

If no test directories found, proceed without `--test-dirs` but flag this as a warning.

### 2. Run parse-source

```
python WORK_DIR/runtime/tools.py parse-source \
  --source-root "SOURCE_ROOT" \
  --test-dirs "tests,test" \
  --work-dir "WORK_DIR" \
  --output "WORK_DIR/source-inventory.json"
```

If no test dirs found, omit `--test-dirs`.

### 3. Read and Verify the Inventory

Read `WORK_DIR/source-inventory.json`. Verify these fields are populated:

| Field | Expected | Critical? |
|-------|----------|-----------|
| `files` | List of .c/.h file paths | Yes — if empty, blocker |
| `source_tests` | List of test file paths | No — warning if empty |
| `test_functions` | List of test function names | No — warning if empty |
| `public_apis` | List of public API functions | Yes |
| `functions` | List of all functions with metadata | Yes |
| `types` | List of struct/enum/typedef | No |
| `call_graph` | List of call edges | No |
| `globals` | List of global variables | No |
| `parse_failures` | List of files that failed to parse | No — warning if non-empty |

### 4. Build Test Migration Checklist

From the `test_functions` list, create a checklist. Each entry:

```
- [ ] <test_function_name> (in <source_file>) → Rust equivalent: ________
```

This checklist will be used by Phase 3 (spec) and Phase 6 (test) to ensure complete C test coverage.

Write the checklist to `WORK_DIR/test-migration-checklist.md`.

### 5. Summarize Key Findings

Note any:
- Parse failures (which files, what went wrong)
- Ambiguous public API boundaries
- Conditional compilation (`#ifdef`, `#ifndef`) that may affect module boundaries
- Heavy macro usage that complicates translation
- File I/O or platform-specific code

## Output

1. `WORK_DIR/source-inventory.json` — structured parse data (written by tools.py)
2. `WORK_DIR/test-migration-checklist.md` — C test function checklist (written by you)
3. Summary in your return message: file count, function count, test function count, warnings

## Gate

- `PHASE_PASS` — inventory has files + functions, test_functions extracted (even if 0)
- `PHASE_BLOCKED` — `files` is empty (no C source found or parse completely failed)
- `PHASE_DEGRADED` — parse failures on some files, or no test functions found
