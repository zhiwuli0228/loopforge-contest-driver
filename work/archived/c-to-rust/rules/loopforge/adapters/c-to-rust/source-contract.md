# C-To-Rust Source Contract

- `SOURCE_ROOT` is read-only.
- Requirements must be read only from `work/design/README.md`.
- Resolve source and test directories from filesystem, build, translation-unit, and test evidence plus runtime defaults.
- Local development fallback must remain generic and must not depend on a project-specific directory name.
- Production execution must not depend on `work/code/`.
- Do not write reports, snapshots, runtime state, or generated files under `SOURCE_ROOT`.
