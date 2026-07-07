# Work Asset Guide

`work/` contains the static runtime assets used by the LoopForge consistency-check driver.

## Purpose

- `work/runtime/` holds the Python data layer and runner entry points.
- `work/scripts/` holds Linux and Windows bootstrap scripts.
- `work/skills/` holds agent-facing execution guidance.
- `work/profiles/`, `work/rules/`, and `work/subagent/` hold workflow contracts and guardrails.

## Input Model

The driver accepts one external runtime input:

- `SOURCE_ROOT`

The authoritative requirements and acceptance criteria come from `work/design/README.md`. `SOURCE_ROOT` is read-only and does not need a README. `work/code/` is only a local fixture and is not part of the formal submission surface.

`work/loopforge.config.yaml` provides framework defaults. It should describe the baseline mode, profile, and execution posture, not ad hoc per-task objectives.

## Output Model

Primary run outputs are written to:

- `result/output.md`
- `result/issues/00-summary.md`
- `logs/trace/`

Consistency-check evidence should stay under `logs/trace/consistency/` unless a later stage defines a more specific subdirectory.
