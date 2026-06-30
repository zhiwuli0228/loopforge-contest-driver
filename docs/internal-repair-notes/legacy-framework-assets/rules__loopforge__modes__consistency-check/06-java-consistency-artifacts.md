# Java Consistency Artifacts

For Java Maven consistency-check runs, capture at least the following in mode artifacts:

- the frozen design sources that were read
- the target module list and any excluded modules
- the Java classes or packages mapped to each design statement
- drift items grouped by missing behavior, behavior mismatch, schema drift, and design ambiguity
- the planned repair scope, including any required common-module touch points
- verification command evidence, or a degraded explanation when verification is blocked

When the current runner only indexes `code/.loopforge/plan/`, keep the detailed files there and reference them from `mode-artifacts.md` and `final-report.md`.
