# Source Root Contract

- `SOURCE_ROOT` is the only external source-tree input.
- Platform-provided source paths take priority when available.
- Explicit `--source-root` or `SOURCE_ROOT` overrides local fallback behavior.
- Linux may use the contest platform source mount when present.
- Windows defaults to `work/code/`; non-Windows execution uses explicit `SOURCE_ROOT` or the contest platform mount.
- The resolved source tree is the only mutable business-code area during execution.
