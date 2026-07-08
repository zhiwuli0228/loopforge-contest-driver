# Work Asset Guide

`work/` contains the static runtime assets used by the LoopForge consistency-check repair-and-verify driver.

## Purpose

- `work/runtime/` holds the Python data layer and runner entry points.
- `work/scripts/` holds Linux and Windows bootstrap scripts.
- `work/skills/` holds agent-facing execution guidance.
- `work/profiles/`, `work/rules/`, and `work/subagent/` hold workflow contracts and guardrails.

## Input Model

The driver accepts one external runtime input:

- `SUBMISSION_ROOT`

The authoritative requirements and acceptance criteria come from the standard submission package:

- `SUBMISSION_ROOT/README.md`
- `SUBMISSION_ROOT/design-docs/`
- `SUBMISSION_ROOT/code/`
- `SUBMISSION_ROOT/test-cases/` when present or required

`work/design/README.md` remains the repository's internal contract description for this harness, but it is not the authoritative design source for a real submission package. `work/code/` is only a local fixture and is not part of the formal submission surface.

`work/loopforge.config.yaml` provides framework defaults. It should describe the baseline mode, profile, execution posture, mutable support-asset policy, and verification ordering contract, not ad hoc per-task objectives.

## Output Model

Primary run outputs are written to:

- `result/output.md`
- `result/issues/00-summary.md`
- `logs/trace/`

Consistency-check evidence should stay under `logs/trace/consistency/` unless a later stage defines a more specific subdirectory. In the current baseline, that evidence is expected to cover acceptance-baseline extraction, repair execution, build verification, black-box verification, retry evidence, and final verdict assembly.
