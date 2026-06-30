# Source README Contract

- Requirements, constraints, and acceptance context come from the README under `SOURCE_ROOT`.
- Supported names are `README.md`, `README`, `readme.md`, and `Readme.md`.
- The runner must record whether a source README was found and which path was selected.
- If no source README exists, execution must stop with `BLOCKED_WITH_REPORT`.
- The framework must not wait for humans to fill task metadata or verification commands.
