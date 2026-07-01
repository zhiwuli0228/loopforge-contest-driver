# Adaptation Guide

## Goal

Adapt the framework to a source tree by supplying `SOURCE_ROOT`.

The framework reads task context only from the preloaded `work/design/README.md`; `SOURCE_ROOT` supplies read-only implementation evidence.

## Adaptation Rules

- Keep profiles declarative.
- Keep rules generic.
- Do not hard-code a repository, language, or business domain into the core framework.
- Do not require humans to fill verification commands before a run can start.
- Keep evaluator-facing outputs under `work/result/` and `work/logs/`.

## Mode Selection Guidance

- `feature-development` for requirement-driven implementation work
- `migration` for compatibility-preserving change across stacks or structures
- `defect-repair` for bug fixing and regression repair
- `consistency-check` for design-versus-implementation analysis
- `skill-generation` for reusable workflow packaging
