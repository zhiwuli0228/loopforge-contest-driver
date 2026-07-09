# c2r-03: Spec (Partial — One Sub-Batch of One Capability)

## Role

Write ONE PART of a capability specification. A large capability is split into multiple sub-batches by function count — each sub-batch writes spec content for 2–4 functions. You do NOT write the entire capability spec. You do NOT write the test-migration spec.

## Why Batched

A single capability may have 8+ key functions. Writing all Requirements (3 scenarios each = 24+ scenarios) and all Test Specifications (3 test cases each = 24+ test cases with concrete Rust values) in one subagent causes context explosion. By splitting into sub-batches of 2–4 functions, each subagent writes at most 12 scenarios + 12 test cases — well within context budget.

## Context You Receive

- `OPENSPEC_CHANGE` — OpenSpec change name
- `SOURCE_ROOT` — absolute path to C source tree
- `WORK_DIR` — absolute path to work directory
- `CAPABILITY_ID` — derived from the C source file name (e.g., `fdb_kvdb` from `src/fdb_kvdb.c`). This is the file-group name, NOT a single capability map entry.
- `FUNCTION_SUBSET` — JSON array of function names you are responsible for. e.g., `["_fdb_kvdb_init", "_fdb_kvdb_set", "_fdb_kvdb_get"]`. These are the `apis[0]` values from capability map entries that belong to this file-group.
- `PART_INDEX` — which part you are (1-based). Part 1 writes shared sections (Overview, Data Structures, Invariants, Dependencies). Parts 2+ write only their function Requirements and Test Specifications.
- `PRIOR_OUTPUTS.inventory` — absolute path to `source-inventory.json`
- `PRIOR_OUTPUTS.design` — absolute path to `design.md` from Phase 2
- `PRIOR_OUTPUTS.capability_map` — absolute path to `01c-capability-map.json`

## SuperPower Rules (this phase only)

- **Allowed tools**: none (pure agent reasoning + file writes)
- **Allowed filesystem**: read `**`, write `openspec/changes/*/specs/<CAPABILITY_ID>/spec-part-<PART_INDEX>.md`
- **Forbidden**: modify source code, modify tools.py, modify profiles, write other parts' spec files

## Steps

### 1. Read Your Assignment

Read `01c-capability-map.json`. Your `CAPABILITY_ID` maps to a C source file (e.g., `fdb_kvdb` → `src/fdb_kvdb.c`). Find ALL capability entries whose `evidence[0].file` matches this source file. From those entries, extract only the ones whose `apis[0]` is in your `FUNCTION_SUBSET`.

From the matching entries, extract:
- `apis[0]` — the function name
- `behaviors` — behavior classification (mutation, init, query, etc.)
- `state_effects` — what state changes this function causes
- `evidence[0].file` and `evidence[0].symbol` — C source location

If no capability map entries match your source file, return `PHASE_BLOCKED`.

### 2. Read Design (Scoped)

Read `design.md` — only the sections relevant to your capability's types and module mapping. Skip unrelated sections.

If `PART_INDEX` is 1, also note the overall architectural notes for the Capability Overview.

### 3. Read C Source (Scoped to Your File-Group)

Read the C source file for your file-group: `SOURCE_ROOT/<CAPABILITY_ID>.c` (e.g., `SOURCE_ROOT/src/fdb_kvdb.c`). You may also read the corresponding header `SOURCE_ROOT/inc/<CAPABILITY_ID>.h` if it exists. Focus ONLY on the functions in `FUNCTION_SUBSET`:
- Find each function's signature, body, and location (file:line)
- Trace error return paths
- Note side effects (global writes, file I/O)
- Note data structures used (parameters, return types, internal structs)

Do NOT deeply analyze functions outside `FUNCTION_SUBSET` — they belong to other sub-batches.

### 4. Write Your Spec Part

Create your spec part file at:

```
openspec/changes/OPENSPEC_CHANGE/specs/<CAPABILITY_ID>/spec-part-<PART_INDEX>.md
```

The file structure depends on `PART_INDEX`:

---

**If PART_INDEX == 1** (first part — includes shared sections):

```markdown
# Spec: <CAPABILITY_ID> (Part 1 of N)

## Capability Overview
<One paragraph. Describe the role of this C source module in the system — what it does based on the functions it contains.>

## Data Structures
| C Struct | Fields | Rust Equivalent | Notes |
|----------|--------|----------------|-------|
| <structs used by functions in this part> |

## Requirements — <function_name>
REQ-<capability-id>-001: <function_name> SHALL <behavior>
  C source reference: [file:line]
  
  Scenario (normal path):
    GIVEN <state>
    WHEN <operation>
    THEN <expected result>
  
  Scenario (error path):
    GIVEN <error state>
    WHEN <operation>
    THEN <error behavior>
  
  Scenario (boundary condition):
    GIVEN <boundary state>
    WHEN <operation>
    THEN <boundary behavior>

## Requirements — <next_function>
...

## Test Specification — Phase 5b Contract
### Test Cases: <function_name>
| # | Type | Input | Expected Output | Setup |
|---|------|-------|-----------------|-------|
| 1 | normal | <Rust literal> | <Rust value/pattern> | <setup> |
| 2 | error  | <Rust literal> | <Rust error variant> | <setup> |
| 3 | boundary | <Rust literal> | <Rust value/pattern> | <setup> |

### Test Cases: <next_function>
...

## Invariants
INV-<capability-id>-001: ...
INV-<capability-id>-002: ...

## Dependencies
<List other file-groups (C source modules) that this module calls into. Identify cross-file function calls from your C source analysis.>
```

---

**If PART_INDEX >= 2** (subsequent parts — function content only):

```markdown
# Spec: <CAPABILITY_ID> (Part N of M)

## Requirements — <function_name>
<same format as above>

## Test Specification — Phase 5b Contract
### Test Cases: <function_name>
<same format as above>
```

**No Overview, Data Structures, Invariants, or Dependencies** — these are in Part 1 only.

### 5. Content Rules

**Requirements**: Every function in your `FUNCTION_SUBSET` MUST have a REQ entry with exactly 3 scenarios (normal, error, boundary). If a scenario type is not applicable, write "N/A — <reason>".

**Test Specification**: Every function MUST have a test case table with exactly 3 cases (normal, error, boundary). All values MUST use Rust literal syntax:
- Input: `Config { sector_size: 4096 }`, `b"key".to_vec()`, `"/tmp/test.db"`
- Expected Output: `Ok(())`, `Err(Error::InvalidConfig)`, `Ok(42)`
- No C syntax leakage: no `NULL`, no `int`, no `{0}`, no `malloc`

**Function limit**: You write spec for at most 4 functions. If `FUNCTION_SUBSET` has more, return `PHASE_BLOCKED` — the orchestrator misconfigured your batch.

### 6. Self-Check

Verify before returning:
- [ ] Every function in `FUNCTION_SUBSET` has a REQ entry with 3 scenarios
- [ ] Every function has a Test Specification table with 3 concrete test cases
- [ ] All values use Rust syntax (no `NULL`, `int`, `{0}`, C types)
- [ ] If PART_INDEX == 1: Capability Overview, Data Structures, Invariants, and Dependencies are present
- [ ] If PART_INDEX >= 2: No Overview, Data Structures, Invariants, or Dependencies sections

## Output

```
openspec/changes/OPENSPEC_CHANGE/specs/<CAPABILITY_ID>/spec-part-<PART_INDEX>.md
```

Phase 4 (Plan) reads all `spec-part-*.md` files for a capability and treats them as one logical spec.

## Gate

- `PHASE_PASS` — spec part written, every function in FUNCTION_SUBSET has ≥3 scenarios AND ≥3 concrete test cases with Rust syntax
- `PHASE_BLOCKED` — CAPABILITY_ID not found, FUNCTION_SUBSET too large (>4), C source unreadable, design.md missing
- `PHASE_DEGRADED` — spec written but some functions lack complete scenarios or test cases lack concrete values
