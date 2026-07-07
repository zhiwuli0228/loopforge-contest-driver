# c2r-01b: Per-Module Capability Brainstorm

## Role

Deeply analyze ONE C source module and identify its key functional capabilities. You are one of several parallel instances — other instances are analyzing other modules. Your output will be synthesized by 01c into a unified capability map.

## Context You Receive

- `MODULE_SOURCE` — absolute path to one `.c` file (e.g., `/mnt/e/.../FlashDB/src/fdb_kvdb.c`)
- `MODULE_HEADER` — absolute path to the corresponding `.h` file
- `INVENTORY_PATH` — absolute path to `01a-source-inventory.json` (for function list and call graph)
- `WORK_DIR` — absolute path to work directory

**Important**: You are analyzing ONE module. Other subagents are analyzing other modules in parallel. Focus only on your assigned module.

## SuperPower Rules (this phase only)

- **Allowed tools**: none (pure agent reasoning + file writes)
- **Allowed filesystem**: read `**`, write `logs/trace/c-to-rust/capabilities/**`
- **Forbidden**: modify C source files, modify tools.py, modify profiles, modify openspec/, modify work/output/

## Autonomous Judgment Rules

**You MUST independently decide what constitutes a "capability" in your assigned module. Do NOT ask the user for guidance.**

Use these criteria to identify capabilities:

1. **Independent state lifecycle**: A group of functions that share and manage a distinct piece of state (e.g., a cache table, a sector header, a status register)
2. **Dedicated error paths**: Functions with their own error handling patterns distinct from other parts of the code
3. **Algorithm with ≥3 intermediate states**: A multi-step algorithm with distinct phases (e.g., GC: scan → move → erase → reformat)
4. **Distinct data structure**: A struct with dedicated create/read/update/delete operations

**Decision rules**:
- You MUST identify at least 1 capability per module. If only 1, explain why further splitting is not warranted.
- Maximum 5 capabilities per module. If you find more, merge the smallest ones.
- If unsure whether to split or merge, prefer SPLITTING. The 01c synthesize phase can merge later; it cannot split.
- A capability may involve functions from your module's header AND implementation file.

## Steps

### 1. Read the C Source

Read your assigned C source file (`MODULE_SOURCE`) in full. Read the corresponding header file (`MODULE_HEADER`).

### 2. Read the Inventory Data

Read `INVENTORY_PATH`. For your module, extract:
- Which functions belong to this module
- Call relationships (who calls whom within this module, and cross-module calls)
- Types defined or used by this module
- Global state variables

### 3. Identify Function Groups

Group functions by the data they operate on and the state they share. Each group is a candidate capability.

### 4. For Each Candidate Capability, Analyze Deeply

For each capability candidate, read the relevant C functions line-by-line. Identify:

- **Trigger conditions**: What causes this code to execute?
- **State transitions**: Does the code move through distinct states? Draw them.
- **Invariants**: What MUST be true before, during, and after execution?
- **Error paths**: What happens when things go wrong?
- **Boundary conditions**: What are the edge cases (empty input, full capacity, wrapped counters)?
- **Test coverage**: Which existing C tests exercise this capability?

### 5. Write the Scenario Document

Write your output to `WORK_DIR/logs/trace/c-to-rust/capabilities/<module>-scenarios.md`.

Use this EXACT template structure. Every section MUST be filled in. If a section is truly not applicable, write "N/A — [reason]" instead of leaving it empty.

---

```markdown
# Module Analysis: [MODULE_SOURCE filename]

## Module Overview

[One paragraph describing what this module does in the C codebase. What problem does it solve? What is its role in the larger system?]

---

## Capability 1: [Descriptive Name — NOT file-based, e.g., "KV Sector Status Management" not "fdb_kvdb sector code"]

### Functions Involved

| C Function | File:Line | Role in this capability |
|------------|-----------|------------------------|
| [func_name] | [file:line] | [What this function does for this capability] |
| ... | ... | ... |

### Trigger Conditions

[What external events or internal states cause this capability to execute? Examples: "On KV write when current sector is full", "On database initialization", "On cache miss"]

### State Machine

[Describe the states this capability moves through. Draw as text diagram:]

```
INITIAL_STATE → [trigger] → INTERMEDIATE_STATE → [trigger] → FINAL_STATE
```

[If no state machine exists in this capability, write: "N/A — this capability is stateless. Functions are pure transformations without internal state transitions."]

### Invariants

- **INV-001**: [State an invariant that must hold. Example: "Sector store status SHALL only transition forward (UNUSED → EMPTY → USING → FULL), never backward except via erase"]
- **INV-002**: [State another invariant. Minimum 1 invariant per capability.]
- **INV-003**: [...]

### Error Paths

| Error Condition | Detection Method | Response | Recovery |
|----------------|-----------------|----------|----------|
| [e.g., CRC32 mismatch] | [How detected] | [What happens] | [How to recover] |
| ... | ... | ... | ... |

[Minimum 1 error path per capability. If the C code has no explicit error handling for this capability, write: "N/A — C code does not handle errors for this path (crashes/undefined behavior on failure)"]

### Boundary Conditions

| Boundary | Value/Description | C Code Handling | Risk if mishandled |
|----------|------------------|----------------|-------------------|
| [e.g., Maximum KV name length] | [FDB_KV_NAME_MAX] | [How C handles it] | [What breaks] |
| ... | ... | ... | ... |

[Minimum 1 boundary condition per capability.]

### C Test Coverage

| C Test Function | Test File | What it validates for this capability |
|----------------|-----------|--------------------------------------|
| [test_name] | [file:line] | [What aspect of this capability the test covers] |
| ... | ... | ... |

[If no C tests exist for this capability, write: "N/A — no C tests exercise this capability. This is a TEST COVERAGE GAP that must be addressed in the Rust migration."]

---

## Capability 2: [Name]
[... same structure as Capability 1 ...]

---

## Cross-Module Dependencies

### Functions This Module Calls (from other modules)

| Called Function | Defined In (module) | Purpose |
|----------------|---------------------|---------|
| [func] | [other_module.c] | [Why this module needs it] |

### Functions Other Modules Call (from this module)

| Function In This Module | Called By (module) | Purpose |
|------------------------|-------------------|---------|
| [func] | [other_module.c] | [Why they need it] |

[If none in either direction, write "N/A — this module is self-contained with no cross-module dependencies."]
```

---

## Output

Write ONE file:
```
WORK_DIR/logs/trace/c-to-rust/capabilities/<module>-scenarios.md
```

Where `<module>` is derived from your `MODULE_SOURCE` filename (e.g., `fdb_kvdb` → `fdb_kvdb-scenarios.md`).

## Gate

- `PHASE_PASS` — all mandatory sections filled for at least 1 capability, cross-module dependencies listed
- `PHASE_BLOCKED` — C source file unreadable or inventory JSON missing
- `PHASE_DEGRADED` — some sections incomplete, or only 1 capability identified with insufficient justification
