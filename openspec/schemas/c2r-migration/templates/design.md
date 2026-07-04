## Context

[Background: What the C codebase does, its size, why migration is needed. Include key metrics: N source files, M functions, K test functions, L lines of C code.]

## Goals / Non-Goals

**Goals:**
- [Goal 1: What the migration must achieve — e.g., complete semantic equivalence, safe Rust preference, < 10% unsafe]
- [Goal 2: ...]

**Non-Goals:**
- [Non-goal 1: What is explicitly out of scope — e.g., performance parity, C ABI compatibility, platform-specific features]
- [Non-goal 2: ...]

## Capability Mapping

[If a capability map (`01c-capability-map.json`) is available, fill this table. Every capability from the map MUST appear here. If no capability map is available, replace this section with **Module Mapping**: a list mapping each C source file to its Rust module path.]

| Capability ID | Name | Priority | C Source Files | Rust Target Module | Key Functions | Dependencies |
|--------------|------|----------|----------------|-------------------|---------------|--------------|
| [id] | [name] | [P0/P1/P2] | [files] | [rust_module] | [func1, func2, ...] | [dep-ids or "无"] |
| [id] | [name] | [P0/P1/P2] | [files] | [rust_module] | [func1, func2, ...] | [dep-ids] |

[Alternatively, if no capability map available — **Module Mapping**:]
[```
C: src/[file].c  →  Rust: src/[module].rs
```]

## Type Mapping

[For each key C type, state the Rust equivalent. Always required regardless of input source.]

| C Type | Rust Equivalent | Notes |
|--------|----------------|-------|
| `struct [name] { ... }` | `struct [Name] { ... }` | [ownership notes, repr(C) if needed] |
| `typedef enum [name] { ... }` | `enum [Name] { ... }` | [mapping notes] |

## Decisions

### 1. [Decision Name]

[Description of the decision and what problem it solves.]

**Rationale**: [Why this choice over alternatives. Reference capability priorities and dependencies from the capability map if available, or module structure from the source inventory.]

**Alternatives considered:**
- Alternative A: [Description] — Rejected because [specific reason]
- Alternative B: [Description] — Rejected because [specific reason]

[Minimum 1 rejected alternative per decision. If no alternatives were considered, write: "No alternatives considered — [justification for why this decision is the only viable option]"]

### 2. [Decision Name]

...

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| [Risk description] | [What happens if it materializes] | [How to prevent or handle it] |
| [Risk description] | [Impact] | [Mitigation] |

[Minimum 3 risks. If fewer than 3 risks are apparent, write: "Additional risks not identified — [explanation of why the migration is low-risk]"]

## Open Questions

1. [Question that needs resolution before or during implementation]
2. [Question]
