#!/usr/bin/env python3
"""Validate produced subagent run evidence artifacts."""

from __future__ import annotations

from pathlib import Path
import sys


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_scalar(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'"}:
        return cleaned[1:-1]
    return cleaned


def parse_stage_contracts(path: Path) -> list[dict[str, str]]:
    stages: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw in read_text(path).splitlines():
        stripped = raw.strip()
        if stripped.startswith("- id:"):
            if current is not None:
                stages.append(current)
            current = {"id": strip_scalar(stripped.split(":", 1)[1])}
            continue
        if current is None:
            continue
        for key in ("subagent", "output"):
            prefix = f"{key}:"
            if stripped.startswith(prefix):
                current[key] = strip_scalar(stripped.split(":", 1)[1])
                break
    if current is not None:
        stages.append(current)
    return stages


def extract_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for raw in text.splitlines():
        stripped = raw.strip()
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        if key in {"stage_id", "executed_by_subagent", "parent_direct_execution", "output_artifact", "gate"}:
            metadata[key] = strip_scalar(value)
    return metadata


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    superspec_path = repo_root / "profiles" / "superspec" / "consistency-check-stages.yaml"
    final_report_path = repo_root / "code" / ".loopforge" / "reports" / "final-report.md"
    errors: list[str] = []

    if not superspec_path.exists():
        print("[FAIL] missing profiles/superspec/consistency-check-stages.yaml", file=sys.stderr)
        return 1

    stages = parse_stage_contracts(superspec_path)
    if not stages:
        print("[FAIL] no stages declared in superspec", file=sys.stderr)
        return 1

    for stage in stages:
        stage_id = stage.get("id", "<unknown>")
        if stage_id == "07-final-report":
            continue
        artifact_path = repo_root / stage.get("output", "")
        if not artifact_path.exists():
            errors.append(f"missing stage artifact: {artifact_path.relative_to(repo_root)}")
            continue
        metadata = extract_metadata(read_text(artifact_path))
        if not metadata.get("executed_by_subagent"):
            errors.append(f"{stage_id}: missing executed_by_subagent")
        if metadata.get("parent_direct_execution") != "false":
            errors.append(f"{stage_id}: parent_direct_execution must be false")

    if not final_report_path.exists():
        errors.append("missing final report: code/.loopforge/reports/final-report.md")
    else:
        final_report_text = read_text(final_report_path)
        if "## Subagent Execution Evidence" not in final_report_text:
            errors.append("final report missing Subagent Execution Evidence section")
        if "All stages completed" in final_report_text and "## Subagent Execution Evidence" not in final_report_text:
            errors.append("final report is monolithic: missing subagent evidence")
        if "| Stage | Subagent | Artifact | Gate | Parent Direct Execution |" not in final_report_text:
            errors.append("final report missing subagent evidence table header")
        if "| 00-preflight |" not in final_report_text:
            errors.append("final report missing per-stage evidence rows")

    if errors:
        for item in errors:
            print(f"[FAIL] {item}", file=sys.stderr)
        return 1

    print("Subagent run evidence validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
