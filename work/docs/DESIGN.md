# Design

LoopForge uses a stable core plus configurable modes and profiles.

## Architectural Intent

- keep driver assets stable under `work/`
- keep target code isolated under `code/`
- keep runtime artifacts under `code/.loopforge/`
- keep task-specific details in profiles rather than in runner logic

## Core Components

- `skills/loopforge-driver/SKILL.md`: agent entrypoint
- `runtime/loopforge_runner.py`: deterministic execution helper
- `rules/loopforge/core/`: invariant platform rules
- `rules/loopforge/modes/`: reusable flow definitions
- `rules/loopforge/adapters/`: language and platform guidance
- `profiles/`: configuration templates and examples
