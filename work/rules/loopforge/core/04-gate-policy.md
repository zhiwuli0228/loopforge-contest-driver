# Gate Policy

## Policy Objective

LoopForge uses fail-soft reporting with explicit gate events. The platform should prefer leaving behind evidence and a final report instead of exiting without trace.

## Hard Gates

Execution should hard-block when any of the following is true:

- `work/` or `code/` is missing
- the configured layout is not `work-code`
- the artifact path escapes `code/`
- static configuration is unusable
- the requested action would mutate `work/`

## Soft Gates

Execution may continue in degraded form when:

- the target project type cannot be detected
- git snapshots cannot be collected
- verification commands fail but reporting can still complete
- optional mode-specific artifacts are incomplete

## Logging Contract

Each meaningful phase should log a gate event in `code/.loopforge/gates/gate-events.md`.

At minimum, log:

- bootstrap
- self-check
- detect
- snapshot
- verify
- finalize

Each event should record:

- phase name
- pass, warn, fail, or degrade status
- action taken
- reason or constraint summary
