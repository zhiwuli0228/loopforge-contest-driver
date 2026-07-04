## Why

The contest runtime may provide a read-only `SOURCE_ROOT` without any README, while the current harness treats a source README or the local-only `work/code/README.md` as required task context. The submission must therefore carry its authoritative requirements in a stable, preloaded document that remains available when `work/code/` is absent and does not require modifying `SOURCE_ROOT`.

## What Changes

- Add `work/design/README.md` as a version-controlled, submission-time asset and the sole authoritative source for requirements, constraints, and acceptance criteria.
- **BREAKING**: Remove the runtime requirement that `SOURCE_ROOT` contain a README and remove all formal fallback behavior involving `work/code/README.md`.
- Discover the source project from source files, build metadata, tests, and directory structure without requiring README evidence.
- Keep `SOURCE_ROOT` read-only and direct all generated artifacts to existing writable work, log, result, and output locations.
- Validate the preloaded design README during startup and record its identity in execution evidence.
- Add packaging and runtime checks proving that execution does not depend on `work/code/` or `SOURCE_ROOT/README*`.

## Capabilities

### New Capabilities

- `preloaded-design-input`: Defines the preloaded design README, source-root independence, read-only source handling, validation, evidence, and submission-package guarantees.

### Modified Capabilities

None.

## Impact

- Affects runner startup, source-project resolution, task-packet construction, analysis gates, configuration, rules, skills, subagent contracts, documentation, smoke tests, and packaging validation.
- Removes formal runtime coupling to `work/code/README.md` and any README located below `SOURCE_ROOT`.
- Changes the input model from source-README-driven execution to preloaded-design-plus-source execution.
