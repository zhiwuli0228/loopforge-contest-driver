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

from runtime.code_inventory import build_source_inventory, extract_implementation_model
from runtime.design_scanner import scan_design_root
from runtime.report_writer import compose_report_payload, write_reports
from runtime.traceability_builder import build_traceability, render_traceability_summary
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
    "work/runtime/traceability_builder.py",
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


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FORMAT)


def resolve_path(base: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = (base / path).resolve()
    return path.resolve()


def resolve_default_source_root(workspace_root: Path, platform_name: str | None = None) -> Path:
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


def _guard_outside_source(source_root: Path, *targets: Path) -> None:
    for target in targets:
        try:
            target.resolve().relative_to(source_root.resolve())
        except ValueError:
            continue
        raise ValueError(f"writable destination must be outside SOURCE_ROOT: {target}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _normalized_final_status(payload: Dict[str, Any]) -> str:
    raw_status = payload.get("final_status", "BLOCKED")
    findings = payload.get("findings", [])
    if raw_status == "READY":
        return "FINALIZED_NO_FINDINGS"
    if findings:
        return "FINALIZED_WITH_FINDINGS"
    if raw_status == "DEGRADED":
        return "DEGRADED_FINAL_REPORT_READY"
    return "BLOCKED_WITH_REPORT"


class LoopForgeRunner:
    def __init__(self, workspace_root: Path, work_dir: Path, source_root: Path, result_dir: Path, log_dir: Path) -> None:
        self.workspace_root = workspace_root.resolve()
        self.work_dir = work_dir.resolve()
        self.source_root = source_root.resolve()
        self.result_dir = result_dir.resolve()
        self.log_dir = log_dir.resolve()
        self.trace_dir = self.log_dir / "trace"
        self.consistency_trace_dir = self.trace_dir / TRACE_NAMESPACE
        self.output_path = self.result_dir / "output.md"
        self.issue_summary_path = self.result_dir / "issues" / "00-summary.md"
        self.final_report_path = self.trace_dir / "final-report.md"
        self.run_summary_path = self.trace_dir / "run-summary.json"
        self.self_check_path = self.consistency_trace_dir / "00-preflight-self-check.json"
        self.design_root = self.work_dir / "design"
        self.design_readme_path = self.design_root / "README.md"
        self.config_path = self.work_dir / "loopforge.config.yaml"
        self.config = _load_yaml(self.config_path) if self.config_path.exists() else {}
        profile_rel = self.config.get("task", {}).get("profile", "profiles/examples/default-java-consistency.yaml")
        self.profile_path = resolve_path(self.work_dir, profile_rel)
        _guard_outside_source(self.source_root, self.result_dir, self.log_dir)

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
        if not self.source_root.exists():
            issues.append(f"source_root_missing:{self.source_root}")
        elif not self.source_root.is_dir():
            issues.append(f"source_root_not_directory:{self.source_root}")
        elif not any(self.source_root.rglob("*")):
            issues.append(f"source_root_empty:{self.source_root}")
        if not self.design_readme_path.is_file():
            issues.append(f"design_readme_missing:{self.design_readme_path}")
        issues.extend(self._legacy_reference_issues())

        design_hash = _sha256(self.design_readme_path) if self.design_readme_path.is_file() else ""
        payload = {
            "ok": not issues,
            "generated_at": utc_now(),
            "workspace_root": str(self.workspace_root),
            "work_dir": str(self.work_dir),
            "source_root": str(self.source_root),
            "design_readme_path": str(self.design_readme_path),
            "design_readme_sha256": design_hash,
            "profile_path": str(self.profile_path),
            "issues": issues,
        }
        self.ensure_outputs()
        self.self_check_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        return payload

    def _write_blocked_reports(self, payload: Dict[str, Any], reason: str) -> None:
        self.ensure_outputs()
        report = {
            "final_status": "BLOCKED_WITH_REPORT",
            "reason": reason,
            "issues": payload.get("issues", []),
            "design_readme_sha256": payload.get("design_readme_sha256", ""),
            "source_root": payload.get("source_root", ""),
        }
        self.output_path.write_text(
            "# Design-Implementation Consistency Report\n\n"
            "## Final Status\n\n"
            "- Status: BLOCKED_WITH_REPORT\n"
            f"- Reason: {reason}\n\n"
            "## Issues\n\n"
            + "\n".join(f"- {item}" for item in payload.get("issues", []))
            + "\n",
            encoding="utf-8",
        )
        self.issue_summary_path.write_text(
            "# Issue Summary\n\n"
            f"- {reason}\n"
            + ("\n".join(f"- {item}" for item in payload.get("issues", [])) + "\n" if payload.get("issues") else ""),
            encoding="utf-8",
        )
        self.final_report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        self.run_summary_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    def run(self) -> Dict[str, Any]:
        self.ensure_outputs()
        self_check = self.create_self_check_payload()
        if not self_check["ok"]:
            self._write_blocked_reports(self_check, "self_check_failed")
            return {"ok": False, "status": "BLOCKED_WITH_REPORT", "self_check": self_check}

        profile_arg = str(self.profile_path)
        design_scan = scan_design_root(self.design_root)
        source_inventory = build_source_inventory(self.source_root, profile_arg)
        implementation = extract_implementation_model(self.source_root, profile_arg)
        traceability = build_traceability(design_scan["design_model"], implementation["implementation_model"])

        (self.consistency_trace_dir / "01-design-inventory.json").write_text(
            json.dumps(design_scan["inventory"], indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (self.consistency_trace_dir / "03-design-model.json").write_text(
            json.dumps(design_scan["design_model"], indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (self.consistency_trace_dir / "03-design-model-evidence.json").write_text(
            json.dumps(design_scan["evidence_index"], indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (self.consistency_trace_dir / "02-source-inventory.json").write_text(
            json.dumps(source_inventory, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (self.consistency_trace_dir / "02-adapter-selection.json").write_text(
            json.dumps(source_inventory["selection"], indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (self.consistency_trace_dir / "02-source-inventory-gate.json").write_text(
            json.dumps(
                {
                    "status": "PASS",
                    "selected_adapter": source_inventory["selected_adapter"],
                    "file_count": source_inventory["file_count"],
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (self.consistency_trace_dir / "04-implementation-model.json").write_text(
            json.dumps(implementation["implementation_model"], indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (self.consistency_trace_dir / "04-implementation-model-evidence.json").write_text(
            json.dumps(implementation["inventory"], indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (self.consistency_trace_dir / "05-traceability-matrix.json").write_text(
            json.dumps(traceability, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (self.consistency_trace_dir / "05-traceability-map.md").write_text(
            render_traceability_summary(traceability), encoding="utf-8"
        )
        (self.consistency_trace_dir / "05-traceability-map-evidence.json").write_text(
            json.dumps({"links": traceability.get("links", []), "gaps": traceability.get("gaps", [])}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        for placeholder_name in ("06-drift-findings.json", "07-risk-classification.json", "08-repair-plan.json"):
            placeholder_path = self.consistency_trace_dir / placeholder_name
            if not placeholder_path.exists():
                placeholder_path.write_text(json.dumps({}, indent=2, ensure_ascii=False), encoding="utf-8")

        verification_plan = resolve_verification_commands(
            self.source_root,
            profile_arg,
            adapter_id=source_inventory["selected_adapter"],
        )
        verification = run_verification(
            self.source_root,
            commands=verification_plan["commands"],
            command_source=verification_plan["command_source"],
        )
        (self.consistency_trace_dir / "09-verification-results.json").write_text(
            json.dumps(verification, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        payload = compose_report_payload(
            trace_root=self.consistency_trace_dir,
            result_dir=self.result_dir,
            design_root=self.design_root,
            source_root=self.source_root,
            profile_path=self.profile_path,
        )
        payload["final_status"] = _normalized_final_status(payload)
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
    parser = argparse.ArgumentParser(description="Run the authoritative analyze-only consistency pipeline")
    parser.add_argument("--work-dir", default="work")
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
    source_arg = (args.source_root or "").strip()
    source_root = resolve_path(workspace_root, source_arg) if source_arg else resolve_default_source_root(workspace_root)
    result_dir = resolve_path(workspace_root, args.result_dir)
    log_dir = resolve_path(workspace_root, args.log_dir)

    try:
        runner = LoopForgeRunner(workspace_root, work_dir, source_root, result_dir, log_dir)
        if args.self_check:
            print_json(runner.create_self_check_payload())
        if args.run:
            print_json(runner.run())
    except Exception as exc:
        print_json({"ok": False, "status": "BLOCKED_WITH_REPORT", "error": f"{type(exc).__name__}: {exc}"})
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
