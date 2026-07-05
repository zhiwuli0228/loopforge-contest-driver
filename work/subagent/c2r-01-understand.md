# c2r-01: Understand

## Role

Parse the C source tree into a structured inventory, analyze each module for functional capabilities, and synthesize a unified capability map with a dependency graph. Read-only phase. Produces `01-source-inventory.json`, `01c-capability-map.json`, and `test-migration-checklist.md`.

## Context You Receive

- `SOURCE_ROOT` — absolute path to C source tree
- `WORK_DIR` — absolute path to work directory

## SuperPower Rules (this phase only)

- **Allowed tools**: `parse-source`
- **Allowed filesystem**: read `**`, write `logs/trace/c-to-rust/**`, write `openspec/changes/*/`
- **Forbidden**: modify C source files, modify tools.py, modify profiles, modify work/output/

## Autonomous Judgment Rules

When identifying capabilities (Step 6), you MUST independently decide what constitutes a "capability." Do NOT ask the user for guidance.

Use these criteria:
1. **Independent state lifecycle**: A group of functions that share and manage a distinct piece of state
2. **Dedicated error paths**: Functions with their own error handling patterns
3. **Algorithm with ≥3 intermediate states**: A multi-step algorithm with distinct phases
4. **Distinct data structure**: A struct with dedicated create/read/update/delete operations

Decision rules:
- At least 1 capability per module. If only 1, explain why.
- Maximum 5 capabilities per module. If more, merge the smallest.
- If unsure whether to split or merge, prefer SPLITTING (synthesis step can merge later).

When synthesizing (Step 7):
- Merge capabilities when: two capabilities from different modules describe the same behavior from different angles
- Priority: P0 = no dependencies, foundational types/constants; P1 = depends on P0, core business logic; P2 = depends on P1 or auxiliary

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
  --output "WORK_DIR/logs/trace/c-to-rust/01-source-inventory.json"
```

If no test dirs found, omit `--test-dirs`.

### 3. Read and Verify the Inventory

Read `WORK_DIR/logs/trace/c-to-rust/01-source-inventory.json`. Verify these fields are populated:

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

Write the checklist to `WORK_DIR/logs/trace/c-to-rust/test-migration-checklist.md`.

### 5. Summarize Key Findings

Note any:
- Parse failures (which files, what went wrong)
- Ambiguous public API boundaries
- Conditional compilation (`#ifdef`, `#ifndef`) that may affect module boundaries
- Heavy macro usage that complicates translation
- File I/O or platform-specific code

### 6. Per-Module Capability Analysis

For each C source module (`.c` file) in the inventory, read the source file and its corresponding header. For each module:

a. **Group functions** by the data they operate on and the state they share. Each group is a candidate capability.

b. **For each candidate capability**, analyze:
   - **Trigger conditions**: What causes this code to execute?
   - **State transitions**: Does the code move through distinct states? Draw them.
   - **Invariants**: What MUST be true before, during, and after execution?
   - **Error paths**: What happens when things go wrong?
   - **Boundary conditions**: What are the edge cases (empty input, full capacity, wrapped counters)?
   - **Test coverage**: Which existing C tests exercise this capability?

c. **Write a scenario document** for each module to `WORK_DIR/logs/trace/c-to-rust/capabilities/<module>-scenarios.md`. Use this structure:

```markdown
# Module Analysis: [filename]

## Module Overview
[One paragraph describing what this module does.]

---

## Capability 1: [Descriptive Name]

### Functions Involved
| C Function | File:Line | Role in this capability |
|------------|-----------|------------------------|
| [func] | [file:line] | [role] |

### Trigger Conditions
[What causes this capability to execute?]

### State Machine
[States and transitions, or "N/A — stateless capability"]

### Invariants
- **INV-001**: [invariant description]
- **INV-002**: [invariant description]

### Error Paths
| Error Condition | Detection Method | Response | Recovery |
|----------------|-----------------|----------|----------|
| [condition] | [how detected] | [response] | [recovery] |

### Boundary Conditions
| Boundary | Value | C Code Handling | Risk if mishandled |
|----------|-------|----------------|-------------------|
| [boundary] | [value] | [handling] | [risk] |

### C Test Coverage
| C Test Function | Test File | What it validates |
|----------------|-----------|------------------|
| [test] | [file] | [coverage] |

---

## Cross-Module Dependencies

### Functions This Module Calls (from other modules)
| Called Function | Defined In | Purpose |
|----------------|-----------|---------|
| [func] | [module] | [purpose] |

### Functions Other Modules Call (from this module)
| Function | Called By | Purpose |
|----------|----------|---------|
| [func] | [module] | [purpose] |
```

### 7. Cross-Module Capability Synthesis

Read all `*-scenarios.md` files from Step 6. Synthesize them into a unified capability map.

a. **Merge near-duplicate capabilities** across modules. When two capabilities from different modules describe the same behavior, merge them.

b. **Assign priorities**:
   - P0: No dependencies. Foundational types, constants, pure functions.
   - P1: Depends only on P0. Core business logic.
   - P2: Depends on P1 or auxiliary. Nice-to-have, debugging, reporting.

c. **Build a dependency graph** (DAG). For each capability, list its dependencies. The graph MUST be a DAG — if capabilities form a cycle, break it by splitting one of them.

d. **Identify test coverage gaps**: which capabilities have zero or partial C test coverage.

### 8. Write the Capability Map

Write `WORK_DIR/logs/trace/c-to-rust/01c-capability-map.json`:

```json
{
  "source_modules": ["list of all module names"],
  "total_scenario_files": N,
  "capabilities": [
    {
      "id": "kebab-case-unique-id",
      "name": "Human-Readable Capability Name",
      "priority": "P0",
      "summary": "One sentence describing what this capability does and why it matters.",
      "source_modules": ["module1", "module2"],
      "scenario_files": ["capabilities/module1-scenarios.md"],
      "key_functions": ["func1", "func2", "func3"],
      "key_data_structures": ["StructA", "EnumB"],
      "is_cross_module": true
    }
  ],
  "dependency_graph": {
    "capability-id-1": [],
    "capability-id-2": ["capability-id-1"]
  },
  "test_coverage_gaps": [
    {
      "capability_id": "capability-id",
      "gap_description": "No C tests cover the error recovery path",
      "severity": "high"
    }
  ],
  "synthesis_notes": {
    "merged_capabilities": [
      {
        "result_id": "merged-id",
        "sources": ["module-a:cap-x", "module-b:cap-y"],
        "reason": "Why merged"
      }
    ],
    "warnings": []
  }
}
```

Validate before declaring success:
- Total capabilities ≥ 3 (else `PHASE_DEGRADED`)
- Every capability has ≥ 1 key function
- Dependency graph is a DAG
- Every module appears in at least one capability
- JSON is valid

## Output

1. `WORK_DIR/logs/trace/c-to-rust/01-source-inventory.json` — structured parse data (written by tools.py)
2. `WORK_DIR/logs/trace/c-to-rust/test-migration-checklist.md` — C test function checklist (written by you)
3. `WORK_DIR/logs/trace/c-to-rust/capabilities/<module>-scenarios.md` — per-module analysis (written by you)
4. `WORK_DIR/logs/trace/c-to-rust/01c-capability-map.json` — unified capability map (written by you)
5. Summary in your return message: file count, function count, capability count, test function count, warnings

## Gate

- `PHASE_PASS` — inventory has files + functions, capability map is valid JSON with ≥ 3 capabilities and DAG, every module covered
- `PHASE_BLOCKED` — `files` is empty (no C source found) or parse completely failed
- `PHASE_DEGRADED` — parse failures on some files, fewer than 3 capabilities, some modules not covered, or no test functions found
