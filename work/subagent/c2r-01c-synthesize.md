# c2r-01c: Cross-Module Capability Synthesis

## Role

Read the per-module scenario documents produced by 01b instances and synthesize them into a unified capability map. Identify cross-module capabilities, merge near-duplicates, assign priorities, and build a dependency graph.

**Critical rule**: You read only the 01b summary documents. Do NOT read C source files. Trust the 01b subagents' analysis.

## Context You Receive

- `SCENARIOS_DIR` — path to `logs/trace/c-to-rust/capabilities/` containing all `*-scenarios.md` files
- `INVENTORY_PATH` — path to `01a-source-inventory.json`
- `WORK_DIR` — path to work directory

## SuperPower Rules (this phase only)

- **Allowed tools**: none (pure agent reasoning + file writes)
- **Allowed filesystem**: read `**`, write `logs/trace/c-to-rust/**`, write `openspec/changes/*/`
- **Forbidden**: modify C source files, modify tools.py, modify profiles, modify work/output/

## Autonomous Judgment Rules

**You MUST independently make synthesis decisions. Do NOT ask the user for guidance.**

- Merge capabilities when: two capabilities from different modules describe the same behavior from different angles (e.g., kvdb's "sector allocation" and file's "sector file path" are both about sector storage)
- Split is not your job — 01b already split. Your job is to merge and prioritize.
- Priority assignment rules (see Step 3)

## Steps

### 1. Read All Scenario Documents

Read every `*-scenarios.md` file in `SCENARIOS_DIR`. For each, extract:
- Module name
- Number of capabilities identified
- Capability names and their key functions
- Cross-module dependency lists

### 2. Identify Cross-Module Capabilities

Compare capability descriptions across modules. When you find related capabilities:

```
Module A, Capability X: "Sector Status Management" — manages sector store/dirty status
Module B, Capability Y: "Flash Erase Operations" — erases sectors by filling 0xFF

→ Merged capability: "Sector Lifecycle Management"
  Source modules: [A, B]
  Reason: These capabilities represent the full lifecycle of a sector (format → use → fill → erase). Implementing one without the other breaks sector state consistency.
```

Cross-module indicators to look for:
- One module's "called functions" matches another module's "functions other modules call"
- Capabilities in different modules that operate on the same data structure or flash address range
- Capabilities that form a sequential pipeline (e.g., "CRC32 compute" → "CRC32 verify" in different modules)

### 3. Assign Priorities

| Priority | Criteria | Examples |
|----------|----------|----------|
| P0 | No dependencies on other capabilities. Foundational types, constants, pure functions. | CRC32 computation, error types, status table primitives, write-granularity types |
| P1 | Depends only on P0 capabilities. Core business logic. | KV CRUD, sector formatting, file I/O, TSDB append |
| P2 | Depends on P1 or is auxiliary. Nice-to-have, debugging, reporting. | KV print, set_default, control commands, iterator |

### 4. Build Dependency Graph

For each capability, list which other capabilities it depends on:

```
"kv-crud" depends on: ["status-table-machine", "crc32-integrity", "file-io"]
"garbage-collection" depends on: ["kv-crud", "sector-lifecycle", "file-io"]
```

The graph MUST be a DAG (no cycles). If 01b outputs suggest a cycle, break it by splitting one of the capabilities.

### 5. Identify Test Coverage Gaps

Compare capabilities against the C test inventory from `INVENTORY_PATH`:

- Which capabilities have zero C test coverage?
- Which capabilities have only partial coverage (some scenarios tested, some not)?
- Flag these as test coverage gaps.

### 6. Write the Capability Map

Write `WORK_DIR/logs/trace/c-to-rust/01c-capability-map.json`. Use this EXACT structure:

```json
{
  "source_modules": ["list of all module names from 01b"],
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
    "capability-id-2": ["capability-id-1"],
    "capability-id-3": ["capability-id-1", "capability-id-2"]
  },
  "test_coverage_gaps": [
    {
      "capability_id": "capability-id",
      "gap_description": "No C tests cover the error recovery path for this capability",
      "severity": "high|medium|low"
    }
  ],
  "synthesis_notes": {
    "merged_capabilities": [
      {
        "result_id": "merged-capability-id",
        "sources": ["module-a:capability-x", "module-b:capability-y"],
        "reason": "Why these were merged"
      }
    ],
    "warnings": ["Any concerns about 01b analysis quality or completeness"]
  }
}
```

### 7. Validate Before Reporting

Before declaring success, verify:

| Check | Action if fails |
|-------|----------------|
| Total capabilities ≥ 3 | Report `PHASE_DEGRADED` if fewer — analysis depth may be insufficient |
| Every capability has ≥ 1 key function | Fix — incomplete capability definition |
| Dependency graph is a DAG | Break cycles by splitting capabilities |
| Every 01b module appears in at least one capability | Report `PHASE_DEGRADED` — module not covered |
| JSON is valid | Fix syntax errors |

## Output

Write ONE file:
```
WORK_DIR/logs/trace/c-to-rust/01c-capability-map.json
```

## Gate

- `PHASE_PASS` — valid JSON, ≥ 3 capabilities, dependency graph is a DAG, all modules covered
- `PHASE_BLOCKED` — no 01b scenario files found or all are unreadable
- `PHASE_DEGRADED` — fewer than 3 capabilities, or some modules not covered, or JSON has warnings
