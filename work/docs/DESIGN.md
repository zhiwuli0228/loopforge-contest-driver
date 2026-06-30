# Design

LoopForge is a generic contest execution framework.

## Core Model

The framework operates on:

```text
SOURCE_ROOT + source README
```

`SOURCE_ROOT` resolves to the source tree under evaluation.
The source README provides requirements, constraints, and acceptance context.

## Stable Components

- `work/runtime/loopforge_runner.py` initializes artifacts and writes evaluator-facing outputs.
- `work/scripts/` provides Linux and Windows entrypoints.
- `work/rules/loopforge/common/` defines source, result, and logging contracts.
- `work/rules/loopforge/core/` defines execution boundaries.
- `work/rules/loopforge/modes/` defines generic workflow shapes.
- `work/profiles/` provides declarative defaults and examples.

## Output Contract

- Evaluator-facing outputs are written to `result/` and `logs/`.
- Internal runtime evidence is written under `logs/trace/`.
- The framework never requires humans to edit task metadata before a run.
