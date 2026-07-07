# Consistency-Check Task Contract

This document is the authoritative contract for the baseline consistency-check workflow.

## Purpose

The driver SHALL compare the documented design intent with the implementation found under `SOURCE_ROOT`, identify drift, and produce evidence that can be reviewed without mutating the source tree.

## Input Model

- `SOURCE_ROOT` is the only external runtime input.
- `SOURCE_ROOT` SHALL be treated as read-only.
- The implementation under `SOURCE_ROOT` MAY be a project root or a parent directory that contains the project root.
- The workflow MUST discover the relevant source layout from the filesystem and from the provided design contract.

## Required Baseline Behavior

- The default workflow SHALL operate in `consistency-check` mode.
- The default workflow SHALL be `analyze-only`.
- The workflow SHALL use `work/design/README.md` as the contract source of truth.
- The workflow SHALL preserve evidence under `logs/trace/`.
- The workflow SHALL not write to `SOURCE_ROOT`.

## Required Outputs

The baseline run SHALL produce at minimum:

- `result/output.md`
- `result/issues/00-summary.md`
- `logs/trace/final-report.md`
- `logs/trace/consistency/`

## Completion Criteria

The baseline change is complete when all of the following are true:

1. Entry documentation describes the repository as a consistency-check harness.
2. Default configuration resolves to `consistency-check` and `analyze-only`.
3. This document clearly states the input, output, and read-only expectations.
4. Follow-on changes can consume this contract without guessing the execution model.

## Non-Goals

- Do not define repair or code mutation behavior here.
- Do not encode language-specific implementation rules here.
- Do not require a README inside `SOURCE_ROOT`.

## Review Questions

If the workflow is unclear, answer these questions first:

1. What design intent is being checked?
2. What implementation surface is in scope?
3. What evidence is required to judge drift?
4. What outputs are expected at the end of the run?
