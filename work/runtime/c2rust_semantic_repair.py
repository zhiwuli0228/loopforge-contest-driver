from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from c2rust_analysis import evaluate_semantic_equivalence
from c2rust_invariant_tests import render_invariant_tests
from c2rust_repair import invoke_external_repair_provider, run_repair_loop
from self_healing_loop import RepairConfig, SelfHealingOrchestrator, normalize_diagnostic


def _remove_interim_issues(packet: Any) -> None:
    packet.issues[:] = [item for item in packet.issues if item.get("code") not in {"semantic_gate_failed", "cargo_verification_failed"}]


def run_semantic_repair_loop(packet: Any, analysis: Dict[str, Any], project_payload: Dict[str, Any],
                             semantic: Dict[str, Any], commands: List[str], timeout_seconds: int) -> Dict[str, Any]:
    limit = int(packet.config.get("execution", {}).get("max_semantic_repair_rounds", 2) or 2)
    rounds: List[Dict[str, Any]] = []
    current = semantic
    if not current.get("passed"):
        evidence_path = packet.paths.migration_trace_dir / "semantic-repair-diagnostic.log"
        evidence_text = json.dumps({"failing_checks": current.get("failing_checks", []), "checks": current.get("checks", [])}, indent=2, ensure_ascii=True)
        evidence_path.write_text(evidence_text + "\n", encoding="utf-8")
        source_modules = [item for item in project_payload.get("module_list", []) if str(item).startswith("src/")]
        primary = source_modules[0] if source_modules else "src/lib.rs"
        repair_ir = normalize_diagnostic(
            run_id=str(getattr(packet, "metadata", {}).get("run_id") or getattr(packet, "design_readme_sha256", "semantic-repair-run")),
            source="differential", tool="semantic-gate",
            text=f"differential semantic verification failed\n --> {primary}:1:1\n{evidence_text}",
            project_root=packet.output_project_dir, evidence_path=evidence_path,
            related_ids=current.get("failing_checks", []),
            expected={"semantic_gate": "passed"},
        )
        provider_index = 0

        def provider(task: Dict[str, Any], isolated: Path) -> Dict[str, Any]:
            nonlocal provider_index
            result = invoke_external_repair_provider(packet, isolated, task, "isolated-semantic-repair", provider_index, timeout_seconds)
            provider_index += 1
            return result

        split_commands = [tuple(command.split()) for command in commands]
        orchestrator = SelfHealingOrchestrator(
            run_id=repair_ir["run_id"], project_root=packet.output_project_dir,
            trace_dir=packet.paths.migration_trace_dir, provider=provider,
            config=RepairConfig(
                max_local_rounds=max(1, limit), timeout_seconds=timeout_seconds,
                targeted_command=split_commands[0] if split_commands else ("cargo", "test", "--locked"),
                regression_command=split_commands[1] if len(split_commands) > 1 else ("cargo", "test", "--locked", "--", "--nocapture"),
            ),
            relationship_graph={primary: source_modules[1:]},
        )
        repaired = orchestrator.process(repair_ir)
        orchestrator.final_retry()
        integrity = orchestrator.publish()
        record: Dict[str, Any] = {"round": 0, "repair_ir": repair_ir, "repaired": repaired, "repair_integrity": integrity}
        if integrity.get("compliance_status") == "satisfied" and (repaired or integrity.get("counts", {}).get("final_retry_repaired")):
            crate_name = packet.output_project_name.replace("-", "_")
            invariant_text, plan = render_invariant_tests(crate_name, analysis, analysis.get("semantic_invariants", []))
            invariant_path = packet.output_project_dir / "tests" / "semantic_invariants.rs"
            if invariant_text:
                invariant_path.write_text(invariant_text, encoding="utf-8")
            project_payload["semantic_test_plan"] = plan
            _remove_interim_issues(packet)
            cargo = run_repair_loop(packet, commands, timeout_seconds)
            record["cargo"] = cargo
            current = evaluate_semantic_equivalence(packet, analysis, packet.output_project_dir, project_payload, cargo)
            record["semantic"] = current
            if current.get("passed"):
                _remove_interim_issues(packet)
        rounds.append(record)

    payload = {"passed": bool(current.get("passed")), "rounds_executed": len(rounds),
               "max_rounds": limit, "rounds": rounds, "semantic": current,
               "repair_integrity": rounds[-1].get("repair_integrity", {}) if rounds else {}}
    (packet.paths.migration_trace_dir / "semantic-repair-rounds.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return payload
