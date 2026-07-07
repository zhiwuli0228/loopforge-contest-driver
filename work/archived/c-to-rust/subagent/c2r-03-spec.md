# c2r-03: Spec

## Role

Create capability-level specifications driven by the brainstorm capability map. Write phase — produces one `specs/<capability-id>/spec.md` per capability, plus `specs/test-migration/spec.md`.

## Context You Receive

- `OPENSPEC_CHANGE` — OpenSpec change name
- `SOURCE_ROOT` — absolute path to C source tree
- `WORK_DIR` — absolute path to work directory
- `PRIOR_OUTPUTS.inventory` — absolute path to `01-source-inventory.json` (includes `test_functions`)
- `PRIOR_OUTPUTS.design` — absolute path to `design.md` from Phase 2
- `PRIOR_OUTPUTS.capability_map` — (OPTIONAL) absolute path to `01c-capability-map.json` from Phase 1. If provided, use capability IDs, dependency graph, and priorities from the map. If NOT provided, derive capabilities from the proposal's Capabilities section and the design's module mapping.

## SuperPower Rules (this phase only)

- **Allowed tools**: none (pure agent reasoning + file writes)
- **Allowed filesystem**: read `**`, write `openspec/changes/*/specs/**/*.md`
- **Forbidden**: modify source code, modify tools.py, modify profiles

## Steps

### 1. Get OpenSpec Template

```
openspec instructions specs --change "OPENSPEC_CHANGE" --json
```

If openspec unavailable, create specs at `openspec/changes/OPENSPEC_CHANGE/specs/`.

### 2. Read Design, Inventory, and Capability Map (if available)

Read `design.md` for overall architecture and type mapping.
Read `source-inventory.json` for `test_functions` list and module structure.
If available, read `01c-capability-map.json` for the authoritative list of capabilities, their priorities, and dependencies.

### 3. Write Per-Capability Specs

**If capability map is available**: For EACH capability in `01c-capability-map.json`, create a spec at:

```
openspec/changes/OPENSPEC_CHANGE/specs/<capability-id>/spec.md
```

The `<capability-id>` MUST be the exact `id` from the capability map (kebab-case).

Read the C source files listed in the capability's `source_modules` and `scenario_files` fields. Focus ONLY on the functions listed in `key_functions`.

**If capability map is NOT available**: For each capability listed in the proposal's Capabilities section, create a spec at:

```
openspec/changes/OPENSPEC_CHANGE/specs/<capability-name>/spec.md
```

Use the kebab-case name from the proposal. Read the C source files mapped to this capability in the design's module mapping.

Each capability spec MUST contain these sections (apply regardless of input source):

**Capability Overview**: One paragraph on what this capability does. Reference the capability map's `summary` and expand.

**Key Functions** (table):
| C Function | C File:Line | Rust Equivalent | Behavior Summary |
|------------|-------------|-----------------|------------------|
| [func] | [file:line] | `fn [name](...) -> ...` | [1-line summary] |

**Data Structures** (table):
| C Struct | Fields | Rust Equivalent | Notes |
|----------|--------|----------------|-------|
| [struct] | [fields] | [rust struct with fields] | [ownership notes, repr(C) if needed] |

**Requirements** (each with SHALL/MUST):
```
REQ-<capability-id>-001: <function-name> SHALL <behavior description>
  C source reference: [file:line]
  
  Scenario (normal path):
    GIVEN [precondition state]
    WHEN [operation is performed]
    THEN [expected result, return value, state change]
  
  Scenario (error path):
    GIVEN [error precondition]
    WHEN [operation is performed]
    THEN [error handling behavior, error return value]
  
  Scenario (boundary condition):
    GIVEN [boundary state]
    WHEN [operation is performed]
    THEN [expected boundary behavior]
```

**Every requirement MUST have at least 3 scenarios** (normal, error, boundary). If a scenario type is truly not applicable, write "N/A — [specific reason]" instead of omitting it.

**Invariants**:
```
INV-<capability-id>-001: Before/after <operation>, <state> SHALL <condition>
INV-<capability-id>-002: On failure of <operation>, <state> SHALL NOT change
INV-<capability-id>-003: ...
```
Minimum 1 invariant per capability. If none, explain why.

**Dependencies**: List which other capabilities this one depends on (from the dependency graph in the capability map).

### 4. Write Test Migration Spec

Create `specs/test-migration/spec.md`. This is the binding contract between C tests and Rust tests.

**C Test Inventory**: List every entry from `test_functions` in the inventory.

**C→Rust Mapping Table**:
```
| C Test Function | C Source File | Rust Test Function | Rust Test File | Status |
|-----------------|---------------|-------------------|----------------|--------|
| test_flashdb_init | tests/test_init.c | test_init | tests/test_init.rs | mapped |
| test_legacy_api | tests/test_legacy.c | — | — | N/A: deprecated API |
```

Every C test function must appear in this table. Status is `mapped` or `N/A` with a reason.

**Additional Test Requirements**: Scenarios not covered by C tests but required for semantic equivalence:
```
REQ-TEST-001: Boundary condition — SHALL test <scenario> with <inputs>
  WHEN <condition> THEN <expected outcome>
```

### 5. Cross-Check Coverage

If capability map is available: verify every capability in `01c-capability-map.json` has a corresponding spec file. Every capability's `key_functions` are covered by at least one requirement in the spec. The dependency graph in the capability map is reflected in each spec's Dependencies section.

If capability map is NOT available: verify every capability from the proposal has a corresponding spec file, and every module in the design's module mapping is covered by at least one spec.

## Output

```
openspec/changes/OPENSPEC_CHANGE/specs/<capability-id>/spec.md   (per capability)
openspec/changes/OPENSPEC_CHANGE/specs/test-migration/spec.md
```

The test-migration spec is critical — Phase 6 uses it to verify complete C test coverage.

## Gate

- `PHASE_PASS` — one spec per capability, every spec has ≥3 scenarios per requirement, test-migration spec has complete mapping table
- `PHASE_BLOCKED` — design.md missing or inventory unreadable
- `PHASE_DEGRADED` — some capability specs missing requirements, or some C test functions lack Rust mapping
