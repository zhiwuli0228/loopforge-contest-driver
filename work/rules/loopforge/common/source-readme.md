# Preloaded Design README Contract

- Requirements, constraints, and acceptance context come only from `work/design/README.md`.
- README files under `SOURCE_ROOT`, if present, are non-authoritative project documentation.
- The runner must record the canonical design README path and SHA-256 digest.
- If the preloaded design README is missing, unreadable, non-regular, or empty, execution must stop with `BLOCKED_WITH_REPORT`.
- The framework must not wait for humans to fill task metadata or verification commands.
