# Patch Summary Template

The patch stage must write:

`work/logs/trace/consistency/05-patch-summary.md`

Use this structure:

```markdown
# Patch Summary

## Gate

Gate: READY_FOR_VERIFICATION

## Applied Skill

- Skill: skills/code-implementation/SKILL.md

## Modified Files

| File | Purpose | Repair Plan Item |
|---|---|---|
| path/to/file | ... | RP-001 |

## Implemented Repair Items

| Repair Item | Status | Evidence |
|---|---|---|
| RP-001 | DONE | ... |

## Files Intentionally Not Modified

| File | Reason |
|---|---|
| ... | ... |

## Security-Sensitive Areas

| Area | Touched | Notes |
|---|---:|---|
| Input validation | yes/no | ... |
| Error handling | yes/no | ... |
| Logging | yes/no | ... |
| Data access | yes/no | ... |
| Authentication / authorization | yes/no | ... |

## Deviations From Repair Plan

- None

## Verification Readiness

- Ready for verification: true
- Verification command source: loopforge.config.yaml
```
