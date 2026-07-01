# Generic C source-analysis runtime

The source-analysis gate inventories the resolved, read-only C project before Rust generation. It has no bundled project identity, repository revision, symbol prefix, directory exclusion, expected metric, or preprocessor macro policy.

## Input-derived policy

- Source and test roots come from `layout_resolution` for the current input.
- `compile_commands.json` is consumed when present. Otherwise deterministic C99 arguments and discovered include paths are recorded.
- Optional preprocessing variants may be supplied through `metadata.source_analysis.preprocessor_variants`; none are injected by default.
- Python uses `pycparser==2.22`. Structural recovery handles unsupported extensions, while incomplete recovery remains fail-closed.

## Evidence and blocking

Each run atomically writes `source-inventory.json`, `independent-source-scan.json`, `public-api-map.json`, `type-map.json`, `call-graph.json`, `global-state-map.json`, `preprocessor-variants.json`, and `analysis-verification.json` using schema `c-source-analysis/v2`.

All documents share a run ID, source digest, and the digest of the input-derived policy. Zero source/API/test counts, incomplete types, unresolved APIs, scanner differences, parse failures, input mutation, mixed runs, or dangling evidence produce `BLOCKED_WITH_REPORT`.
