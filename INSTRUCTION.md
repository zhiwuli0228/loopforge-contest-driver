# Contest Execution Instruction

This repository is a contest driver for design-implementation consistency repair and verification. The authoritative external input is a standard submission package exposed as `SUBMISSION_ROOT`.

## Environment

Supported execution environments:

- Linux with `bash`
- Windows with PowerShell

Required tools:

- Python 3
- `bash`
- `node` for OpenSpec
- Rust toolchain with `cargo` and `rustc`

Quick toolchain check:

```bash
bash work/scripts/openspec.sh --version
python work/scripts/validate_consistency_contracts.py
```

## Submission Root Protocol

Submission path resolution priority:

1. Contest platform explicit submission path
2. `--submission-root <path>`
3. `--source-root <path>` for compatibility
4. `SUBMISSION_ROOT`
5. `SOURCE_ROOT` for compatibility
6. Linux fallback: `/__CONTEST_PLATFORM_SOURCE_ROOT__/source`
7. Linux fallback: `/__CONTEST_PLATFORM_SOURCE_ROOT__`

The standard submission package layout is:

```text
SUBMISSION_ROOT/
├── README.md
├── design-docs/
├── code/
├── test-cases/
└── contest.meta.yaml   # optional
```

Authoritative input rules:

- `SUBMISSION_ROOT/README.md` is the package-level rules, frozen API baseline, error-code baseline, verification-command source, and modification entry contract.
- `SUBMISSION_ROOT/design-docs/` is the business design source of truth.
- `SUBMISSION_ROOT/code/` is the business implementation area and the default mutable repair scope.
- `SUBMISSION_ROOT/test-cases/` is the black-box validation area unless package metadata waives it.
- In the default `repair-and-verify` baseline, no path under `SUBMISSION_ROOT` may be modified except `code/` and explicitly declared support assets such as `maven-settings.xml`.

If required package assets are missing, preflight records the failure in `logs/trace/consistency/00-preflight-self-check.json` and the run ends in an invalid or blocked report.

## Validation

Repository contract validation:

```bash
python work/scripts/validate_consistency_contracts.py
```

Submission package preflight validation only:

```bash
SUBMISSION_ROOT="E:\001code\java\java-contest" bash work/scripts/run.sh --self-check
```

This preflight checks at least:

- required workflow assets exist in the repository
- `SUBMISSION_ROOT/README.md` exists
- `SUBMISSION_ROOT/design-docs/` exists
- `SUBMISSION_ROOT/code/` exists
- `SUBMISSION_ROOT/test-cases/` exists unless metadata waives it
- result and log outputs are outside `SUBMISSION_ROOT`
- mutable support assets stay within the declared allowlist

## Run the Tool

Authoritative contest startup command:

```bash
SUBMISSION_ROOT="/path/to/submission" bash work/scripts/run.sh --self-check --run
```

Minimal run command:

```bash
SUBMISSION_ROOT="/path/to/submission" bash work/scripts/run.sh --run
```

Windows PowerShell:

```powershell
$env:SUBMISSION_ROOT="C:\path\to\submission"
python work\runtime\loopforge_runner.py --work-dir work --submission-root $env:SUBMISSION_ROOT --result-dir result --log-dir logs --self-check --run
```

The default run uses the repair-and-verify consistency baseline, the default Java profile with Generic fallback, and stage evidence under `logs/trace/consistency/`.

## Runtime Command Surface

The authoritative runtime commands are:

```bash
python work/runtime/tools.py scan-design --design-root "$SUBMISSION_ROOT/design-docs" --submission-readme "$SUBMISSION_ROOT/README.md" --output logs/trace/consistency/01-acceptance-baseline.json
python work/runtime/tools.py scan-code --source-root "$SUBMISSION_ROOT/code" --output logs/trace/consistency/02-source-inventory.json --selection-output logs/trace/consistency/02-adapter-selection.json
python work/runtime/tools.py run-verification --project-dir "$SUBMISSION_ROOT" --submission-root "$SUBMISSION_ROOT" --profile work/profiles/examples/default-java-consistency.yaml --output logs/trace/consistency/09-verification-results.json
python work/runtime/tools.py write-report --result-dir result --trace-root logs/trace/consistency --trace-dir logs/trace --payload-output logs/trace/consistency/09-final-report-input.json
```

## Result Retrieval

Primary evaluator outputs:

- `result/output.md`
- `result/issues/00-summary.md`
- `logs/trace/final-report.md`
- `logs/trace/consistency/`

Useful preflight and run diagnostics:

- `logs/trace/run-summary.json`
- `logs/trace/consistency/00-preflight-self-check.json`
- `logs/trace/consistency/00-submission-layout.json`

## Failure Handling

- Check `result/issues/00-summary.md` for the top-level invalid, blocked, or partial reason.
- Check `logs/trace/consistency/00-preflight-self-check.json` for package layout or immutable-boundary failures.
- Check `logs/trace/run-summary.json` for selected adapter, verification status, and final output paths.
- Requirements must come from `SUBMISSION_ROOT/README.md` and `SUBMISSION_ROOT/design-docs/`, not from repository-local fallback assumptions.
