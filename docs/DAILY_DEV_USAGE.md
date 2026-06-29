# Daily Dev Usage

For local development outside a contest environment:

1. keep this repository root under version control as the platform package
2. place the working repository under `code/`
3. configure `loopforge.config.yaml` from the repository root
4. run the runner directly for deterministic steps

Example:

```bash
python runtime/loopforge_runner.py --work-dir . --code-dir code --init --self-check --detect
python runtime/loopforge_runner.py --work-dir . --code-dir code --snapshot local-before-change
python runtime/loopforge_runner.py --work-dir . --code-dir code --verify --finalize
```

Windows entrypoints:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
powershell -ExecutionPolicy Bypass -File scripts/smoke-test.ps1
```

If `verification.commands` is still a placeholder, `--verify` should end in `BLOCKED_WITH_REPORT`. That is expected behavior for an unadapted package.

For a minimal platform acceptance check:

```bash
bash scripts/smoke-test.sh
```

Expected smoke-test outcomes:

- artifacts exist under `code/.loopforge/`
- `code/.loopforge/runtime/loopforge_runner.py` exists
- `code/.loopforge/state/loop-state.json` exists
- `code/.loopforge/state/config-check-summary.json` exists
- `code/.loopforge/state/work-package-summary.json` exists
- `code/.loopforge/reports/final-report.md` exists
- final report includes contract-validation content
- final report includes work-package contract content
- gate log includes a `FINALIZE` event
- no `./.loopforge/` directory is created

For negative-path acceptance checks:

```bash
python scripts/runner-negative-check.py
```

Expected negative-path outcomes:

- bad config or profile scenarios still produce `code/.loopforge/`
- verification state is `blocked-with-report`
- final report result is `BLOCKED_WITH_REPORT`
- contract validation contains explicit errors instead of guessed recovery
