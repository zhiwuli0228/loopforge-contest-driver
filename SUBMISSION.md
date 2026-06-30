# Submission Notes

This package is submitted as a contest execution driver.

## Execution Entry

- `INSTRUCTION.md`

## Runnable Assets

- `work/`

## Primary Results

- `result/output.md`
- `result/issues/00-summary.md`
- `logs/interaction.md`
- `logs/trace/`

## Internal Evidence

- `SOURCE_ROOT/.loopforge/` may contain internal runtime evidence, including `reports/final-report.md`
- internal evidence is not the primary judge-facing output

## Model

- `SOURCE_ROOT` is the only external source-path input
- task intent, constraints, and acceptance hints are read from `SOURCE_ROOT/README*`
- the package does not require manual editing of `work/loopforge.config.yaml`

## Non-Goals

LoopForge does not:

- commit code
- push changes
- open pull requests
- upload results to a contest platform
