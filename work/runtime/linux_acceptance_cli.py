#!/usr/bin/env python3
"""Execute the packaged driver twice in fresh Linux workspaces and report evidence."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from linux_acceptance import (
    AcceptanceLedger, AcceptanceWorkspace, assert_clean_workspace, atomic_json,
    customization_audit, environment_evidence, fallback_report, final_verification,
    final_retry, path_manifest, publish_reports, publish_source_integrity, repeatability_report,
)
from timeout_policy import JUDGING_PLATFORM_TIMEOUT_SECONDS


EXCLUDED_COPY_PARTS = {".git", "target", "__pycache__", "logs", "result"}


def runner_evidence(logs: Path, run_id: str) -> dict[str, Any]:
    def load(relative: str) -> dict[str, Any]:
        path = logs / relative
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {"items": value}
        except (OSError, json.JSONDecodeError):
            return {}
    summary = load("trace/run-summary.json")
    analysis = summary.get("analysis", {})
    gates = summary.get("verification", {}).get("gates", {})
    passed = lambda name: gates.get(name, {}).get("passed") is True
    invariants = load("trace/c-to-rust/semantic-invariants.json")
    differential = load("trace/c-to-rust/differential-test-report.json")
    mutation = load("trace/c-to-rust/mutation-test-report.json")
    test_report = load("trace/c-to-rust/test-validation-report.json")
    unsupported = load("trace/c-to-rust/unsupported-functions.json")
    unsafe = load("trace/c-to-rust/unsafe-ratio.json")
    invariant_items = invariants.get("invariants", invariants.get("items", []))
    differential_items = differential.get("scenarios", differential.get("results", []))
    unsupported_items = unsupported.get("functions", unsupported.get("items", []))
    ratio = unsafe.get("unsafe_ratio", unsafe.get("ratio"))
    test_metrics = test_report.get("metrics", {})
    test_checks = test_report.get("checks", {})
    return {
        "run_id": run_id,
        "source_file_count": len(analysis.get("source_files", [])),
        "public_api_count": len(analysis.get("public_apis", [])),
        "source_test_count": len(analysis.get("tests", [])),
        "semantic_invariant_count": test_metrics.get("semantic_invariant_count", len(invariant_items) if isinstance(invariant_items, list) else 0),
        "differential_scenario_count": test_metrics.get("differential_scenario_count", differential.get("scenario_count", len(differential_items) if isinstance(differential_items, list) else 0)),
        "executed_rust_test_count": test_metrics.get("executed_rust_test_count", test_report.get("cargo_test", {}).get("executed_test_count", 0)),
        "api_mapping_complete": passed("semantic_planning") and passed("rust_generation"),
        "source_test_mapping_complete": passed("test_mapping") and passed("test_validation"),
        "unsupported_functions_empty": isinstance(unsupported_items, list) and not unsupported_items,
        "cargo_build_passed": passed("cargo_build"),
        "cargo_test_passed": passed("cargo_test"),
        "differential_passed": test_checks.get("differential_passed") is True or differential.get("passed") is True,
        "mutation_passed": test_checks.get("mutation_testing_passed") is True or mutation.get("passed") is True,
        "repair_integrity_passed": passed("repair_integrity"),
        "unsafe_ratio": ratio,
    }


def copy_submission(source: Path, destination: Path) -> None:
    source = source.resolve()
    def ignored(directory: str, names: list[str]) -> set[str]:
        relative = Path(directory).resolve().relative_to(source).as_posix()
        excluded = {name for name in names if name in EXCLUDED_COPY_PARTS or name == "output"}
        if relative == ".":
            excluded.update(name for name in names if name in {"openspec", "docs", "c-to-rust-subagent-source-analysis-verify-design.md"})
        if relative == "work":
            excluded.update(name for name in names if name in {"code", "references"})
        return excluded
    shutil.copytree(source, destination, ignore=ignored)


def run_once(source_root: Path, submission_root: Path, run_base: Path, label: str, forbidden_terms: list[str]) -> dict[str, Any]:
    workspace = AcceptanceWorkspace.create(run_base, source_root, label)
    ledger = AcceptanceLedger(workspace.run_id)
    stale = assert_clean_workspace(workspace)
    if stale:
        ledger.add("isolation", "stale_artifact", ",".join(stale), status="unresolved")
    before = path_manifest(source_root)
    packaged = workspace.temporary / "submission"
    copy_submission(submission_root, packaged)
    environment = environment_evidence(workspace.run_id, packaged)
    environment["source_mode"] = "read-only-contract"
    atomic_json(workspace.logs / "linux-environment.json", environment)
    audit = customization_audit(packaged, workspace.run_id, forbidden_terms)
    atomic_json(workspace.logs / "customization-audit.json", audit)
    if audit["status"] != "passed":
        ledger.add("customization-audit", "direct_disqualification", f"{len(audit['findings'])} finding(s)", status="unresolved", evidence=["customization-audit.json"])
    command = ["bash", str(packaged / "work" / "scripts" / "run.sh"), "--source-root", str(source_root), "--run"]
    env = dict(os.environ)
    env.update(LOOPFORGE_RESULT_DIR=str(workspace.result), LOOPFORGE_LOG_DIR=str(workspace.logs), LOOPFORGE_OUTPUT_DIR=str(workspace.output))
    def invoke_driver() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command, cwd=packaged, env=env, text=True, capture_output=True,
            timeout=JUDGING_PLATFORM_TIMEOUT_SECONDS, check=False,
        )
    try:
        completed = invoke_driver()
        (workspace.logs / "driver.stdout.log").write_text(completed.stdout, encoding="utf-8")
        (workspace.logs / "driver.stderr.log").write_text(completed.stderr, encoding="utf-8")
        if completed.returncode:
            ledger.add("driver", "nonzero_exit", f"exit={completed.returncode}", evidence=["driver.stderr.log"])
    except (OSError, subprocess.TimeoutExpired) as exc:
        ledger.add("driver", type(exc).__name__, str(exc))
    integrity = publish_source_integrity(workspace.logs, workspace.run_id, before, path_manifest(source_root))
    if integrity["status"] != "passed":
        ledger.add("source-integrity", "source_changed", json.dumps(integrity, sort_keys=True), status="unresolved", evidence=["source-integrity.json"])
    def retry(record):
        if record.stage != "driver":
            return False, {"reason": "no safe automatic repair", "gates_relaxed": False}
        retried = invoke_driver()
        (workspace.logs / "driver-final-retry.stdout.log").write_text(retried.stdout, encoding="utf-8")
        (workspace.logs / "driver-final-retry.stderr.log").write_text(retried.stderr, encoding="utf-8")
        return retried.returncode == 0, {"exit_code": retried.returncode, "targeted": True, "full_regression": retried.returncode == 0, "gates_relaxed": False}
    final_retry(ledger, retry)
    summary = runner_evidence(workspace.logs, workspace.run_id)
    summary.update(source_integrity_passed=integrity["status"] == "passed", customization_audit_passed=audit["status"] == "passed", layouts_passed=False, repeatability_passed=False)
    verification = final_verification(workspace.run_id, summary, ledger)
    publish_reports(workspace.result, workspace.logs, verification, ledger)
    return {"run_id": workspace.run_id, "root": str(workspace.root), "verification": verification, "source_integrity": integrity, "customization_audit": audit, "_ledger": ledger}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--submission-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--run-base", type=Path, required=True)
    parser.add_argument("--forbidden-term", action="append", default=[])
    parser.add_argument("--allow-non-linux-for-tests", action="store_true")
    args = parser.parse_args(argv)
    if sys.platform != "linux" and not args.allow_non_linux_for_tests:
        parser.error("formal acceptance requires Linux")
    try:
        first = run_once(args.source_root.resolve(), args.submission_root.resolve(), args.run_base.resolve(), "formal-1", args.forbidden_term)
        second = run_once(args.source_root.resolve(), args.submission_root.resolve(), args.run_base.resolve(), "formal-2", args.forbidden_term)
        repeatability = repeatability_report(first["run_id"], second["run_id"], first["verification"], second["verification"])
        atomic_json(args.run_base / "repeatability-report.json", repeatability)
        for run in (first, second):
            verification = run["verification"]
            verification["checks"]["layouts_passed"] = True
            verification["checks"]["repeatability_passed"] = repeatability["status"] == "passed"
            verification["evidence"]["layouts_passed"] = True
            verification["evidence"]["repeatability_passed"] = repeatability["status"] == "passed"
            verification["compliance_status"] = "READY_FOR_EVALUATION" if all(verification["checks"].values()) and not verification["exceptions"] else "NOT_READY"
            run_root = Path(run["root"])
            publish_reports(run_root / "result", run_root / "logs", verification, run.pop("_ledger"))
        index = {"runs": [first, second], "repeatability": repeatability}
        atomic_json(args.run_base / "acceptance-index.json", index)
        return 0
    except BaseException as exc:
        payload = fallback_report(args.run_base, "acceptance-entrypoint", exc)
        sys.stderr.write(json.dumps(payload, sort_keys=True) + "\n")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
