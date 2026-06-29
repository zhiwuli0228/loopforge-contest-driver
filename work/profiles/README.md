# Profiles

Profiles provide task-specific configuration without changing the LoopForge core.

## Purpose

- `templates/` contains starting points for each mode.
- `examples/` contains representative sample profiles for reusable task classes.

Profiles are configuration only. They must not carry runner logic, static rule logic, or repository-specific implementation scripts.

## Suggested Schema

Profiles should stay declarative and should normally contain:

- `profile`
  - profile identity and intent
- `task`
  - mode, objective, and language context
- `inputs`
  - expected external materials such as specs, bug reports, or source references
- `execution`
  - mode-level switches that shape the run without changing platform policy
- `verification`
  - project-facing verification expectations and placeholders
- `reporting`
  - report focus, drift categories, or migration-risk emphasis

## Adaptation Rules

- keep profiles generic and reusable
- do not encode repository-local shell scripts into templates
- do not move core policy from `work/rules/` into profiles
- use examples to illustrate classes of work, not a single hard-coded contest problem
