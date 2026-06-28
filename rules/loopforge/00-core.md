# LoopForge Core Rules

## Principles

- Single Main Loop
- Single Work Tree
- Controlled Coding Subagents
- Single Final Review
- Single Final Report
- Fail Soft, Block Late
- Evidence First

## Mandatory Behavior

- Keep one controlling workflow for the full task.
- Do not let subagents create independent delivery branches, PRs, or final judgments.
- Make all changes inside the current repository work tree.
- Prefer minimal diffs and minimal file count.
- Preserve existing user changes unless explicitly instructed otherwise.
- Always leave behind evidence artifacts when an action is attempted.

## Blocking Threshold

Use `BLOCK` only for destructive or unrecoverable conditions. Ordinary implementation or verification failures must stay in retry, repair, or degrade paths.
