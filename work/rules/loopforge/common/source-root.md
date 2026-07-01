# Source Root Contract

- `SOURCE_ROOT` is the only external source-tree input.
- Platform-provided source paths take priority when available.
- Explicit `--source-root` or `SOURCE_ROOT` overrides local fallback behavior.
- Linux may use the contest platform source mount when present.
- Windows and non-Windows execution use explicit `SOURCE_ROOT` or the contest platform mount; production execution has no `work/code/` fallback.
- The resolved source tree is read-only during execution.
