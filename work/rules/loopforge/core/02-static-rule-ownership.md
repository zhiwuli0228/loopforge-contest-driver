# Static Rule Ownership

## Ownership

Files in the LoopForge root outside `SOURCE_ROOT` are human-maintained static assets. They define the execution contract and must remain stable during unattended runs.

This includes:

- `INSTRUCTION.md`
- `README.md`
- `SUBMISSION.md`
- `loopforge.config.yaml`
- `rules/**`
- `profiles/**`
- `runtime/loopforge_runner.py`
- `scripts/**`
- `docs/**`

## Agent Policy

The agent may read these files, summarize them, and apply their constraints, but must not:

- initialize new static rule files during execution
- rewrite or optimize existing rule text
- auto-fill placeholders in static config
- mutate the driver skill or runner source as part of task execution

## Failure Handling

If static assets are incomplete, invalid, or contradictory:

- report the issue explicitly
- stop before making unsupported assumptions
- preserve any already-created runtime evidence under `SOURCE_ROOT/.loopforge/`

Missing or invalid static configuration is an adaptation failure, not a reason for the agent to regenerate the platform contract.

