# Source Root Contract

- `SOURCE_ROOT` is the only external source-tree input.
- Platform-provided source paths take priority when available.
- Explicit `--source-root` or `SOURCE_ROOT` overrides local fallback behavior.
- Linux may use the contest platform source mount when present.
- Windows and local fallback may use `.code/`.
- The resolved source tree is the only mutable business-code area during execution.
