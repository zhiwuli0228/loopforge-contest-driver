# Cross-platform Design

LoopForge supports Windows local development and Linux official submission through a single Python runner plus platform-specific script entrypoints.

## Policy

- official submission is Linux-first
- Windows is a development and local smoke-test compatibility layer
- `work/runtime/loopforge_runner.py` remains the single cross-platform execution core
- static configuration continues to use `/` path separators
- all runtime artifacts remain under `code/.loopforge/`

## Entrypoints

- Linux official entry: `bash work/scripts/bootstrap.sh`
- Windows development entry: `powershell -ExecutionPolicy Bypass -File work/scripts/bootstrap.ps1`
- Linux smoke test: `bash work/scripts/smoke-test.sh`
- Windows smoke test: `powershell -ExecutionPolicy Bypass -File work/scripts/smoke-test.ps1`

## Verification Command Selection

`work/loopforge.config.yaml` may provide:

- `verification.commands.default`
- `verification.commands.linux`
- `verification.commands.windows`
- `verification.commands.macos`

Selection order:

1. current platform profile
2. `default`
3. `BLOCKED_WITH_REPORT`

Legacy list-style `verification.commands` is still supported and is treated as `default`.

## Reporting

Final reports should include:

- detected runtime OS
- configured official submission OS
- configured local development OS list
- selected verification command profile
- whether fallback to `default` was used
- cross-platform execution notes
