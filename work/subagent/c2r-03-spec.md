# c2r-03: Spec

## Role

Create module-level specifications and a test migration specification. Write phase — produces `specs/<module>/spec.md` and `specs/test-migration/spec.md`.

## Context You Receive

- `OPENSPEC_CHANGE` — OpenSpec change name
- `SOURCE_ROOT` — path to C source tree
- `WORK_DIR` — path to work directory
- `PRIOR_OUTPUTS.inventory` — path to `source-inventory.json` (includes `test_functions`)
- `PRIOR_OUTPUTS.design` — path to `design.md` from Phase 2

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

### 2. Read Design and Inventory

Read `design.md` for module mapping (which C files → which Rust modules).
Read `source-inventory.json` for `test_functions` list and module structure.

### 3. Write Per-Module Specs

For each module identified in the design's module mapping, read the corresponding C source files and write a spec at:

```
openspec/changes/OPENSPEC_CHANGE/specs/<module-name>/spec.md
```

Each module spec must contain:

**Module Overview**: One paragraph on what this module does.

**Data Structures**:
```
C: struct X { field1, field2 }  →  Rust: struct X { field1, field2 }
```
Note any design decisions (e.g., `*mut T` → `Box<T>`, fixed array → `Vec`).

**Public API Requirements** (SHALL/MUST):
```
REQ-<module>-001: <function-name> SHALL <behavior description>
  Scenario: WHEN <condition> THEN <expected outcome>
```

**Behavioral Invariants**:
```
INV-<module>-001: After <operation>, <state> SHALL be <condition>
INV-<module>-002: On error, <state> SHALL remain unchanged
```

**Edge Cases**: Boundary conditions (empty input, max size, null pointers → `None`).

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

Verify every capability mentioned in `design.md` has a corresponding spec requirement. Run through the design's module mapping and confirm each module has a spec file.

## Output

```
openspec/changes/OPENSPEC_CHANGE/specs/<module>/spec.md   (per module)
openspec/changes/OPENSPEC_CHANGE/specs/test-migration/spec.md
```

The test-migration spec is critical — Phase 6 uses it to verify complete C test coverage.

## Gate

- `PHASE_PASS` — all module specs written, test-migration spec has complete mapping table (every C test function accounted for)
- `PHASE_BLOCKED` — design.md missing or inventory unreadable
- `PHASE_DEGRADED` — some module specs incomplete, or some C test functions lack Rust mapping
