#!/usr/bin/env python3
"""Negative-path acceptance checks for the LoopForge runner."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Dict, List


ScenarioMutator = Callable[[Path], None]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise AssertionError(f"expected text not found in {path}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def make_workspace(repo_root: Path) -> Path:
    temp_root = Path(tempfile.mkdtemp(prefix="loopforge-negative-"))
    shutil.copytree(repo_root / "work", temp_root / "work")
    shutil.copytree(repo_root / "code", temp_root / "code")
    return temp_root


def run_runner(workspace: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "work/runtime/loopforge_runner.py",
            "--work-dir",
            "work",
            "--code-dir",
            "code",
            "--init",
            "--self-check",
            "--verify",
            "--finalize",
        ],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        check=False,
    )


def read_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def scenario_missing_profile(workspace: Path) -> None:
    config_path = workspace / "work" / "loopforge.config.yaml"
    replace_once(
        config_path,
        '  profile: "profiles/templates/feature-development.yaml"',
        '  profile: "profiles/templates/does-not-exist.yaml"',
    )


def scenario_verification_outside_code(workspace: Path) -> None:
    config_path = workspace / "work" / "loopforge.config.yaml"
    replace_once(config_path, '  working_directory: "code"', '  working_directory: "work"')


def scenario_profile_mode_mismatch(workspace: Path) -> None:
    profile_path = workspace / "work" / "profiles" / "templates" / "feature-development.yaml"
    replace_once(profile_path, '  mode: "feature-development"', '  mode: "migration"')


def scenario_output_outside_code(workspace: Path) -> None:
    config_path = workspace / "work" / "loopforge.config.yaml"
    replace_once(
        config_path,
        '  final_report: "code/.loopforge/reports/final-report.md"',
        '  final_report: "work/reports/final-report.md"',
    )


def scenario_missing_mode_rule(workspace: Path) -> None:
    target = workspace / "work" / "rules" / "loopforge" / "modes" / "feature-development" / "04-final-report.md"
    target.unlink()


def scenario_missing_all_verification_commands(workspace: Path) -> None:
    config_path = workspace / "work" / "loopforge.config.yaml"
    replace_once(
        config_path,
        '  commands:\n    default:\n      - "fill-by-human-before-execution"\n    linux:\n      - "fill-by-human-before-linux-submission"\n    windows:\n      - "fill-by-human-before-windows-local-test"',
        '  commands: {}',
    )


SCENARIOS: List[Dict[str, object]] = [
    {
        "name": "missing-profile",
        "mutator": scenario_missing_profile,
        "expected_errors": ["profile: profile file not found"],
    },
    {
        "name": "verification-outside-code",
        "mutator": scenario_verification_outside_code,
        "expected_errors": ["verification.working_directory must resolve to code/ or a descendant of code/"],
    },
    {
        "name": "profile-mode-mismatch",
        "mutator": scenario_profile_mode_mismatch,
        "expected_errors": ["profile: task.mode (feature-development) does not match profile task.mode (migration)"],
    },
    {
        "name": "output-outside-code",
        "mutator": scenario_output_outside_code,
        "expected_errors": ["outputs.final_report must resolve under code/"],
    },
    {
        "name": "missing-mode-rule",
        "mutator": scenario_missing_mode_rule,
        "expected_errors": ["work-package: missing required mode rule: rules/loopforge/modes/feature-development/04-final-report.md"],
    },
    {
        "name": "missing-all-verification-commands",
        "mutator": scenario_missing_all_verification_commands,
        "expected_errors": ["verification.commands does not define any runnable command for the current platform"],
    },
]


def validate_scenario(repo_root: Path, scenario: Dict[str, object]) -> None:
    workspace = make_workspace(repo_root)
    try:
        mutator = scenario["mutator"]
        assert callable(mutator)
        mutator(workspace)

        result = run_runner(workspace)
        if result.returncode != 0:
            raise AssertionError(
                f"{scenario['name']}: runner exited non-zero\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )

        artifact_root = workspace / "code" / ".loopforge"
        config_summary = read_json(artifact_root / "state" / "config-check-summary.json")
        report_text = (artifact_root / "reports" / "final-report.md").read_text(encoding="utf-8")
        verify_summary = read_json(artifact_root / "state" / "verification-summary.json")
        mode_artifact_text = (artifact_root / "plan" / "mode-artifacts.md").read_text(encoding="utf-8")

        if config_summary.get("ok") is not False:
            raise AssertionError(f"{scenario['name']}: expected config-check-summary ok=false")
        if verify_summary.get("status") != "blocked-with-report":
            raise AssertionError(f"{scenario['name']}: expected blocked-with-report verification status")
        if "BLOCKED_WITH_REPORT" not in report_text:
            raise AssertionError(f"{scenario['name']}: expected BLOCKED_WITH_REPORT in final report")
        if "## Contract Verdict" not in report_text or "FAIL" not in report_text:
            raise AssertionError(f"{scenario['name']}: expected contract verdict FAIL in final report")
        if "## Mode Artifact Summary" not in report_text:
            raise AssertionError(f"{scenario['name']}: expected mode artifact summary section in final report")
        if "# Mode Artifacts" not in mode_artifact_text:
            raise AssertionError(f"{scenario['name']}: expected initialized mode artifact index")

        errors = [str(item) for item in config_summary.get("errors", [])]
        for expected in scenario["expected_errors"]:
            if not any(expected in error for error in errors):
                raise AssertionError(
                    f"{scenario['name']}: expected error containing {expected!r}, actual errors: {errors}"
                )
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    failures: List[str] = []
    for scenario in SCENARIOS:
        try:
            validate_scenario(repo_root, scenario)
            print(f"[PASS] {scenario['name']}")
        except Exception as exc:
            failures.append(f"{scenario['name']}: {exc}")
            print(f"[FAIL] {scenario['name']}: {exc}", file=sys.stderr)

    if failures:
        print("\nNegative-path acceptance failed:", file=sys.stderr)
        for item in failures:
            print(f"- {item}", file=sys.stderr)
        return 1

    print("\nNegative-path acceptance passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
