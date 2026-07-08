#!/usr/bin/env python3
"""Authoritative consistency-check runtime runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import yaml

WORK_ROOT = Path(__file__).resolve().parents[1]
if str(WORK_ROOT) not in sys.path:
    sys.path.insert(0, str(WORK_ROOT))

from runtime.code_inventory import build_source_inventory
from runtime.design_scanner import scan_design_root
from runtime.report_writer import compose_report_payload, write_reports
from runtime.verification_runner import resolve_verification_commands, run_verification


ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
TRACE_NAMESPACE = "consistency"
REQUIRED_WORKFLOW_FILES = [
    "INSTRUCTION.md",
    "README.md",
    "work/design/README.md",
    "work/loopforge.config.yaml",
    "work/runtime/tools.py",
    "work/runtime/design_scanner.py",
    "work/runtime/code_inventory.py",
    "work/runtime/verification_runner.py",
    "work/runtime/report_writer.py",
    "work/skills/design-implementation-consistency/SKILL.md",
    "work/skills/loopforge-driver/SKILL.md",
    "work/profiles/examples/default-java-consistency.yaml",
    "work/profiles/superspec/design-implementation-consistency-stages.yaml",
    "work/profiles/superpower/design-implementation-consistency-guards.yaml",
    "work/subagent/design-implementation-consistency-stage-map.yaml",
    "work/subagent/dic-00-preflight.md",
    "work/subagent/dic-01-design-intake.md",
    "work/subagent/dic-02-source-inventory.md",
    "work/subagent/dic-03-design-model.md",
    "work/subagent/dic-04-implementation-model.md",
    "work/subagent/dic-05-traceability-map.md",
    "work/subagent/dic-06-drift-analysis.md",
    "work/subagent/dic-07-risk-classification.md",
    "work/subagent/dic-08-repair-plan.md",
    "work/subagent/dic-09-finalize.md",
]
LEGACY_FORBIDDEN_LITERALS = (
    "c-to-rust-migration-v2",
    "c-to-rust-migration-guards",
    "c-to-rust-migration-stages",
    "logs/trace/c-to-rust",
    "work/rules/loopforge/adapters/c-to-rust",
    "work/subagent/c2r-",
)
FINAL_STATUSES = (
    "SUBMISSION_PASSED",
    "SUBMISSION_PARTIAL",
    "SUBMISSION_BLOCKED",
    "SUBMISSION_INVALID",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FORMAT)


def resolve_path(base: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = (base / path).resolve()
    return path.resolve()


def resolve_default_submission_root(workspace_root: Path, platform_name: str | None = None) -> Path:
    current_platform = platform_name or ("nt" if sys.platform.startswith("win") else "posix")
    if current_platform == "nt":
        return (workspace_root / "__CONTEST_PLATFORM_SOURCE_ROOT__" / "source").resolve()
    for candidate in [Path("/__CONTEST_PLATFORM_SOURCE_ROOT__/source"), Path("/__CONTEST_PLATFORM_SOURCE_ROOT__")]:
        if candidate.is_dir():
            return candidate.resolve()
    return Path("/__CONTEST_PLATFORM_SOURCE_ROOT__/source").resolve()


def _relative_to(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _guard_outside_submission(submission_root: Path, *targets: Path) -> None:
    for target in targets:
        try:
            target.resolve().relative_to(submission_root.resolve())
        except ValueError:
            continue
        raise ValueError(f"writable destination must be outside SUBMISSION_ROOT: {target}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


class LoopForgeRunner:
    def __init__(self, workspace_root: Path, work_dir: Path, submission_root: Path, result_dir: Path, log_dir: Path) -> None:
        self.workspace_root = workspace_root.resolve()
        self.work_dir = work_dir.resolve()
        self.submission_root = submission_root.resolve()
        self.result_dir = result_dir.resolve()
        self.log_dir = log_dir.resolve()
        self.trace_dir = self.log_dir / "trace"
        self.consistency_trace_dir = self.trace_dir / TRACE_NAMESPACE
        self.output_path = self.result_dir / "output.md"
        self.issue_summary_path = self.result_dir / "issues" / "00-summary.md"
        self.final_report_path = self.trace_dir / "final-report.md"
        self.run_summary_path = self.trace_dir / "run-summary.json"
        self.self_check_path = self.consistency_trace_dir / "00-preflight-self-check.json"
        self.config_path = self.work_dir / "loopforge.config.yaml"
        self.config = _load_yaml(self.config_path) if self.config_path.exists() else {}
        profile_rel = self.config.get("task", {}).get("profile", "profiles/examples/default-java-consistency.yaml")
        self.profile_path = resolve_path(self.work_dir, profile_rel)
        submission_cfg = self.config.get("submission", {})
        self.package_readme_path = self.submission_root / submission_cfg.get("readme", "README.md")
        self.design_root = self.submission_root / submission_cfg.get("design_dir", "design-docs")
        self.code_root = self.submission_root / submission_cfg.get("code_dir", "code")
        self.test_root = self.submission_root / submission_cfg.get("test_dir", "test-cases")
        self.mutable_support_assets = [self.submission_root / item for item in submission_cfg.get("mutable_support_assets", [])]
        self.metadata_paths = [self.submission_root / item for item in submission_cfg.get("metadata_files", [])]
        _guard_outside_submission(self.submission_root, self.result_dir, self.log_dir)

    def ensure_outputs(self) -> None:
        self.result_dir.mkdir(parents=True, exist_ok=True)
        (self.result_dir / "issues").mkdir(parents=True, exist_ok=True)
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.consistency_trace_dir.mkdir(parents=True, exist_ok=True)

    def _legacy_reference_issues(self) -> List[str]:
        issues: List[str] = []
        authoritative_files = [
            self.work_dir / "skills" / "design-implementation-consistency" / "SKILL.md",
            self.work_dir / "skills" / "loopforge-driver" / "SKILL.md",
            self.work_dir / "scripts" / "run.sh",
        ]
        for path in authoritative_files:
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for literal in LEGACY_FORBIDDEN_LITERALS:
                if literal in text:
                    issues.append(f"legacy_reference:{_relative_to(path, self.workspace_root)}:{literal}")
        return issues

    def create_self_check_payload(self) -> Dict[str, Any]:
        issues: List[str] = []
        for relative in REQUIRED_WORKFLOW_FILES:
            if not (self.workspace_root / relative).exists():
                issues.append(f"missing_required_asset:{relative}")
        if not self.submission_root.exists():
            issues.append(f"submission_root_missing:{self.submission_root}")
        elif not self.submission_root.is_dir():
            issues.append(f"submission_root_not_directory:{self.submission_root}")
        elif not any(self.submission_root.rglob("*")):
            issues.append(f"submission_root_empty:{self.submission_root}")
        if not self.package_readme_path.is_file():
            issues.append(f"submission_readme_missing:{self.package_readme_path}")
        if not self.design_root.is_dir():
            issues.append(f"design_docs_missing:{self.design_root}")
        if not self.code_root.is_dir():
            issues.append(f"code_root_missing:{self.code_root}")
        if not self.test_root.is_dir() and not any(path.is_file() for path in self.metadata_paths):
            issues.append(f"test_root_missing:{self.test_root}")
        issues.extend(self._legacy_reference_issues())

        design_hash = _sha256(self.package_readme_path) if self.package_readme_path.is_file() else ""
        resolved_metadata = next((path for path in self.metadata_paths if path.is_file()), None)
        payload = {
            "ok": not issues,
            "generated_at": utc_now(),
            "workspace_root": str(self.workspace_root),
            "work_dir": str(self.work_dir),
            "submission_root": str(self.submission_root),
            "submission_readme_path": str(self.package_readme_path),
            "submission_readme_sha256": design_hash,
            "design_root": str(self.design_root),
            "code_root": str(self.code_root),
            "test_root": str(self.test_root),
            "mutable_support_assets": [str(path) for path in self.mutable_support_assets],
            "metadata_file": str(resolved_metadata) if resolved_metadata else "",
            "profile_path": str(self.profile_path),
            "issues": issues,
        }
        self.ensure_outputs()
        self.self_check_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        (self.consistency_trace_dir / "00-submission-layout.json").write_text(
            json.dumps(
                {
                    "submission_root": str(self.submission_root),
                    "submission_readme": str(self.package_readme_path),
                    "design_root": str(self.design_root),
                    "code_root": str(self.code_root),
                    "test_root": str(self.test_root) if self.test_root.is_dir() else "",
                    "mutable_support_assets": [str(path) for path in self.mutable_support_assets],
                    "metadata_file": str(resolved_metadata) if resolved_metadata else "",
                },
                indent=2,
                ensure_ascii=True,
            ) + "\n",
            encoding="utf-8",
        )
        return payload

    def _write_terminal_reports(self, payload: Dict[str, Any], reason: str, status: str) -> None:
        self.ensure_outputs()
        report = {
            "final_status": status,
            "reason": reason,
            "issues": payload.get("issues", []),
            "submission_readme_sha256": payload.get("submission_readme_sha256", ""),
            "submission_root": payload.get("submission_root", ""),
        }
        self.output_path.write_text(
            "# Design-Implementation Consistency Report\n\n"
            "## Final Status\n\n"
            f"- Status: {status}\n"
            f"- Reason: {reason}\n\n"
            "## Issues\n\n"
            + "\n".join(f"- {item}" for item in payload.get("issues", []))
            + "\n",
            encoding="utf-8",
        )
        self.issue_summary_path.write_text(
            "# Issue Summary\n\n"
            f"- {status}: {reason}\n"
            + ("\n".join(f"- {item}" for item in payload.get("issues", [])) + "\n" if payload.get("issues") else ""),
            encoding="utf-8",
        )
        self.final_report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        self.run_summary_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    def _write_json(self, name: str, payload: Dict[str, Any]) -> None:
        (self.consistency_trace_dir / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def run(self) -> Dict[str, Any]:
        self.ensure_outputs()
        self_check = self.create_self_check_payload()
        if not self_check["ok"]:
            self._write_terminal_reports(self_check, "self_check_failed", "SUBMISSION_INVALID")
            return {"ok": False, "status": "SUBMISSION_INVALID", "self_check": self_check}

        profile_arg = str(self.profile_path)
        design_scan = scan_design_root(self.design_root, submission_readme=self.package_readme_path)
        source_inventory = build_source_inventory(
            self.code_root,
            profile_arg,
            submission_root=self.submission_root,
            test_root=self.test_root if self.test_root.is_dir() else None,
        )
        self._write_json("01-acceptance-baseline.json", design_scan["design_model"])
        self._write_json("02-source-inventory.json", source_inventory)
        self._write_json("02-adapter-selection.json", source_inventory["selection"])
        gap_model = {
            "objects": design_scan["design_model"].get("objects", []),
            "gaps": [],
            "findings": [],
            "summary": {"acceptance_object_count": len(design_scan["design_model"].get("objects", []))},
        }
        repair_batches = {"batches": [], "strategy": "no-op-unattended-runner"}
        repair_execution = {"changed_files": [], "status": "no-op", "reason": "runner preserves repair-aware artifacts without autonomous source mutation"}
        self._write_json("03-gap-model.json", gap_model)
        self._write_json("04-repair-batches.json", repair_batches)
        self._write_json("05-repair-execution.json", repair_execution)

        verification_plan = resolve_verification_commands(
            self.submission_root,
            profile_arg,
            adapter_id=source_inventory["selected_adapter"],
            submission_root=self.submission_root,
        )
        verification = run_verification(
            self.submission_root,
            commands=verification_plan["commands"],
            command_source=verification_plan["command_source"],
        )
        build_results = [item for item in verification.get("results", []) if item.get("verification_class") != "black_box_tests"]
        black_box_results = [item for item in verification.get("results", []) if item.get("verification_class") == "black_box_tests"]
        build_status = "success" if build_results and all(item["status"] == "success" for item in build_results) else (
            "blocked" if any(item["status"] == "blocked" for item in build_results) else
            "failed" if any(item["status"] == "failed" for item in build_results) else
            "timeout" if any(item["status"] == "timeout" for item in build_results) else
            "unavailable" if build_results and all(item["status"] == "unavailable" for item in build_results) else
            "partial" if build_results else "skipped"
        )
        black_box_status = "success" if black_box_results and all(item["status"] == "success" for item in black_box_results) else (
            "blocked" if any(item["status"] == "blocked" for item in black_box_results) else
            "failed" if any(item["status"] == "failed" for item in black_box_results) else
            "timeout" if any(item["status"] == "timeout" for item in black_box_results) else
            "unavailable" if black_box_results and all(item["status"] == "unavailable" for item in black_box_results) else
            "partial" if black_box_results else "skipped"
        )
        build_verification = {"overall_status": build_status, "results": build_results, "command_source": verification_plan["command_source"]}
        black_box_verification = {"overall_status": black_box_status, "results": black_box_results, "command_source": verification_plan["command_source"]}
        retry_repair = {"status": "not_attempted", "reason": "runner does not autonomously re-enter repair without an external repair provider"}

        self._write_json("06-build-verification.json", build_verification)
        self._write_json("07-black-box-verification.json", black_box_verification)
        self._write_json("08-retry-repair.json", retry_repair)
        self._write_json("09-verification-results.json", verification)

        payload = compose_report_payload(
            trace_root=self.consistency_trace_dir,
            result_dir=self.result_dir,
            design_root=self.design_root,
            source_root=self.code_root,
            submission_root=self.submission_root,
            test_root=self.test_root if self.test_root.is_dir() else None,
            profile_path=self.profile_path,
        )
        payload_output = self.consistency_trace_dir / "09-final-report-input.json"
        payload_output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        outputs = write_reports(payload, result_dir=self.result_dir, trace_dir=self.trace_dir)

        summary = {
            "ok": True,
            "status": payload["final_status"],
            "generated_at": utc_now(),
            "self_check": self_check,
            "selected_adapter": source_inventory["selected_adapter"],
            "verification_status": verification.get("overall_status", "unknown"),
            "outputs": outputs,
            "trace_root": str(self.consistency_trace_dir),
        }
        self.run_summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        return summary


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the authoritative repair-and-verify consistency pipeline")
    parser.add_argument("--work-dir", default="work")
    parser.add_argument("--submission-root")
    parser.add_argument("--source-root")
    parser.add_argument("--result-dir", default="result")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--run", action="store_true")
    return parser.parse_args(argv)


def print_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    if not any([args.self_check, args.run]):
        print("No action provided.", file=sys.stderr)
        return 2

    script_root = Path(__file__).resolve().parent.parent.parent
    work_dir = resolve_path(script_root, args.work_dir)
    workspace_root = work_dir.parent
    submission_arg = (args.submission_root or args.source_root or "").strip()
    submission_root = resolve_path(workspace_root, submission_arg) if submission_arg else resolve_default_submission_root(workspace_root)
    result_dir = resolve_path(workspace_root, args.result_dir)
    log_dir = resolve_path(workspace_root, args.log_dir)

    try:
        runner = LoopForgeRunner(workspace_root, work_dir, submission_root, result_dir, log_dir)
        if args.self_check:
            print_json(runner.create_self_check_payload())
        if args.run:
            print_json(runner.run())
    except Exception as exc:
        print_json({"ok": False, "status": "SUBMISSION_BLOCKED", "error": f"{type(exc).__name__}: {exc}"})
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
