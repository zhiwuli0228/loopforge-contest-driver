# Running LoopForge

## Required Copy

Copy the following into the target repository context:

- `skills/loopforge-driver/`
- `rules/loopforge/`

Optional:

- `optional-opencode/tools/loopforge.ts`

## Start

1. Start OpenCode in the target project root.
2. Ask OpenCode to use the `loopforge-driver` skill for the contest task.
3. Provide the task statement, spec, or bug-fix goal in natural language.

## Expected Runtime Artifacts

LoopForge creates:

- `.loopforge/`
- `.loopforge/runtime/loopforge_runner.py`
- `.loopforge/state/loop-state.json`
- `.loopforge/state/verification-summary.json`
- `.loopforge/gates/gate-events.md`
- `.loopforge/reports/final-report.md`

## No Hook Required

LoopForge does not require hooks. The primary path is `Skill + Rule + generated Runner`.

## Runner Bootstrap

The agent must extract the Python code block from `rules/loopforge/20-runner-source-python.md` and write it to:

```text
.loopforge/runtime/loopforge_runner.py
```

Then run:

```bash
python .loopforge/runtime/loopforge_runner.py --init
python .loopforge/runtime/loopforge_runner.py --self-check
python .loopforge/runtime/loopforge_runner.py --detect
python .loopforge/runtime/loopforge_runner.py --prepare path/to/task.txt
python .loopforge/runtime/loopforge_runner.py --start-apply
python .loopforge/runtime/loopforge_runner.py --complete-apply
python .loopforge/runtime/loopforge_runner.py --integrate-review
python .loopforge/runtime/loopforge_runner.py --verify
python .loopforge/runtime/loopforge_runner.py --repair
python .loopforge/runtime/loopforge_runner.py --finalize
```

## Optional Tool Mode

If project-local OpenCode tools are supported, `optional-opencode/tools/loopforge.ts` may be copied to:

```text
.opencode/tools/loopforge.ts
```

This wrapper is optional and must not be treated as the primary execution path.

## Current Scope

This milestone supports:

- directory bootstrap
- self-check
- basic project detection
- git diff snapshots
- deterministic task/spec/brainstorm/plan/lease generation
- subagent report template generation
- subagent report change backfill
- lease-based integrate review summary
- Java Maven verification
- repair round state updates and repair snapshots
- final report generation

Repair orchestration and executable non-Java verification are still deferred.

## Local Validation

Recommended local checks for this repository:

```bash
python --version
python -c "import pathlib; print(pathlib.Path('rules/loopforge/20-runner-source-python.md').exists())"
```
