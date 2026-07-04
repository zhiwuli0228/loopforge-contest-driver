# Verification Evidence

## Passed

- Python compilation: all Python files under `work/runtime` and `work/scripts` compiled successfully.
- Unit suite: `30` tests passed via `python -m unittest discover -s work/runtime/tests -p test_*.py`.
- Windows smoke: `work/scripts/smoke-test.ps1` passed with README-free source fixtures.
- Submission contract: `work/scripts/validate_design_input_contract.py` passed after building a temporary package without `work/code/`, injecting a README-free source tree, verifying the design SHA-256, and confirming the source tree was unchanged.
- OpenSpec: `openspec validate preload-design-readme --strict` passed.
- Patch hygiene: `git diff --check` passed; only pre-existing/generated line-ending warnings were reported.
- Production dependency scan: no forbidden `work/code/README`, `SOURCE_ROOT/README`, or `source-readme` references remain in runtime, configuration, rules, skills, profiles, or subagent contracts.

## Environment-Limited Check

- Linux smoke was invoked with `bash work/scripts/smoke-test.sh`, but this Windows host's `bash` resolves to an unusable WSL installation and failed before script execution with `getpwuid(0)` and `/bin/bash` startup errors. The Linux script was updated in parallel with the passing PowerShell smoke script; execution must be repeated on the official Linux environment.
