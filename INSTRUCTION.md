# LoopForge Official Consistency-Check Entry

This file is the Linux backup of the official root `INSTRUCTION.md`.

## Prerequisites

Required in `PATH`: `bash`, `python3`, `cargo`, `rustc`, and `node` for OpenSpec.

## Toolchain Setup

The workflow uses [OpenSpec](https://www.npmjs.com/package/@fission-ai/openspec) for schema-driven artifact management. If `openspec` is not globally installed, the bundled wrapper handles it automatically.

### Quick check

```bash
bash work/scripts/openspec.sh --version
```

### SuperPower Guards

Before running any staged work, the agent MUST read the permission boundaries:

```text
work/profiles/superpower/design-implementation-consistency-guards.yaml
```

This file defines allowed tools, filesystem access patterns, and forbidden actions. Default-deny applies to anything not explicitly allowed.

### Project Profiles

The default profile for this baseline is:

```text
work/profiles/examples/default-java-consistency.yaml
```

The staged execution definition is:

```text
work/profiles/superspec/design-implementation-consistency-stages.yaml
```

## Default Execution Contract

The repository is configured for an analyze-only consistency-check baseline.

- `work/design/README.md` is the authoritative task contract.
- `SOURCE_ROOT` is read-only and is the only external input.
- No default workflow step should imply business code mutation.
- File handoff and stage evidence are required between phases.

## Staged Execution

Default evidence should accumulate under `logs/trace/consistency/`.

Typical stages:

1. Preflight
2. Design Read
3. Source Inventory
4. Design Model
5. Implementation Model
6. Traceability Mapping
7. Drift Analysis
8. Risk Classification
9. Repair Planning
10. Final Report

Repair-oriented stages remain available only when a later profile explicitly enables them.

## tools.py

All data retrieval goes through `python work/runtime/tools.py`. It returns raw JSON and does not make pass/fail judgments.

```bash
python work/runtime/tools.py scan-design --design-root work/design --output logs/trace/consistency/01-design-inventory.json
python work/runtime/tools.py scan-code --source-root /path --output logs/trace/consistency/02-source-inventory.json --selection-output logs/trace/consistency/02-adapter-selection.json
python work/runtime/tools.py extract-implementation --source-root /path --output logs/trace/consistency/04-implementation-model.json
python work/runtime/tools.py build-traceability --design-model logs/trace/consistency/03-design-model.json --implementation-model logs/trace/consistency/04-implementation-model.json --output logs/trace/consistency/05-traceability-matrix.json
python work/runtime/tools.py run-verification --project-dir /path --commands '["mvn test"]' --output logs/trace/consistency/09-verification-results.json
python work/runtime/tools.py check-unsafe --project-dir /path
python work/runtime/tools.py fault-injection --project-dir /path --trace-dir logs/trace
python work/runtime/tools.py neutrality-audit --paths '["src/**/*.rs"]' --forbidden-terms '["term1","term2"]'
python work/runtime/tools.py write-report --result-dir result --trace-root logs/trace/consistency --trace-dir logs/trace --payload-output logs/trace/consistency/09-final-report-input.json
```

Legacy C2Rust support still exposes `parse-source`, but it is not part of the authoritative consistency-check command surface.

## Reports

Expected outputs:

```text
result/output.md
result/issues/00-summary.md
logs/trace/final-report.md
logs/trace/consistency/
```
