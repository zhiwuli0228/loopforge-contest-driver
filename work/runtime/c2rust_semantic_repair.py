from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from c2rust_analysis import evaluate_semantic_equivalence
from c2rust_invariant_tests import render_invariant_tests
from c2rust_repair import invoke_external_repair_provider, run_repair_loop


def _remove_interim_issues(packet: Any) -> None:
    packet.issues[:] = [item for item in packet.issues if item.get("code") not in {"semantic_gate_failed", "cargo_verification_failed"}]


def run_semantic_repair_loop(packet: Any, analysis: Dict[str, Any], project_payload: Dict[str, Any],
                             semantic: Dict[str, Any], commands: List[str], timeout_seconds: int) -> Dict[str, Any]:
    limit = int(packet.config.get("execution", {}).get("max_semantic_repair_rounds", 2) or 2)
    rounds: List[Dict[str, Any]] = []
    current = semantic
    for index in range(limit):
        if current.get("passed"):
            break
        api_check = next((c for c in current.get("checks", []) if c.get("name") == "api_mapping"), {})
        gaps = [item.get("source_test") for item in project_payload.get("test_mapping", [])
                if item.get("coverage_level") in {"none", "structural_only", "partial_semantic"}]
        task = {
            "kind": "semantic_repair",
            "round": index,
            "project_dir": str(packet.output_project_dir.resolve()),
            "failing_checks": current.get("failing_checks", []),
            "unsupported_apis": api_check.get("unsupported_apis", []),
            "source_test_coverage_gaps": gaps,
            "evidence_paths": [
                str(packet.paths.migration_trace_dir / "semantic-audit-report.md"),
                str(packet.paths.migration_trace_dir / "semantic-invariants.json"),
                str(packet.paths.migration_trace_dir / "02-api-mapping.json"),
                str(packet.paths.migration_trace_dir / "04-test-mapping.json"),
            ],
            "instructions": "Implement missing behavior and strong tests. Do not mark unsupported APIs supported without implementation; do not delete or weaken tests or gates.",
        }
        provider = invoke_external_repair_provider(packet, packet.output_project_dir, task, "semantic-repair", index, timeout_seconds)
        record: Dict[str, Any] = {"round": index, "task": task, "provider": provider}
        if not provider.get("applied"):
            rounds.append(record)
            break

        crate_name = packet.output_project_name.replace("-", "_")
        invariant_text, plan = render_invariant_tests(crate_name, analysis, analysis.get("semantic_invariants", []))
        invariant_path = packet.output_project_dir / "tests" / "semantic_invariants.rs"
        if invariant_text:
            invariant_path.write_text(invariant_text, encoding="utf-8")
        elif invariant_path.exists():
            invariant_path.unlink()
        project_payload["semantic_test_plan"] = plan
        _remove_interim_issues(packet)
        cargo = run_repair_loop(packet, commands, timeout_seconds)
        record["cargo"] = cargo
        current = evaluate_semantic_equivalence(packet, analysis, packet.output_project_dir, project_payload, cargo)
        record["semantic"] = current
        rounds.append(record)
        if current.get("passed"):
            _remove_interim_issues(packet)
            break

    payload = {"passed": bool(current.get("passed")), "rounds_executed": len(rounds),
               "max_rounds": limit, "rounds": rounds, "semantic": current}
    (packet.paths.migration_trace_dir / "semantic-repair-rounds.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return payload
