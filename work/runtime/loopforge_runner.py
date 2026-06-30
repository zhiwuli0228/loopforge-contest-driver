#!/usr/bin/env python3
"""LoopForge execution orchestrator for the FlashDB C-to-Rust contest flow."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agent_task_packet import AgentTaskPacket, RuntimePaths
from c2rust_analysis import analyze_source, evaluate_semantic_equivalence
from c2rust_project_generator import generate_project
from c2rust_repair import run_repair_loop


ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
README_CANDIDATES = ["README.md", "README", "READNE.md", "readme.md", "Readme.md"]
REQUIRED_RUNTIME_FILES = [
    "work/runtime/loopforge_runner.py",
    "work/runtime/agent_task_packet.py",
    "work/runtime/c2rust_analysis.py",
    "work/runtime/c2rust_project_generator.py",
    "work/runtime/c2rust_repair.py",
]
REQUIRED_ADAPTER_FILES = [
    "work/rules/loopforge/adapters/c2rust-flashdb/source-contract.md",
    "work/rules/loopforge/adapters/c2rust-flashdb/output-contract.md",
    "work/rules/loopforge/adapters/c2rust-flashdb/test-migration-contract.md",
    "work/rules/loopforge/adapters/c2rust-flashdb/unsafe-contract.md",
    "work/rules/loopforge/adapters/c2rust-flashdb/verification-contract.md",
    "work/rules/loopforge/adapters/c2rust-flashdb/semantic-equivalence-contract.md",
    "work/rules/loopforge/adapters/c2rust-flashdb/repair-loop-contract.md",
]
REQUIRED_MISC_FILES = [
    "INSTRUCTION.md",
    "README.md",
    "work/code/README.md",
    "work/loopforge.config.yaml",
    "work/profiles/examples/c2rust-flashdb-migration.yaml",
    "work/skills/c2rust-flashdb-migration/SKILL.md",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FORMAT)


def parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "~"}:
        return None
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    if value.lstrip("-").isdigit():
        try:
            return int(value)
        except ValueError:
            return value
    return value


def parse_simple_yaml(text: str) -> Dict[str, Any]:
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Any]] = [(-1, root)]
    lines = text.splitlines()

    def next_meaningful(start: int) -> Optional[str]:
        for candidate in lines[start + 1 :]:
            stripped = candidate.strip()
            if stripped and not stripped.startswith("#"):
                return candidate
        return None

    for index, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        container = stack[-1][1]

        if stripped.startswith("- "):
            if not isinstance(container, list):
                raise ValueError(f"invalid list item near line {index + 1}")
            item_text = stripped[2:].strip()
            if ":" in item_text:
                item_key, item_value = item_text.split(":", 1)
                item_key = item_key.strip()
                item_value = item_value.strip()
                item: Dict[str, Any] = {}
                if item_value:
                    item[item_key] = parse_scalar(item_value)
                else:
                    upcoming = next_meaningful(index)
                    nested: Any = {}
                    if upcoming is not None:
                        next_indent = len(upcoming) - len(upcoming.lstrip(" "))
                        if next_indent > indent and upcoming.strip().startswith("- "):
                            nested = []
                    item[item_key] = nested
                container.append(item)
                stack.append((indent, item))
            else:
                container.append(parse_scalar(item_text))
            continue

        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            if isinstance(container, list):
                raise ValueError(f"unexpected mapping item near line {index + 1}")
            container[key] = parse_scalar(value)
            continue

        upcoming = next_meaningful(index)
        next_container: Any = {}
        if upcoming is not None:
            next_indent = len(upcoming) - len(upcoming.lstrip(" "))
            if next_indent > indent and upcoming.strip().startswith("- "):
                next_container = []
        if isinstance(container, list):
            raise ValueError(f"unexpected nested mapping near line {index + 1}")
        container[key] = next_container
        stack.append((indent, next_container))

    return root


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def path_is_relative_to(path: Path, other: Path) -> bool:
    try:
        path.relative_to(other)
        return True
    except ValueError:
        return False


class LoopForgeRunner:
    def __init__(self, workspace_root: Path, work_dir: Path, source_root: Path, result_dir: Path, log_dir: Path) -> None:
        self.workspace_root = workspace_root.resolve()
        self.work_dir = work_dir.resolve()
        self.source_root = source_root.resolve()
        self.result_dir = result_dir.resolve()
        self.log_dir = log_dir.resolve()
        self.trace_dir = self.log_dir / "trace"
        self.artifact_dir = self.trace_dir / "execution-adapter"
        self.migration_trace_dir = self.trace_dir / "c2rust"
        self.project_dir = self.workspace_root / "flashDB_rust"
        self.config = parse_simple_yaml((self.work_dir / "loopforge.config.yaml").read_text(encoding="utf-8"))
        profile_rel = str(self.config.get("task", {}).get("profile", "")).replace("/", os.sep)
        self.profile = parse_simple_yaml((self.work_dir / profile_rel).read_text(encoding="utf-8"))
        self.result_output_path = self.result_dir / "output.md"
        self.issue_summary_path = self.result_dir / "issues" / "00-summary.md"
        self.interaction_log_path = self.log_dir / "interaction.md"
        self.run_summary_path = self.trace_dir / "run-summary.json"
        self.final_report_path = self.trace_dir / "final-report.md"
        self.self_check_path = self.artifact_dir / "state" / "self-check.json"
        self.detect_path = self.artifact_dir / "state" / "detect-summary.json"
        self.verify_path = self.artifact_dir / "state" / "verification-summary.json"
        self.orchestrator_state_path = self.artifact_dir / "state" / "orchestrator-state.json"
        self.packet_snapshot_path = self.artifact_dir / "state" / "packet.json"
        self.gates_path = self.artifact_dir / "gate-events.md"
        self.mode_artifacts_path = self.artifact_dir / "mode-artifacts.md"
        self.source_inventory_md = self.migration_trace_dir / "01-source-inventory.md"
        self.source_inventory_json = self.migration_trace_dir / "01-source-inventory.json"
        self.api_mapping_md = self.migration_trace_dir / "02-api-mapping.md"
        self.api_mapping_json = self.migration_trace_dir / "02-api-mapping.json"
        self.migration_plan_md = self.migration_trace_dir / "03-migration-plan.md"
        self.migration_plan_json = self.migration_trace_dir / "03-migration-plan.json"
        self.test_mapping_md = self.migration_trace_dir / "04-test-mapping.md"
        self.test_mapping_json = self.migration_trace_dir / "04-test-mapping.json"
        self.migration_summary_md = self.migration_trace_dir / "05-migration-summary.md"
        self.verification_report_md = self.migration_trace_dir / "06-verification-report.md"
        self.unsafe_ratio_json = self.migration_trace_dir / "unsafe-ratio.json"
        self.gate_events: List[Dict[str, str]] = []

    def create_packet(self) -> AgentTaskPacket:
        packet = AgentTaskPacket(
            paths=RuntimePaths(
                workspace_root=self.workspace_root,
                work_dir=self.work_dir,
                source_root=self.source_root,
                result_dir=self.result_dir,
                log_dir=self.log_dir,
                trace_dir=self.trace_dir,
                artifact_dir=self.artifact_dir,
                migration_trace_dir=self.migration_trace_dir,
                project_dir=self.project_dir,
            ),
            config=self.config,
            profile=self.profile,
            readme_candidates=list(self.config.get("source", {}).get("readme_candidates", README_CANDIDATES)),
            max_repair_rounds=int(self.config.get("execution", {}).get("max_repair_rounds", 2) or 2),
        )
        packet.metadata["source_root_resolution"] = str(self.source_root)
        return packet

    def ensure_outputs(self) -> None:
        self.result_dir.mkdir(parents=True, exist_ok=True)
        (self.result_dir / "issues").mkdir(parents=True, exist_ok=True)
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        (self.artifact_dir / "state").mkdir(parents=True, exist_ok=True)
        self.migration_trace_dir.mkdir(parents=True, exist_ok=True)
        if not self.interaction_log_path.exists():
            self.interaction_log_path.write_text("# Interaction Log\n\nNo manual interaction.\n", encoding="utf-8")
        self.mode_artifacts_path.write_text(
            "\n".join(
                [
                    "# Mode Artifacts",
                    "",
                    f"- mode: `{self.config.get('task', {}).get('mode', 'migration')}`",
                    f"- generated_at: `{utc_now()}`",
                    "",
                    "- `01-source-inventory.md/json`",
                    "- `02-api-mapping.md/json`",
                    "- `03-migration-plan.md/json`",
                    "- `04-test-mapping.md/json`",
                    "- `05-migration-summary.md`",
                    "- `06-verification-report.md`",
                    "- `repair-rounds.md/json`",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def write_templates(self) -> None:
        self.result_output_path.write_text(
            "\n".join(
                [
                    "# Output",
                    "",
                    "- status: `NOT_RUN`",
                    "- source_root: `NOT_RUN`",
                    "- selected_source_readme: `NOT_RUN`",
                    "- flashdb_root: `NOT_RUN`",
                    "- rust_project: `NOT_RUN`",
                    "- cargo_build: `NOT_RUN`",
                    "- cargo_test: `NOT_RUN`",
                    "- unsafe_gate: `NOT_RUN`",
                    "- semantic_gate: `NOT_RUN`",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        self.issue_summary_path.write_text(
            "\n".join(
                [
                    "# Issue Summary",
                    "",
                    "- final_status: NOT_RUN",
                    "- source_root: NOT_RUN",
                    "- issue_count: NOT_RUN",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def normalize_commands(self) -> List[str]:
        commands = self.config.get("verification", {}).get("commands", [])
        if isinstance(commands, dict):
            default_commands = commands.get("default", [])
            if isinstance(default_commands, list):
                return [str(item) for item in default_commands]
        if isinstance(commands, list):
            return [str(item) for item in commands]
        return []

    def record_gate_event(self, gate: str, passed: bool, detail: str) -> None:
        self.gate_events.append({"gate": gate, "status": "PASS" if passed else "FAIL", "detail": detail})
        lines = ["| Gate | Status | Detail |", "|---|---|---|"]
        lines.extend(f"| {item['gate']} | {item['status']} | {item['detail']} |" for item in self.gate_events)
        self.gates_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def self_check(self, packet: AgentTaskPacket) -> Dict[str, Any]:
        required_files = REQUIRED_RUNTIME_FILES + REQUIRED_ADAPTER_FILES + REQUIRED_MISC_FILES
        missing = [path for path in required_files if not (self.workspace_root / path).exists()]
        work_code_readme = self.workspace_root / "work" / "code" / "README.md"
        invalid_source = path_is_relative_to(work_code_readme.resolve(), self.source_root) if work_code_readme.exists() else False
        if invalid_source:
            packet.add_issue("invalid_source_root", "work/code/README.md is a contest requirement document, not a FlashDB source root")
        for item in missing:
            packet.add_issue("required_asset_missing", item)
        payload = {
            "ok": not missing and not invalid_source,
            "required_files_checked": required_files,
            "missing_files": missing,
            "source_root": str(self.source_root),
            "local_fallback_source_dir": str(self.config.get("platform", {}).get("local_fallback_source_dir", "")),
            "invalid_source_root": invalid_source,
            "issues": list(packet.issues),
        }
        write_json(self.self_check_path, payload)
        self.record_gate_event("SELF_CHECK", payload["ok"], "runtime and adapter assets validated")
        return payload

    def write_source_inventory(self, analysis: Dict[str, Any]) -> None:
        lines = [
            "# Source Inventory",
            "",
            f"- selected_readme: `{analysis.get('readme_path') or 'missing'}`",
            f"- source_root: `{self.source_root}`",
            f"- resolved_flashdb_root: `{analysis.get('flashdb_root') or 'missing'}`",
            "",
            "## Source Files",
            "",
        ]
        lines.extend([f"- `{item}`" for item in analysis.get("src_files", [])] or ["- none"])
        lines.extend(["", "## Test Files", ""])
        lines.extend([f"- `{item}`" for item in analysis.get("test_files", [])] or ["- none"])
        lines.extend(["", "## Public APIs", ""])
        lines.extend([f"- `{item}`" for item in analysis.get("public_apis", [])] or ["- none"])
        lines.extend(["", "## Structs", ""])
        lines.extend([f"- `{item}`" for item in analysis.get("structs", [])] or ["- none"])
        lines.extend(["", "## Macros", ""])
        lines.extend([f"- `{item}`" for item in analysis.get("macros", [])] or ["- none"])
        lines.extend(["", "## I/O Boundaries", ""])
        lines.extend([f"- `{item}`" for item in analysis.get("io_boundaries", [])] or ["- none"])
        lines.append("")
        self.source_inventory_md.write_text("\n".join(lines), encoding="utf-8")
        write_json(self.source_inventory_json, analysis)

    def write_api_mapping(self, analysis: Dict[str, Any], project_payload: Optional[Dict[str, Any]]) -> None:
        mapping_payload = {
            "support_level": analysis.get("support_level", "unsupported"),
            "mapped_apis": project_payload.get("mapped_apis", []) if project_payload else [],
            "unsupported_apis": project_payload.get("unsupported_apis", analysis.get("public_apis", [])) if project_payload else analysis.get("public_apis", []),
            "source_coverage": project_payload.get("source_coverage", {}) if project_payload else {},
            "bootstrap_only": bool(project_payload.get("bootstrap_only", False)) if project_payload else False,
        }
        lines = [
            "# API Mapping",
            "",
            f"- support_level: `{mapping_payload['support_level']}`",
            f"- bootstrap_only: `{str(mapping_payload['bootstrap_only']).lower()}`",
            "",
            "## Mapped APIs",
            "",
        ]
        lines.extend([f"- `{item}`" for item in mapping_payload["mapped_apis"]] or ["- none"])
        lines.extend(["", "## Unsupported APIs", ""])
        lines.extend([f"- `{item}`" for item in mapping_payload["unsupported_apis"]] or ["- none"])
        lines.extend(["", "## Source Coverage", ""])
        for key, value in mapping_payload["source_coverage"].items():
            lines.append(f"- `{key}`: `{value}`")
        lines.append("")
        self.api_mapping_md.write_text("\n".join(lines), encoding="utf-8")
        write_json(self.api_mapping_json, mapping_payload)

    def write_migration_plan(self, analysis: Dict[str, Any], project_payload: Optional[Dict[str, Any]]) -> None:
        payload = {
            "support_level": analysis.get("support_level", "unsupported"),
            "module_list": project_payload.get("module_list", []) if project_payload else [],
            "test_files": analysis.get("test_files", []),
            "bootstrap_only": bool(project_payload.get("bootstrap_only", False)) if project_payload else False,
            "semantic_equivalence_claim": project_payload.get("semantic_equivalence_claim", "not_generated") if project_payload else "not_generated",
        }
        lines = [
            "# Migration Plan",
            "",
            f"- support_level: `{payload['support_level']}`",
            f"- semantic_equivalence_claim: `{payload['semantic_equivalence_claim']}`",
            "",
            "## Crate Layout",
            "",
        ]
        lines.extend([f"- `flashDB_rust/{item}`" for item in payload["module_list"]] or ["- generation skipped"])
        lines.extend(["", "## Test Migration List", ""])
        lines.extend([f"- `{item}`" for item in payload["test_files"]] or ["- none"])
        lines.extend(["", "## Unsupported Or Degraded Behaviors", ""])
        if payload["bootstrap_only"]:
            lines.append("- The generated project is only a bootstrap skeleton and must not claim full semantic equivalence.")
        else:
            lines.append("- none")
        lines.append("")
        self.migration_plan_md.write_text("\n".join(lines), encoding="utf-8")
        write_json(self.migration_plan_json, payload)

    def write_test_mapping(self, project_payload: Optional[Dict[str, Any]]) -> None:
        mapping = project_payload.get("test_mapping", []) if project_payload else []
        lines = ["# Test Mapping", "", "## Scenario Mapping", ""]
        if mapping:
            for item in mapping:
                lines.append(
                    f"- `{item['source_test']}` -> `{item['rust_test_file']}` "
                    f"({item['mapping']}, coverage=`{item.get('coverage_level', 'unknown')}`)"
                )
        else:
            lines.append("- none")
        lines.append("")
        self.test_mapping_md.write_text("\n".join(lines), encoding="utf-8")
        write_json(self.test_mapping_json, {"test_mapping": mapping})

    def write_migration_summary(self, analysis: Dict[str, Any], project_payload: Optional[Dict[str, Any]]) -> None:
        lines = [
            "# Migration Summary",
            "",
            f"- generated_at: `{utc_now()}`",
            f"- source_root: `{self.source_root}`",
            f"- support_level: `{analysis.get('support_level', 'unsupported')}`",
            f"- project_dir: `{self.project_dir}`",
            "",
            "## Generation",
            "",
        ]
        if project_payload:
            lines.extend([f"- `{item}`" for item in project_payload.get("module_list", [])])
        else:
            lines.append("- project generation skipped")
        lines.append("")
        self.migration_summary_md.write_text("\n".join(lines), encoding="utf-8")

    def verify_generated(self, packet: AgentTaskPacket, project_payload: Dict[str, Any], repair_payload: Dict[str, Any], semantic_payload: Dict[str, Any]) -> Dict[str, Any]:
        cargo_manifest_exists = (self.project_dir / "Cargo.toml").is_file()
        src_exists = (self.project_dir / "src").is_dir()
        tests_exists = (self.project_dir / "tests").is_dir()

        total_lines = 0
        unsafe_lines = 0
        unsafe_files: List[Dict[str, Any]] = []
        for rust_file in self.project_dir.rglob("*.rs"):
            if "target" in rust_file.parts:
                continue
            file_total = 0
            file_unsafe = 0
            for line in rust_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("//"):
                    continue
                file_total += 1
                if "unsafe" in stripped:
                    file_unsafe += 1
            total_lines += file_total
            unsafe_lines += file_unsafe
            unsafe_files.append({"file": str(rust_file), "code_lines": file_total, "unsafe_lines": file_unsafe})
        unsafe_ratio = (unsafe_lines / total_lines) if total_lines else 0.0
        unsafe_payload = {
            "project": str(self.project_dir),
            "total_code_lines": total_lines,
            "unsafe_lines": unsafe_lines,
            "unsafe_ratio": unsafe_ratio,
            "max_ratio": 0.10,
            "passed": unsafe_ratio < 0.10,
            "files": unsafe_files,
            "generated_at": utc_now(),
        }
        write_json(self.unsafe_ratio_json, unsafe_payload)

        test_mapping_payload = json.loads(self.test_mapping_json.read_text(encoding="utf-8"))
        test_mapping_gate = bool(test_mapping_payload.get("test_mapping"))

        packet.set_gate("cargo_build", bool(repair_payload.get("build_ok")), "cargo build gate", {"rounds_executed": repair_payload.get("rounds_executed", 0)})
        packet.set_gate("cargo_test", bool(repair_payload.get("test_ok")), "cargo test gate", {"rounds_executed": repair_payload.get("rounds_executed", 0)})
        packet.set_gate("unsafe", unsafe_payload["passed"], "unsafe gate", unsafe_payload)
        packet.set_gate("semantic", bool(semantic_payload.get("passed")), "semantic gate", semantic_payload)
        packet.set_gate("test_mapping", test_mapping_gate, "test mapping gate", test_mapping_payload)
        packet.set_gate("repair_loop", bool(repair_payload.get("ok")), "repair loop gate", {"rounds_executed": repair_payload.get("rounds_executed", 0)})

        verification_payload = {
            "cargo_manifest_exists": cargo_manifest_exists,
            "src_exists": src_exists,
            "tests_exists": tests_exists,
            "project_generation": project_payload,
            "repair_loop": repair_payload,
            "unsafe": unsafe_payload,
            "semantic": semantic_payload,
            "test_mapping_gate": test_mapping_gate,
            "ready": packet.ready(),
            "status": "READY_FOR_EVALUATION" if packet.ready() else "BLOCKED_WITH_REPORT",
            "gates": {name: gate.to_dict() for name, gate in packet.gates.items()},
            "issues": packet.issues,
        }
        write_json(self.verify_path, verification_payload)
        lines = [
            "# Verification Report",
            "",
            f"- status: `{verification_payload['status']}`",
            "",
            "## Gates",
            "",
            json.dumps(verification_payload["gates"], indent=2, ensure_ascii=True),
            "",
            "## Repair Loop",
            "",
            json.dumps(repair_payload, indent=2, ensure_ascii=True),
            "",
            "## Semantic",
            "",
            json.dumps(semantic_payload, indent=2, ensure_ascii=True),
            "",
            "## Issues",
            "",
            json.dumps(packet.issues, indent=2, ensure_ascii=True),
            "",
        ]
        self.verification_report_md.write_text("\n".join(lines), encoding="utf-8")
        return verification_payload

    def finalize(self, packet: AgentTaskPacket, self_check_payload: Dict[str, Any], analysis: Dict[str, Any], project_payload: Optional[Dict[str, Any]], verification_payload: Dict[str, Any]) -> Dict[str, Any]:
        final_status = verification_payload.get("status", "BLOCKED_WITH_REPORT")
        report = {
            "generated_at": utc_now(),
            "status": final_status,
            "self_check": self_check_payload,
            "analysis": analysis,
            "project_generation": project_payload or {},
            "verification": verification_payload,
            "packet": packet.to_dict(),
        }
        write_json(self.orchestrator_state_path, report)
        lines = [
            "# LoopForge Final Report",
            "",
            f"- status: `{final_status}`",
            f"- generated_at: `{utc_now()}`",
            f"- source_root: `{self.source_root}`",
            "",
            "## READY Gates",
            "",
        ]
        for gate_name in ["cargo_build", "cargo_test", "unsafe", "semantic", "test_mapping", "repair_loop"]:
            gate = packet.gates.get(gate_name)
            if gate:
                lines.append(f"- `{gate_name}`: `{'pass' if gate.passed else 'fail'}`")
        lines.extend(
            [
                "",
                "## Issues",
                "",
                json.dumps(packet.issues, indent=2, ensure_ascii=True),
                "",
                "## Gate Events",
                "",
                self.gates_path.read_text(encoding="utf-8").rstrip(),
                "",
            ]
        )
        self.final_report_path.write_text("\n".join(lines), encoding="utf-8")
        self.record_gate_event("FINALIZE", True, final_status)
        return {"ok": True, "status": final_status, "report": str(self.final_report_path)}

    def write_entrypoint_result(self, packet: AgentTaskPacket, analysis: Dict[str, Any], verification_payload: Dict[str, Any], finalize_payload: Dict[str, Any]) -> Dict[str, Any]:
        gates = verification_payload.get("gates", {})
        output_lines = [
            "# Output",
            "",
            f"- status: `{finalize_payload['status']}`",
            f"- source_root: `{self.source_root}`",
            f"- selected_source_readme: `{analysis.get('readme_path') or 'missing'}`",
            f"- flashdb_root: `{analysis.get('flashdb_root') or 'missing'}`",
            f"- rust_project: `{self.project_dir}`",
            f"- cargo_build: `{gates.get('cargo_build', {}).get('passed', False)}`",
            f"- cargo_test: `{gates.get('cargo_test', {}).get('passed', False)}`",
            f"- unsafe_gate: `{gates.get('unsafe', {}).get('passed', False)}`",
            f"- semantic_gate: `{gates.get('semantic', {}).get('passed', False)}`",
            "",
            "## Summary",
            "",
            "- The execution orchestrator analyzed SOURCE_ROOT, generated or refreshed flashDB_rust, executed the repair loop, and evaluated semantic/test-mapping gates before declaring READY.",
            "",
        ]
        if packet.issues:
            output_lines.extend(["## Blocking Details", ""])
            output_lines.extend([f"- `{item['code']}`: {item['detail']}" for item in packet.issues])
            output_lines.append("")
        self.result_output_path.write_text("\n".join(output_lines), encoding="utf-8")

        issue_lines = [
            "# Issue Summary",
            "",
            f"- final_status: {finalize_payload['status']}",
            f"- source_root: {self.source_root}",
            f"- issue_count: {len(packet.issues)}",
            "",
        ]
        if packet.issues:
            issue_lines.extend([f"- {item['code']}: {item['detail']}" for item in packet.issues])
        else:
            issue_lines.append("- no_blocking_issues: all READY gates passed")
        issue_lines.append("")
        self.issue_summary_path.write_text("\n".join(issue_lines), encoding="utf-8")

        run_summary = {
            "generated_at": utc_now(),
            "source_root": str(self.source_root),
            "analysis": analysis,
            "verification": verification_payload,
            "finalize": finalize_payload,
            "packet": packet.to_dict(),
        }
        write_json(self.run_summary_path, run_summary)
        return run_summary

    def snapshot_packet(self, packet: AgentTaskPacket) -> None:
        write_json(self.packet_snapshot_path, packet.to_dict())
        self.record_gate_event("SNAPSHOT", True, "packet.json")

    def run_entrypoint(self) -> Dict[str, Any]:
        self.ensure_outputs()
        packet = self.create_packet()
        self_check_payload = self.self_check(packet)
        analysis = analyze_source(packet)
        self.write_source_inventory(analysis)
        self.record_gate_event("ANALYZE_SOURCE", analysis["ok"], f"support_level={analysis.get('support_level', 'unsupported')}")

        project_payload: Optional[Dict[str, Any]] = None
        if analysis["ok"]:
            project_payload = generate_project(packet, analysis)
            packet.metadata["project_generation"] = project_payload
            self.write_api_mapping(analysis, project_payload)
            self.write_migration_plan(analysis, project_payload)
            self.write_test_mapping(project_payload)
            self.write_migration_summary(analysis, project_payload)
            self.record_gate_event("GENERATE_PROJECT", True, project_payload.get("semantic_equivalence_claim", "generated"))
        else:
            self.write_api_mapping(analysis, None)
            self.write_migration_plan(analysis, None)
            self.write_test_mapping(None)
            self.write_migration_summary(analysis, None)
            self.record_gate_event("GENERATE_PROJECT", False, "source analysis failed")

        self.snapshot_packet(packet)

        if project_payload is not None:
            commands = self.normalize_commands()
            repair_payload = run_repair_loop(packet, commands, int(self.config.get("verification", {}).get("timeout_seconds", 600) or 600))
            self.record_gate_event("REPAIR_LOOP", repair_payload["ok"], f"rounds={repair_payload['rounds_executed']}")
            semantic_payload = evaluate_semantic_equivalence(packet, analysis, self.project_dir, project_payload, repair_payload)
            self.record_gate_event("SEMANTIC_GATE", semantic_payload["passed"], ",".join(semantic_payload.get("failing_checks", [])) or "passed")
            verification_payload = self.verify_generated(packet, project_payload, repair_payload, semantic_payload)
        else:
            repair_payload = {"ok": False, "build_ok": False, "test_ok": False, "rounds_executed": 0, "attempts": []}
            write_json(self.migration_trace_dir / "repair-rounds.json", repair_payload)
            (self.migration_trace_dir / "repair-rounds.md").write_text("# Repair Rounds\n\n- rounds_executed: `0`\n\n", encoding="utf-8")
            semantic_payload = {"passed": False, "checks": [], "failing_checks": ["project_generation"], "detail": "semantic gate requires generated project and test mapping"}
            packet.set_gate("cargo_build", False, "cargo build gate", {})
            packet.set_gate("cargo_test", False, "cargo test gate", {})
            packet.set_gate("unsafe", False, "unsafe gate", {"unsafe_ratio": 1.0})
            packet.set_gate("semantic", False, "semantic gate", semantic_payload)
            packet.set_gate("test_mapping", False, "test mapping gate", {})
            packet.set_gate("repair_loop", False, "repair loop gate", repair_payload)
            verification_payload = {
                "status": "BLOCKED_WITH_REPORT",
                "ready": False,
                "gates": {name: gate.to_dict() for name, gate in packet.gates.items()},
                "issues": packet.issues,
            }
            write_json(self.verify_path, verification_payload)
            self.verification_report_md.write_text(
                "# Verification Report\n\n- status: `BLOCKED_WITH_REPORT`\n\n## Issues\n\n"
                + json.dumps(packet.issues, indent=2, ensure_ascii=True)
                + "\n",
                encoding="utf-8",
            )

        finalize_payload = self.finalize(packet, self_check_payload, analysis, project_payload, verification_payload)
        run_summary = self.write_entrypoint_result(packet, analysis, verification_payload, finalize_payload)
        return {
            "ok": finalize_payload["status"] in {"READY_FOR_EVALUATION", "BLOCKED_WITH_REPORT"},
            "self_check": self_check_payload,
            "analysis": analysis,
            "project_generation": project_payload or {},
            "verification": verification_payload,
            "finalize": finalize_payload,
            "run_summary": run_summary,
        }

    def detect_project(self) -> Dict[str, Any]:
        self.ensure_outputs()
        packet = self.create_packet()
        self.self_check(packet)
        analysis = analyze_source(packet)
        self.write_source_inventory(analysis)
        self.write_api_mapping(analysis, None)
        self.write_migration_plan(analysis, None)
        self.write_test_mapping(None)
        self.write_migration_summary(analysis, None)
        payload = {"ok": analysis["ok"], "analysis": analysis, "packet": packet.to_dict(), "issues": list(packet.issues)}
        write_json(self.detect_path, payload)
        return payload

    def verify(self) -> Dict[str, Any]:
        return self.run_entrypoint()["verification"]

    def finalize_only(self) -> Dict[str, Any]:
        if self.orchestrator_state_path.exists():
            payload = json.loads(self.orchestrator_state_path.read_text(encoding="utf-8"))
            return {"ok": True, "status": payload.get("status", "BLOCKED_WITH_REPORT"), "report": str(self.final_report_path)}
        return {"ok": False, "status": "BLOCKED_WITH_REPORT", "report": str(self.final_report_path)}


def resolve_path(base: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = (base / path).resolve()
    return path.resolve()


def resolve_default_source_root(workspace_root: Path) -> Path:
    if os.name != "nt":
        for candidate in [
            Path("/__CONTEST_PLATFORM_SOURCE_ROOT__/source"),
            Path("/__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB"),
            Path("/__CONTEST_PLATFORM_SOURCE_ROOT__"),
        ]:
            if candidate.exists():
                return candidate.resolve()
    for candidate in [workspace_root / ".code" / "FlashDB", workspace_root / "code" / "FlashDB", workspace_root / "code"]:
        if candidate.exists():
            return candidate.resolve()
    return (workspace_root / ".code" / "FlashDB").resolve()


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LoopForge execution orchestrator")
    parser.add_argument("--work-dir", default="work")
    parser.add_argument("--source-root")
    parser.add_argument("--result-dir", default="result")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--snapshot")
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--detect", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--run", action="store_true")
    return parser.parse_args(argv)


def print_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True))


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    if not any([args.init, args.self_check, args.detect, args.verify, args.finalize, args.run]):
        print("No action provided.", file=sys.stderr)
        return 2

    cwd = Path.cwd().resolve()
    work_dir = resolve_path(cwd, args.work_dir)
    workspace_root = work_dir.parent
    source_arg = (args.source_root or os.environ.get("SOURCE_ROOT", "")).strip()
    source_root = resolve_path(workspace_root, source_arg) if source_arg else resolve_default_source_root(workspace_root)
    result_dir = resolve_path(cwd, args.result_dir)
    log_dir = resolve_path(cwd, args.log_dir)
    runner = LoopForgeRunner(workspace_root, work_dir, source_root, result_dir, log_dir)

    try:
        if args.init:
            runner.ensure_outputs()
            runner.write_templates()
            print_json({"ok": True, "status": "initialized", "source_root": str(source_root)})
        if args.self_check:
            packet = runner.create_packet()
            runner.ensure_outputs()
            print_json(runner.self_check(packet))
        if args.detect:
            print_json(runner.detect_project())
        if args.verify:
            print_json(runner.verify())
        if args.finalize:
            print_json(runner.finalize_only())
        if args.run:
            print_json(runner.run_entrypoint())
    except Exception as exc:
        print_json({"ok": False, "error": str(exc)})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
