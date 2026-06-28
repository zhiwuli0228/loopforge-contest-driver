# Spec Normalization Rule

## Objective

Convert the raw task statement into a lightweight structured spec that can drive unattended execution.

## Output File

`.loopforge/spec/normalized-spec.md`

## Required Template

```markdown
# Normalized Spec

## Mode

spec-implementation

## Requirements

- REQ-001:

## Acceptance Criteria

- AC-001:

## Constraints

- C-001:

## Unknowns

- U-001:

## Confidence

HIGH / MEDIUM / LOW
```

## Fallback Rule

If the task cannot be fully normalized, use the raw task as the input source, emit the smallest useful requirement set, and mark confidence as `LOW`.
