# loopforge-contest-driver source/readme input simplification design

## Goal

Reduce operator input for local and contest execution.

The package should work when the source tree is simply placed under `code/`, while still allowing explicit source-path overrides and platform-provided paths.

## Problems

Before this change:

- `work/scripts/run.sh` hardcoded a Linux fallback path of `/__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB`.
- local zero-input execution depended on script-specific branching instead of runner behavior.
- docs over-emphasized manual source-path input even though `code/` is the intended local fallback.
- shell entrypoints and docs each carried their own source-path rules.

## Design

Move source-path resolution into `work/runtime/loopforge_runner.py`.

Resolution order:

1. `--source-root`, when explicitly provided
2. `SOURCE_ROOT`, when explicitly provided
3. contest Linux source mount, only if it exists
4. configured local fallback from `platform.code_dir`, normally `code`

## Changes

- runner now resolves the effective source root centrally
- `run.sh` no longer injects a hardcoded Linux source path
- `run.ps1` no longer requires a source-path parameter for the default case
- `INSTRUCTION.md`, `README.md`, and `work/HARNESS.md` now describe zero-input local execution
- `work/docs/ADAPTATION_GUIDE.md` now treats extra source-path input as override-only

## Non-goals

- no change to task mode semantics
- no change to verification command semantics
- no change to `work/loopforge.config.yaml` profile selection rules
- no change to artifact output locations

## Acceptance

- local execution can rely on `code/` without setting `SOURCE_ROOT`
- explicit `--source-root` still overrides the default
- explicit `SOURCE_ROOT` still overrides the default
- Linux auto-detect is used only when the platform mount actually exists
- docs and scripts describe the same resolution order
