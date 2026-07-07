from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

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


def _determine_status(blocked_artifacts: List[str], findings: List[Dict[str, Any]], coverage: Mapping[str, Any], verification: Mapping[str, Any]) -> str:
    if blocked_artifacts:
        return "BLOCKED"
    if verification.get("overall_status") in {"failed", "timeout", "unavailable", "partial"}:
        return "DEGRADED"
    if findings:
        return "DEGRADED"
    if coverage.get("gaps", 0) or coverage.get("unmatched_implementation_count", 0) or coverage.get("unresolved_reference_count", 0):
        return "DEGRADED"
    if verification.get("overall_status") == "skipped":
        return "DEGRADED"
    return "READY"


def compose_report_payload(
    *,
    trace_root: str | Path,
    result_dir: str | Path | None = None,
    design_root: str | Path | None = None,
    source_root: str | Path | None = None,
    profile_path: str | Path | None = None,
) -> Dict[str, Any]:
    trace_path = Path(trace_root)
    result_path = Path(result_dir) if result_dir else trace_path.parents[1] / "result"
    profile = _load_profile(profile_path)
    model_paths = profile.get("reporting", {}).get("model_paths", {})

    source_inventory_path = trace_path / Path(model_paths.get("source_inventory", "02-source-inventory.json")).name
    adapter_selection_path = trace_path / Path(model_paths.get("adapter_selection", "02-adapter-selection.json")).name
    design_model_path = trace_path / Path(model_paths.get("design", "03-design-model.json")).name
    implementation_model_path = trace_path / Path(model_paths.get("implementation", "04-implementation-model.json")).name
    traceability_path = trace_path / Path(model_paths.get("traceability", "05-traceability-matrix.json")).name
    drift_path = trace_path / Path(model_paths.get("drift_findings", "06-drift-findings.json")).name
    risk_path = trace_path / Path(model_paths.get("risk_classification", "07-risk-classification.json")).name
    repair_path = trace_path / Path(model_paths.get("repair_plan", "08-repair-plan.json")).name
    verification_path = trace_path / Path(model_paths.get("verification_results", "09-verification-results.json")).name

    source_inventory = _load_optional_json(source_inventory_path)
    adapter_selection = _load_optional_json(adapter_selection_path)
    design_model = _load_optional_json(design_model_path)
    implementation_model = _load_optional_json(implementation_model_path)
    traceability = _load_optional_json(traceability_path)
    drift = _load_optional_json(drift_path)
    risk = _load_optional_json(risk_path)
    repair = _load_optional_json(repair_path)
    verification = _load_optional_json(verification_path)

    blocked_artifacts: List[str] = []
    for required in (design_model_path, implementation_model_path, traceability_path):
        if not required.is_file():
            blocked_artifacts.append(required.name)

    findings = _safe_list(drift, "findings")
    coverage_summary = traceability.get("coverage_summary", {})
    final_status = _determine_status(blocked_artifacts, findings, coverage_summary, verification)
    evidence_paths = [str(path) for path in (
        source_inventory_path,
        adapter_selection_path,
        design_model_path,
        implementation_model_path,
        traceability_path,
        drift_path,
        risk_path,
        repair_path,
        verification_path,
    ) if path.is_file()]

    return {
        "final_status": final_status,
        "scope": {
            "design_root": str(design_root or ""),
            "source_root": str(source_root or source_inventory.get("source_root", "")),
            "selected_adapter": adapter_selection.get("adapter_id") or source_inventory.get("selected_adapter", ""),
            "fallback_used": adapter_selection.get("fallback_used", False),
            "analyze_only": True,
        },
        "summary": {
            "design_object_count": len(design_model.get("objects", [])),
            "implementation_object_count": len(implementation_model.get("objects", [])),
            "finding_count": len(findings),
            "blocked_artifact_count": len(blocked_artifacts),
        },
        "coverage": coverage_summary,
        "findings": findings,
        "risk_classification": risk,
        "repair_plan": repair,
        "verification": verification or {"overall_status": "skipped"},
        "blocked_artifacts": blocked_artifacts,
        "evidence_paths": evidence_paths,
        "result_dir": str(result_path),
        "trace_root": str(trace_path),
    }


def _render_output_report(payload: Mapping[str, Any]) -> str:
    coverage = payload.get("coverage", {})
    scope = payload.get("scope", {})
    verification = payload.get("verification", {})
    lines = [
        "# Design-Implementation Consistency Report",
        "",
        "## Final Status",
        "",
        f"- Status: {payload.get('final_status', 'UNKNOWN')}",
        f"- Findings: {payload.get('summary', {}).get('finding_count', 0)}",
        f"- Blocked Artifacts: {payload.get('summary', {}).get('blocked_artifact_count', 0)}",
        "",
        "## Scope",
        "",
        f"- Design Root: {scope.get('design_root', '')}",
        f"- Source Root: {scope.get('source_root', '')}",
        f"- Language Adapter: {scope.get('selected_adapter', '')}",
        f"- Fallback Used: {scope.get('fallback_used', False)}",
        f"- Analyze Only: {scope.get('analyze_only', True)}",
        "",
        "## Traceability Coverage",
        "",
        f"- Matched Links: {coverage.get('matched_links', 0)}",
        f"- Partial Links: {coverage.get('partial_links', 0)}",
        f"- Design Gaps: {coverage.get('gaps', 0)}",
        f"- Unmatched Implementation Objects: {coverage.get('unmatched_implementation_count', 0)}",
        "",
        "## Verification",
        "",
        f"- Overall Status: {verification.get('overall_status', 'unknown')}",
    ]
    findings = payload.get("findings", [])
    if findings:
        lines.extend(["", "## Drift Findings", ""])
        for finding in findings:
            lines.append(f"- {finding.get('id', 'finding')}: {finding.get('summary', '')}")
    blocked = payload.get("blocked_artifacts", [])
    if blocked:
        lines.extend(["", "## Blocked Artifacts", ""])
        for artifact in blocked:
            lines.append(f"- {artifact}")
    return "\n".join(lines) + "\n"


def _render_issue_summary(payload: Mapping[str, Any]) -> str:
    lines = ["# Issue Summary", ""]
    findings = payload.get("findings", [])
    if not findings:
        lines.append("- No confirmed drift findings were provided.")
    else:
        for finding in findings:
            lines.append(f"- {finding.get('id', 'finding')}: {finding.get('summary', '')}")
    verification = payload.get("verification", {})
    if verification.get("overall_status") not in {"", "success"}:
        lines.extend(["", "## Verification Status", "", f"- {verification.get('overall_status', 'unknown')}"])
    blocked = payload.get("blocked_artifacts", [])
    if blocked:
        lines.extend(["", "## Blocked Artifacts", ""])
        for artifact in blocked:
            lines.append(f"- {artifact}")
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
