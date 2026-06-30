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
REQUIRED_RULE_FILES = [
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
        self.profile = parse_simple_yaml((self.work_dir / str(self.config.get("task", {}).get("profile", "")).replace("/", os.sep)).read_text(encoding="utf-8"))
        self.outputs = self.config.get("outputs", {})
        self.packet = AgentTaskPacket(
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
        self.result_output_path = self.result_dir / "output.md"
        self.issue_summary_path = self.result_dir / "issues" / "00-summary.md"
        self.interaction_log_path = self.log_dir / "interaction.md"
        self.run_summary_path = self.trace_dir / "run-summary.json"
        self.final_report_path = self.trace_dir / "final-report.md"
        self.source_inventory_path = self.migration_trace_dir / "01-source-inventory.md"
        self.api_mapping_path = self.migration_trace_dir / "02-api-mapping.md"
        self.migration_plan_path = self.migration_trace_dir / "03-migration-plan.md"
        self.test_mapping_path = self.migration_trace_dir / "04-test-mapping.md"
        self.migration_summary_path = self.migration_trace_dir / "05-migration-summary.md"
        self.verification_report_path = self.migration_trace_dir / "06-verification-report.md"
        self.unsafe_ratio_path = self.migration_trace_dir / "unsafe-ratio.json"
        self.state_dir = self.artifact_dir / "state"
        self.gates_path = self.artifact_dir / "gate-events.md"
        self.mode_artifacts_path = self.artifact_dir / "mode-artifacts.md"
        self.orchestrator_state_path = self.state_dir / "orchestrator-state.json"
        self.self_check_path = self.state_dir / "self-check.json"
        self.detect_path = self.state_dir / "detect-summary.json"
        self.verify_path = self.state_dir / "verification-summary.json"
        self.gate_events: List[Dict[str, str]] = []

    def ensure_outputs(self) -> None:
        self.result_dir.mkdir(parents=True, exist_ok=True)
        (self.result_dir / "issues").mkdir(parents=True, exist_ok=True)
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.migration_trace_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)
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
                    "- `01-source-inventory.md`",
                    "- `02-api-mapping.md`",
                    "- `03-migration-plan.md`",
                    "- `04-test-mapping.md`",
                    "- `05-migration-summary.md`",
                    "- `06-verification-report.md`",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def save_json(self, path: Path, payload: Dict[str, Any]) -> None:
        ensure_parent(path)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    def record_gate_event(self, name: str, passed: bool, detail: str) -> None:
        self.gate_events.append({"gate": name, "status": "PASS" if passed else "FAIL", "detail": detail})
        lines = [
            "| Gate | Status | Detail |",
            "|---|---|---|",
        ]
        lines.extend(f"| {item['gate']} | {item['status']} | {item['detail']} |" for item in self.gate_events)
        self.gates_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def resolve_path_token(self, value: str) -> Path:
        if value == "SOURCE_ROOT":
            return self.source_root
        if value.startswith("SOURCE_ROOT/"):
            return (self.source_root / value[len("SOURCE_ROOT/") :]).resolve()
        path = Path(value)
        if not path.is_absolute():
            path = (self.workspace_root / path).resolve()
        return path.resolve()

    def normalize_commands(self) -> List[str]:
        commands = self.config.get("verification", {}).get("commands", [])
        if isinstance(commands, dict):
            default_commands = commands.get("default", [])
            if isinstance(default_commands, list):
                return [str(item) for item in default_commands]
        if isinstance(commands, list):
            return [str(item) for item in commands]
        return []

    def summarize_issues(self) -> str:
        if not self.packet.issues:
            return "none"
        return "; ".join(f"{item['code']}: {item['detail']}" for item in self.packet.issues)

    def self_check(self) -> Dict[str, Any]:
        self.ensure_outputs()
        required_files = REQUIRED_RUNTIME_FILES + REQUIRED_RULE_FILES + REQUIRED_MISC_FILES
        missing = [path for path in required_files if not (self.workspace_root / path).exists()]
        work_code_readme = self.workspace_root / "work" / "code" / "README.md"
        is_real_source = path_is_relative_to(work_code_readme.resolve(), self.source_root) if work_code_readme.exists() else False
        if is_real_source:
            self.packet.add_issue("invalid_source_root", "work/code/README.md is a contest requirement description, not a FlashDB source root")
        if missing:
            for item in missing:
                self.packet.add_issue("required_asset_missing", item)

        summary = {
            "ok": not missing and not is_real_source,
            "required_files_checked": required_files,
            "missing_files": missing,
            "source_root": str(self.source_root),
            "local_fallback_source_dir": str(self.config.get("platform", {}).get("local_fallback_source_dir", "")),
            "artifact_dir": str(self.artifact_dir),
            "work_code_readme_is_source_root": is_real_source,
            "issues": self.packet.issues,
        }
        self.save_json(self.self_check_path, summary)
        self.record_gate_event("SELF_CHECK", summary["ok"], "static runtime assets and source-root boundary validated")
        return summary

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
        self.source_inventory_path.write_text("\n".join(lines), encoding="utf-8")

    def write_api_mapping(self, analysis: Dict[str, Any], project_payload: Optional[Dict[str, Any]]) -> None:
        mapped_apis = project_payload.get("mapped_apis", []) if project_payload else []
        lines = [
            "# API Mapping",
            "",
            f"- support_level: `{analysis.get('support_level', 'unsupported')}`",
            "",
            "## C API To Rust Mapping",
            "",
        ]
        if mapped_apis:
            for api in mapped_apis:
                lines.append(f"- `{api}` -> `flashdb_rust::{api}` or `FlashDb` method")
        else:
            lines.append("- No Rust API mapping was generated.")
        lines.extend(
            [
                "",
                "## Strategy",
                "",
                "- Data model: in-memory ordered key/value store.",
                "- Error handling: `Option` and total functions for the fallback template.",
                "- Ownership: owned `String` keys and `Vec<u8>` values with borrowed reads.",
                "- Unsafe: `#![forbid(unsafe_code)]` in generated modules.",
                "",
            ]
        )
        self.api_mapping_path.write_text("\n".join(lines), encoding="utf-8")

    def write_migration_plan(self, analysis: Dict[str, Any], project_payload: Optional[Dict[str, Any]]) -> None:
        module_list = project_payload.get("module_list", []) if project_payload else []
        lines = [
            "# Migration Plan",
            "",
            f"- support_level: `{analysis.get('support_level', 'unsupported')}`",
            "",
            "## Crate Layout",
            "",
            "- `flashDB_rust/Cargo.toml`",
            "- `flashDB_rust/src/lib.rs`",
        ]
        lines.extend([f"- `flashDB_rust/{item}`" for item in module_list if item != "src/lib.rs"])
        lines.extend(["", "## Test Migration List", ""])
        lines.extend([f"- `{item}`" for item in analysis.get("test_files", [])] or ["- none"])
        lines.extend(["", "## Unsupported Or Degraded Behaviors", ""])
        if analysis.get("support_level") == "unsupported":
            lines.append("- The current source layout is not covered by the fallback generator template.")
        else:
            lines.append("- No degraded behavior is declared for the local fallback template.")
        lines.append("")
        self.migration_plan_path.write_text("\n".join(lines), encoding="utf-8")

    def write_test_mapping(self, project_payload: Optional[Dict[str, Any]]) -> None:
        lines = ["# Test Mapping", "", "## Scenario Mapping", ""]
        mapping = project_payload.get("test_mapping", []) if project_payload else []
        if mapping:
            for item in mapping:
                lines.append(f"- `{item['source_test']}` -> `{item['rust_test_file']}` ({item['mapping']})")
        else:
            lines.append("- none")
        lines.append("")
        self.test_mapping_path.write_text("\n".join(lines), encoding="utf-8")

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
        self.migration_summary_path.write_text("\n".join(lines), encoding="utf-8")

    def detect_project(self) -> Dict[str, Any]:
        self.ensure_outputs()
        analysis = analyze_source(self.packet)
        self.write_source_inventory(analysis)
        self.write_api_mapping(analysis, None)
        self.write_migration_plan(analysis, None)
        self.write_test_mapping(None)
        self.write_migration_summary(analysis, None)
        summary = {
            "ok": analysis["ok"],
            "source_layout": self.packet.source_layout.to_dict() if self.packet.source_layout else {},
            "analysis": analysis,
            "issues": self.packet.issues,
        }
        self.save_json(self.detect_path, summary)
        self.record_gate_event("DETECT", analysis["ok"], f"support_level={analysis.get('support_level', 'unsupported')}")
        return summary

    def check_unsafe_ratio(self) -> Dict[str, Any]:
        total_lines = 0
        unsafe_lines = 0
        files: List[Dict[str, Any]] = []
        for path in self.project_dir.rglob("*.rs"):
            if "target" in path.parts:
                continue
            code_lines = 0
            file_unsafe = 0
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("//"):
                    continue
                code_lines += 1
                if "unsafe" in stripped:
                    file_unsafe += 1
            total_lines += code_lines
            unsafe_lines += file_unsafe
            files.append({"file": str(path), "code_lines": code_lines, "unsafe_lines": file_unsafe})
        ratio = (unsafe_lines / total_lines) if total_lines else 0.0
        payload = {
            "project": str(self.project_dir),
            "total_code_lines": total_lines,
            "unsafe_lines": unsafe_lines,
            "unsafe_ratio": ratio,
            "max_ratio": 0.10,
            "passed": ratio < 0.10,
            "files": files,
            "generated_at": utc_now(),
        }
        self.unsafe_ratio_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        return payload

    def verify(self) -> Dict[str, Any]:
        self.ensure_outputs()
        analysis = analyze_source(self.packet)
        project_payload: Optional[Dict[str, Any]] = None
        if analysis["ok"] and analysis.get("support_level") != "unsupported":
            project_payload = generate_project(self.packet, analysis)
            self.write_api_mapping(analysis, project_payload)
            self.write_migration_plan(analysis, project_payload)
            self.write_test_mapping(project_payload)
            self.write_migration_summary(analysis, project_payload)
            self.packet.set_gate("project_generation", True, "generated Rust project from supported fallback template", project_payload)
            self.record_gate_event("PROJECT_GENERATION", True, "generated flashDB_rust")
        else:
            self.packet.set_gate("project_generation", False, "project generation skipped because source analysis is incomplete", {"analysis_ok": analysis["ok"], "support_level": analysis.get("support_level", "unsupported")})
            self.record_gate_event("PROJECT_GENERATION", False, "analysis did not satisfy generator preconditions")

        commands = self.normalize_commands()
        verification = {
            "analysis": analysis,
            "commands": commands,
            "project_generation": self.packet.gates["project_generation"].to_dict(),
        }

        if self.packet.gates["project_generation"].passed and commands:
            repair_payload = run_repair_loop(
                self.packet,
                commands=commands,
                timeout_seconds=int(self.config.get("verification", {}).get("timeout_seconds", 600) or 600),
            )
            verification["repair_loop"] = repair_payload
            self.packet.set_gate("cargo_build", repair_payload["build_ok"], "cargo build gate", {"rounds_executed": repair_payload["rounds_executed"]})
            self.packet.set_gate("cargo_test", repair_payload["test_ok"], "cargo test gate", {"rounds_executed": repair_payload["rounds_executed"]})
            self.record_gate_event("CARGO_BUILD", repair_payload["build_ok"], "cargo build completed")
            self.record_gate_event("CARGO_TEST", repair_payload["test_ok"], "cargo test completed")
        else:
            self.packet.set_gate("cargo_build", False, "cargo build gate skipped", {"commands": commands})
            self.packet.set_gate("cargo_test", False, "cargo test gate skipped", {"commands": commands})
            verification["repair_loop"] = {"ok": False, "attempts": []}
            self.record_gate_event("CARGO_BUILD", False, "verification commands unavailable or project not generated")
            self.record_gate_event("CARGO_TEST", False, "verification commands unavailable or project not generated")

        unsafe_payload = self.check_unsafe_ratio() if self.packet.gates["cargo_build"].passed and self.packet.gates["cargo_test"].passed else {
            "project": str(self.project_dir),
            "total_code_lines": 0,
            "unsafe_lines": 0,
            "unsafe_ratio": 1.0,
            "max_ratio": 0.10,
            "passed": False,
            "files": [],
            "generated_at": utc_now(),
        }
        if unsafe_payload["passed"]:
            self.packet.set_gate("unsafe", True, "unsafe gate passed", unsafe_payload)
        else:
            self.packet.add_issue("unsafe_gate_failed", f"unsafe_ratio={unsafe_payload['unsafe_ratio']:.4f}")
            self.packet.set_gate("unsafe", False, "unsafe gate failed", unsafe_payload)
        self.record_gate_event("UNSAFE", unsafe_payload["passed"], f"ratio={unsafe_payload['unsafe_ratio']:.4f}")

        semantic_payload = evaluate_semantic_equivalence(self.packet, analysis, self.project_dir) if self.packet.gates["project_generation"].passed else {
            "passed": False,
            "checks": [],
            "failing_checks": ["project_generation"],
        }
        self.packet.set_gate("semantic", semantic_payload["passed"], "semantic equivalence gate", semantic_payload)
        self.record_gate_event("SEMANTIC", semantic_payload["passed"], ",".join(semantic_payload.get("failing_checks", [])) or "passed")

        ready = self.packet.ready()
        status = "READY_FOR_EVALUATION" if ready else "BLOCKED_WITH_REPORT"
        verification.update(
            {
                "status": status,
                "ready": ready,
                "gates": {name: gate.to_dict() for name, gate in self.packet.gates.items()},
                "issues": self.packet.issues,
            }
        )
        self.save_json(self.verify_path, verification)
        self.verification_report_path.write_text(
            "\n".join(
                [
                    "# Verification Report",
                    "",
                    f"- status: `{status}`",
                    "",
                    "## Gates",
                    "",
                    json.dumps(verification["gates"], indent=2, ensure_ascii=True),
                    "",
                    "## Issues",
                    "",
                    json.dumps(self.packet.issues, indent=2, ensure_ascii=True),
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return verification

    def finalize(self, detect_payload: Optional[Dict[str, Any]] = None, verify_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.ensure_outputs()
        if detect_payload is None:
            if self.detect_path.exists():
                detect_payload = json.loads(self.detect_path.read_text(encoding="utf-8"))
            else:
                detect_payload = self.detect_project()
        if verify_payload is None:
            if self.verify_path.exists():
                verify_payload = json.loads(self.verify_path.read_text(encoding="utf-8"))
            else:
                verify_payload = self.verify()
        ready = verify_payload.get("ready", False)
        final_status = "READY_FOR_EVALUATION" if ready else "BLOCKED_WITH_REPORT"
        final_report = {
            "generated_at": utc_now(),
            "status": final_status,
            "paths": self.packet.paths.to_dict(),
            "source_layout": self.packet.source_layout.to_dict() if self.packet.source_layout else {},
            "detect": detect_payload,
            "verify": verify_payload,
            "issues": self.packet.issues,
            "warnings": self.packet.warnings,
        }
        self.save_json(self.orchestrator_state_path, final_report)
        lines = [
            "# LoopForge Final Report",
            "",
            f"- status: `{final_status}`",
            f"- generated_at: `{utc_now()}`",
            f"- source_root: `{self.source_root}`",
            f"- fallback_source_root: `{self.config.get('platform', {}).get('local_fallback_source_dir', '')}`",
            "",
            "## READY Gates",
            "",
        ]
        for gate_name in ["cargo_build", "cargo_test", "unsafe", "semantic"]:
            gate = self.packet.gates.get(gate_name)
            if gate:
                lines.append(f"- `{gate_name}`: `{'pass' if gate.passed else 'fail'}`")
        lines.extend(
            [
                "",
                "## Issues",
                "",
                json.dumps(self.packet.issues, indent=2, ensure_ascii=True),
                "",
                "## Detection",
                "",
                json.dumps(detect_payload, indent=2, ensure_ascii=True),
                "",
                "## Verification",
                "",
                json.dumps(verify_payload, indent=2, ensure_ascii=True),
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

    def write_entrypoint_result(self, detect_payload: Dict[str, Any], verify_payload: Dict[str, Any], finalize_payload: Dict[str, Any]) -> Dict[str, Any]:
        gates = verify_payload.get("gates", {})
        output_lines = [
            "# Output",
            "",
            f"- status: `{finalize_payload['status']}`",
            f"- source_root: `{self.source_root}`",
            f"- selected_source_readme: `{detect_payload.get('analysis', {}).get('readme_path') or 'missing'}`",
            f"- flashdb_root: `{detect_payload.get('analysis', {}).get('flashdb_root') or 'missing'}`",
            f"- rust_project: `{self.project_dir}`",
            f"- cargo_build: `{gates.get('cargo_build', {}).get('passed', False)}`",
            f"- cargo_test: `{gates.get('cargo_test', {}).get('passed', False)}`",
            f"- unsafe_gate: `{gates.get('unsafe', {}).get('passed', False)}`",
            f"- semantic_gate: `{gates.get('semantic', {}).get('passed', False)}`",
            "",
            "## Summary",
            "",
            "- The execution orchestrator analyzed SOURCE_ROOT, generated a Rust project when the source matched the supported FlashDB fallback template, and evaluated READY gates.",
            "",
        ]
        if self.packet.issues:
            output_lines.extend(["## Blocking Details", ""])
            output_lines.extend([f"- `{item['code']}`: {item['detail']}" for item in self.packet.issues])
            output_lines.append("")
        self.result_output_path.write_text("\n".join(output_lines), encoding="utf-8")

        issue_lines = [
            "# Issue Summary",
            "",
            f"- final_status: {finalize_payload['status']}",
            f"- source_root: {self.source_root}",
            f"- issue_count: {len(self.packet.issues)}",
            "",
        ]
        if self.packet.issues:
            issue_lines.extend([f"- {item['code']}: {item['detail']}" for item in self.packet.issues])
        else:
            issue_lines.append("- no_blocking_issues: all READY gates passed")
        issue_lines.append("")
        self.issue_summary_path.write_text("\n".join(issue_lines), encoding="utf-8")

        run_summary = {
            "generated_at": utc_now(),
            "source_root": str(self.source_root),
            "artifact_dir": str(self.artifact_dir),
            "detect": detect_payload,
            "verify": verify_payload,
            "finalize": finalize_payload,
            "issues": self.packet.issues,
        }
        self.save_json(self.run_summary_path, run_summary)
        return run_summary

    def snapshot(self, name: str) -> Dict[str, Any]:
        self.ensure_outputs()
        snapshot_name = name if name.endswith(".json") else f"{name}.json"
        snapshot_path = self.artifact_dir / snapshot_name
        self.save_json(snapshot_path, self.packet.to_dict())
        self.record_gate_event("SNAPSHOT", True, snapshot_name)
        return {"ok": True, "snapshot": str(snapshot_path)}

    def run_entrypoint(self) -> Dict[str, Any]:
        self.ensure_outputs()
        self_check_payload = self.self_check()
        detect_payload = self.detect_project()
        self.snapshot("before-verify")
        verify_payload = self.verify()
        finalize_payload = self.finalize(detect_payload, verify_payload)
        self.write_entrypoint_result(detect_payload, verify_payload, finalize_payload)
        return {
            "ok": finalize_payload["status"] in {"READY_FOR_EVALUATION", "BLOCKED_WITH_REPORT"},
            "self_check": self_check_payload,
            "detect": detect_payload,
            "verify": verify_payload,
            "finalize": finalize_payload,
        }


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
    fallback = workspace_root / ".code" / "FlashDB"
    if fallback.exists():
        return fallback.resolve()
    return (workspace_root / "code").resolve()


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
    if not any([args.init, args.self_check, args.detect, args.verify, args.finalize, args.run, bool(args.snapshot)]):
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
            print_json({"ok": True, "status": "initialized", "source_root": str(source_root), "artifact_dir": str(runner.artifact_dir)})
        if args.self_check:
            print_json(runner.self_check())
        if args.detect:
            print_json(runner.detect_project())
        if args.snapshot:
            print_json(runner.snapshot(args.snapshot))
        if args.verify:
            print_json(runner.verify())
        if args.finalize:
            print_json(runner.finalize())
        if args.run:
            print_json(runner.run_entrypoint())
    except Exception as exc:
        print_json({"ok": False, "error": str(exc)})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
