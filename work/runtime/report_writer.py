from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping

import yaml


DEFAULT_TRACE_ROOT = "logs/trace/consistency"
DEFAULT_FINAL_REPORT = "logs/trace/final-report.md"
DEFAULT_RESULT_REPORT = "result/output.md"
DEFAULT_ISSUES_REPORT = "result/issues/00-summary.md"
DEFAULT_VERIFICATION_RESULTS = "logs/trace/consistency/09-verification-results.json"
DEFAULT_FINAL_REPORT_INPUT = "logs/trace/consistency/09-final-report-input.json"


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> Dict[str, Any]:
    return _load_json(path) if path.is_file() else {}


def _load_profile(path: str | Path | None) -> Dict[str, Any]:
    if path is None:
        return {}
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _safe_list(payload: Any, key: str) -> List[Dict[str, Any]]:
    if isinstance(payload, dict):
        value = payload.get(key, [])
        return value if isinstance(value, list) else []
    return []


def _determine_status(
    blocked_artifacts: List[str],
    verification: Mapping[str, Any],
    retry_repair: Mapping[str, Any],
    repair_execution: Mapping[str, Any],
) -> str:
    if blocked_artifacts:
      return "SUBMISSION_INVALID"
    verification_status = verification.get("overall_status")
    if verification_status == "success":
        return "SUBMISSION_PASSED"
    if verification_status in {"failed", "timeout", "blocked", "unavailable"}:
        if retry_repair:
            return "SUBMISSION_PARTIAL"
        return "SUBMISSION_BLOCKED"
    if repair_execution or verification_status == "partial":
        return "SUBMISSION_PARTIAL"
    return "SUBMISSION_BLOCKED"


def compose_report_payload(
    *,
    trace_root: str | Path,
    result_dir: str | Path | None = None,
    design_root: str | Path | None = None,
    source_root: str | Path | None = None,
    submission_root: str | Path | None = None,
    test_root: str | Path | None = None,
    profile_path: str | Path | None = None,
) -> Dict[str, Any]:
    trace_path = Path(trace_root)
    result_path = Path(result_dir) if result_dir else trace_path.parents[1] / "result"
    profile = _load_profile(profile_path)
    model_paths = profile.get("reporting", {}).get("model_paths", {})

    acceptance_path = trace_path / Path(model_paths.get("acceptance_baseline", "01-acceptance-baseline.json")).name
    source_inventory_path = trace_path / Path(model_paths.get("source_inventory", "02-source-inventory.json")).name
    adapter_selection_path = trace_path / Path(model_paths.get("adapter_selection", "02-adapter-selection.json")).name
    gap_model_path = trace_path / Path(model_paths.get("gap_model", "03-gap-model.json")).name
    repair_batches_path = trace_path / Path(model_paths.get("repair_batches", "04-repair-batches.json")).name
    repair_execution_path = trace_path / Path(model_paths.get("repair_execution", "05-repair-execution.json")).name
    build_verification_path = trace_path / Path(model_paths.get("build_verification", "06-build-verification.json")).name
    black_box_verification_path = trace_path / Path(model_paths.get("black_box_verification", "07-black-box-verification.json")).name
    retry_repair_path = trace_path / Path(model_paths.get("retry_repair", "08-retry-repair.json")).name
    verification_path = trace_path / Path(model_paths.get("verification_results", "09-verification-results.json")).name

    acceptance = _load_optional_json(acceptance_path)
    source_inventory = _load_optional_json(source_inventory_path)
    adapter_selection = _load_optional_json(adapter_selection_path)
    gap_model = _load_optional_json(gap_model_path)
    repair_batches = _load_optional_json(repair_batches_path)
    repair_execution = _load_optional_json(repair_execution_path)
    build_verification = _load_optional_json(build_verification_path)
    black_box_verification = _load_optional_json(black_box_verification_path)
    retry_repair = _load_optional_json(retry_repair_path)
    verification = _load_optional_json(verification_path)

    blocked_artifacts: List[str] = []
    for required in (acceptance_path, source_inventory_path, gap_model_path, verification_path):
        if not required.is_file():
            blocked_artifacts.append(required.name)

    verification_rollup = verification or {
        "overall_status": black_box_verification.get("overall_status")
        or build_verification.get("overall_status")
        or "skipped",
        "results": build_verification.get("results", []) + black_box_verification.get("results", []),
    }
    final_status = _determine_status(blocked_artifacts, verification_rollup, retry_repair, repair_execution)
    evidence_paths = [
        str(path)
        for path in (
            acceptance_path,
            source_inventory_path,
            adapter_selection_path,
            gap_model_path,
            repair_batches_path,
            repair_execution_path,
            build_verification_path,
            black_box_verification_path,
            retry_repair_path,
            verification_path,
        )
        if path.is_file()
    ]

    return {
        "final_status": final_status,
        "scope": {
            "design_root": str(design_root or ""),
            "source_root": str(source_root or source_inventory.get("source_root", "")),
            "submission_root": str(submission_root or source_inventory.get("submission_root", "")),
            "test_root": str(test_root or source_inventory.get("test_root", "")),
            "selected_adapter": adapter_selection.get("adapter_id") or source_inventory.get("selected_adapter", ""),
            "fallback_used": adapter_selection.get("fallback_used", False),
            "repair_and_verify": True,
        },
        "summary": {
            "acceptance_object_count": len(acceptance.get("objects", [])),
            "gap_count": len(_safe_list(gap_model, "findings")) or len(gap_model.get("gaps", [])) if isinstance(gap_model, dict) else 0,
            "repair_batch_count": len(repair_batches.get("batches", [])) if isinstance(repair_batches, dict) else 0,
            "changed_file_count": len(repair_execution.get("changed_files", [])) if isinstance(repair_execution, dict) else 0,
            "blocked_artifact_count": len(blocked_artifacts),
        },
        "acceptance_baseline": acceptance,
        "gap_model": gap_model,
        "repair_batches": repair_batches,
        "repair_execution": repair_execution,
        "build_verification": build_verification,
        "black_box_verification": black_box_verification,
        "retry_repair": retry_repair,
        "verification": verification_rollup,
        "blocked_artifacts": blocked_artifacts,
        "evidence_paths": evidence_paths,
        "result_dir": str(result_path),
        "trace_root": str(trace_path),
    }


def _render_output_report(payload: Mapping[str, Any]) -> str:
    scope = payload.get("scope", {})
    verification = payload.get("verification", {})
    build_verification = payload.get("build_verification", {})
    black_box_verification = payload.get("black_box_verification", {})
    summary = payload.get("summary", {})
    lines = [
        "# Design-Implementation Consistency Report",
        "",
        "## Final Status",
        "",
        f"- Status: {payload.get('final_status', 'UNKNOWN')}",
        f"- Repair Batches: {summary.get('repair_batch_count', 0)}",
        f"- Changed Files: {summary.get('changed_file_count', 0)}",
        f"- Blocked Artifacts: {summary.get('blocked_artifact_count', 0)}",
        "",
        "## Scope",
        "",
        f"- Design Root: {scope.get('design_root', '')}",
        f"- Submission Root: {scope.get('submission_root', '')}",
        f"- Source Root: {scope.get('source_root', '')}",
        f"- Test Root: {scope.get('test_root', '')}",
        f"- Language Adapter: {scope.get('selected_adapter', '')}",
        f"- Fallback Used: {scope.get('fallback_used', False)}",
        f"- Repair And Verify: {scope.get('repair_and_verify', True)}",
        "",
        "## Verification",
        "",
        f"- Overall Status: {verification.get('overall_status', 'unknown')}",
        f"- Build Verification: {build_verification.get('overall_status', 'unknown')}",
        f"- Black-Box Verification: {black_box_verification.get('overall_status', 'unknown')}",
        "",
        "## Repair Summary",
        "",
    ]
    for changed in payload.get("repair_execution", {}).get("changed_files", []):
        lines.append(f"- Changed: {changed}")
    for blocked in payload.get("retry_repair", {}).get("blocked_targets", []):
        lines.append(f"- Retry Blocked: {blocked}")
    if not payload.get("repair_execution", {}).get("changed_files") and not payload.get("retry_repair", {}).get("blocked_targets"):
        lines.append("- No repair execution details were recorded.")
    blocked = payload.get("blocked_artifacts", [])
    if blocked:
        lines.extend(["", "## Blocked Artifacts", ""])
        for artifact in blocked:
            lines.append(f"- {artifact}")
    return "\n".join(lines) + "\n"


def _render_issue_summary(payload: Mapping[str, Any]) -> str:
    lines = ["# Issue Summary", ""]
    final_status = payload.get("final_status", "UNKNOWN")
    lines.append(f"- Final Status: {final_status}")
    verification = payload.get("verification", {})
    lines.extend(["", "## Verification Status", "", f"- {verification.get('overall_status', 'unknown')}"])
    blocked = payload.get("blocked_artifacts", [])
    if blocked:
        lines.extend(["", "## Blocked Artifacts", ""])
        for artifact in blocked:
            lines.append(f"- {artifact}")
    retry = payload.get("retry_repair", {})
    if retry:
        lines.extend(["", "## Retry Repair", ""])
        reason = retry.get("reason") or retry.get("status") or "retry evidence captured"
        lines.append(f"- {reason}")
    return "\n".join(lines) + "\n"


def _render_final_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Final Audit Report",
        "",
        f"Status: {payload.get('final_status', 'UNKNOWN')}",
        "",
        "## Evidence Paths",
        "",
    ]
    for path in payload.get("evidence_paths", []):
        lines.append(f"- {path}")
    lines.extend(["", "## Structured Payload", "", "```json", json.dumps(payload, indent=2, ensure_ascii=False), "```", ""])
    return "\n".join(lines)


def write_reports(payload: Mapping[str, Any], *, result_dir: str | Path, trace_dir: str | Path) -> Dict[str, str]:
    result_path = Path(result_dir)
    trace_path = Path(trace_dir)
    result_path.mkdir(parents=True, exist_ok=True)
    (result_path / "issues").mkdir(parents=True, exist_ok=True)
    trace_path.mkdir(parents=True, exist_ok=True)

    output_path = result_path / "output.md"
    issues_path = result_path / "issues" / "00-summary.md"
    final_report_path = trace_path / "final-report.md"

    output_path.write_text(_render_output_report(payload), encoding="utf-8")
    issues_path.write_text(_render_issue_summary(payload), encoding="utf-8")
    final_report_path.write_text(_render_final_report(payload), encoding="utf-8")
    return {
        "output_path": str(output_path),
        "issue_summary_path": str(issues_path),
        "final_report_path": str(final_report_path),
    }
