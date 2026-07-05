#!/usr/bin/env python3
"""LoopForge execution orchestrator — thin data-preparation layer.

Responsibilities:
  - Resolve SOURCE_ROOT, validate environment, self-check
  - Run tools.py parse-source (structured data, no judgment)
  - Run semantic_planning (deterministic migration plan)
  - Write context package for Agent consumption
  - Output instructions for Agent to execute SKILL.md

All judgment phases (understanding, design, code generation, testing,
repair, semantic audit, gating) are delegated to the Agent via
work/skills/c-to-rust-migration-v2/SKILL.md.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agent_task_packet import AgentTaskPacket, RuntimePaths, resolve_runtime_contract
from c_project_root_resolver import resolve_c_project_root, write_resolution_trace
from semantic_planning import PlanningBlocked, plan_from_trace
from source_analysis import build_complete_analysis, write_complete_analysis
from source_analysis_verify_gate import build_and_verify_source_analysis


ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
TRACE_NAMESPACE = "c-to-rust"
REQUIRED_RUNTIME_FILES = [
    "work/runtime/loopforge_runner.py",
    "work/runtime/agent_task_packet.py",
    "work/runtime/c_project_root_resolver.py",
    "work/runtime/source_analysis_verify_gate.py",
    "work/runtime/source_analysis.py",
    "work/runtime/semantic_planning.py",
    "work/runtime/semantic-planning.json",
    "work/runtime/rust_project_generation.py",
    "work/runtime/rust-project-generation.json",
    "work/runtime/test_migration_validation.py",
    "work/runtime/timeout_policy.py",
    "work/runtime/self_healing_loop.py",
    "work/runtime/tools.py",
    "work/runtime/check_unsafe_ratio.py",
    "work/vendor/pycparser/__init__.py",
    "work/vendor/PYCPARSER-LICENSE",
]
REQUIRED_ADAPTER_FILES = [
    "work/rules/loopforge/adapters/c-to-rust/source-contract.md",
    "work/rules/loopforge/adapters/c-to-rust/output-contract.md",
    "work/rules/loopforge/adapters/c-to-rust/test-migration-contract.md",
    "work/rules/loopforge/adapters/c-to-rust/unsafe-contract.md",
    "work/rules/loopforge/adapters/c-to-rust/verification-contract.md",
    "work/rules/loopforge/adapters/c-to-rust/semantic-equivalence-contract.md",
    "work/rules/loopforge/adapters/c-to-rust/repair-loop-contract.md",
]
REQUIRED_MISC_FILES = [
    "INSTRUCTION.md",
    "README.md",
    "work/design/README.md",
    "work/loopforge.config.yaml",
    "work/profiles/examples/c-to-rust-migration.yaml",
    "work/skills/c-to-rust-migration-v2/SKILL.md",
]
REQUIRED_SUBAGENT_FILES = [
    "work/subagent/c2r-00-preflight.md",
    "work/subagent/c2r-01-understand.md",
    "work/subagent/c2r-02-design.md",
    "work/subagent/c2r-03-spec.md",
    "work/subagent/c2r-04-plan.md",
    "work/subagent/c2r-05-implement.md",
    "work/subagent/c2r-06-test.md",
    "work/subagent/c2r-07-repair.md",
    "work/subagent/c2r-08-semantic-audit.md",
    "work/subagent/c2r-09-quality-gates.md",
    "work/subagent/c2r-10-finalize.md",
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
    try:
        return float(value)
    except ValueError:
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


def sanitize_dirname(value: str, fallback: str = "c_to_rust_output") -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value).strip("_-")
    return cleaned or fallback


def sanitize_text(text: str, workspace_root: Path) -> str:
    normalized_text = text.replace("\\", "/")
    roots = {str(workspace_root), str(workspace_root).replace("\\", "/")}
    for root in roots:
        normalized_text = normalized_text.replace(root, ".")
        normalized_text = re.sub(re.escape(root), ".", normalized_text, flags=re.IGNORECASE)
    return normalized_text


def sanitize_payload(value: Any, workspace_root: Path) -> Any:
    if isinstance(value, Path):
        try:
            return str(value.resolve().relative_to(workspace_root)).replace("\\", "/")
        except ValueError:
            return value.name
    if isinstance(value, dict):
        return {key: sanitize_payload(item, workspace_root) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_payload(item, workspace_root) for item in value]
    if isinstance(value, str):
        return sanitize_text(value, workspace_root)
    return value


class LoopForgeRunner:
    def __init__(self, workspace_root: Path, work_dir: Path, source_root: Path, result_dir: Path, log_dir: Path) -> None:
        self.workspace_root = workspace_root.resolve()
        self.work_dir = work_dir.resolve()
        self.input_root = source_root.resolve()
        self.result_dir = result_dir.resolve()
        self.log_dir = log_dir.resolve()
        self.trace_dir = self.log_dir / "trace"
        self.artifact_dir = self.trace_dir / "execution-adapter"
        self.migration_trace_dir = self.trace_dir / TRACE_NAMESPACE
        for writable_root in (self.result_dir, self.log_dir, self.work_dir / "output"):
            if path_is_relative_to(writable_root, self.input_root):
                raise ValueError(f"writable destination must be outside SOURCE_ROOT: {writable_root}")
        self.layout_resolution = resolve_c_project_root(self.input_root)
        write_resolution_trace(self.layout_resolution, self.migration_trace_dir)
        resolved = self.layout_resolution.get("resolved_project_root", "")
        self.source_root = Path(resolved).resolve() if resolved else self.input_root
        self.config = parse_simple_yaml((self.work_dir / "loopforge.config.yaml").read_text(encoding="utf-8"))
        profile_rel = str(self.config.get("task", {}).get("profile", "")).replace("/", os.sep)
        self.profile = parse_simple_yaml((self.work_dir / profile_rel).read_text(encoding="utf-8"))
        self.runtime_contract = resolve_runtime_contract(self.work_dir / "design" / "README.md", self.profile)
        self.output_base_dir = Path(os.environ.get("LOOPFORGE_OUTPUT_DIR", str(self.work_dir / "output"))).resolve()
        if path_is_relative_to(self.output_base_dir, self.input_root):
            raise ValueError(f"writable destination must be outside SOURCE_ROOT: {self.output_base_dir}")
        self.project_dir = self.output_base_dir / sanitize_dirname(self.runtime_contract["output_project_name"])
        self.result_output_path = self.result_dir / "output.md"
        self.issue_summary_path = self.result_dir / "issues" / "00-summary.md"
        self.interaction_log_path = self.log_dir / "interaction.md"
        self.run_summary_path = self.trace_dir / "run-summary.json"
        self.final_report_path = self.trace_dir / "final-report.md"
        self.self_check_path = self.artifact_dir / "state" / "self-check.json"
        self.context_pkg_path = self.artifact_dir / "state" / "context-package.json"
        self.source_inventory_json = self.migration_trace_dir / "source-inventory.json"

    def display_path(self, path: Path | str) -> str:
        if isinstance(path, str):
            if path in {"", "missing", "NOT_RUN"}:
                return path
            candidate = Path(path)
        else:
            candidate = path
        try:
            return str(candidate.resolve().relative_to(self.workspace_root)).replace("\\", "/")
        except ValueError:
            return str(candidate).replace("\\", "/")

    def write_json(self, path: Path, payload: Dict[str, Any]) -> None:
        write_json(path, sanitize_payload(payload, self.workspace_root))

    def create_agent_task_packet(self) -> AgentTaskPacket:
        packet = AgentTaskPacket(
            paths=RuntimePaths(
                workspace_root=self.workspace_root,
                work_dir=self.work_dir,
                input_root=self.input_root,
                source_root=self.source_root,
                result_dir=self.result_dir,
                log_dir=self.log_dir,
                trace_dir=self.trace_dir,
                artifact_dir=self.artifact_dir,
                migration_trace_dir=self.migration_trace_dir,
                output_base_dir=self.output_base_dir,
                project_dir=self.project_dir,
            ),
            config=self.config,
            profile=self.profile,
            design_readme_path=Path(self.runtime_contract["design_readme_path"]),
            design_readme_sha256=str(self.runtime_contract["design_readme_sha256"]),
            max_repair_rounds=int(self.config.get("execution", {}).get("max_repair_rounds", 2) or 2),
            source_project_name=str(self.runtime_contract["source_project_name"]),
            source_language=str(self.runtime_contract["source_language"]),
            target_language=str(self.runtime_contract["target_language"]),
            output_project_name=str(self.runtime_contract["output_project_name"]),
            output_project_dir=self.project_dir,
            source_dirs=[str(item) for item in self.runtime_contract["source_dirs"]],
            test_dirs=[str(item) for item in self.runtime_contract["test_dirs"]],
            build_commands=[str(item) for item in self.runtime_contract["build_commands"]],
            unsafe_ratio_max=float(self.runtime_contract["unsafe_ratio_max"]),
            api_name_hints=[str(item) for item in self.runtime_contract["api_name_hints"]],
            module_hints=[str(item) for item in self.runtime_contract["module_hints"]],
        )
        packet.metadata["source_root_resolution"] = str(self.source_root)
        packet.metadata["input_root"] = str(self.input_root)
        packet.metadata["layout_resolution"] = self.layout_resolution
        packet.metadata["design_readme_path"] = self.runtime_contract["design_readme_path"]
        packet.metadata["design_readme_sha256"] = self.runtime_contract["design_readme_sha256"]
        packet.metadata["design_readme_error"] = self.runtime_contract["design_readme_error"]
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

    def self_check(self, packet: AgentTaskPacket) -> Dict[str, Any]:
        required_files = REQUIRED_RUNTIME_FILES + REQUIRED_ADAPTER_FILES + REQUIRED_MISC_FILES + REQUIRED_SUBAGENT_FILES
        missing = [path for path in required_files if not (self.workspace_root / path).exists()]
        invalid_source = self.layout_resolution["status"] != "RESOLVED"
        design_error = str(packet.metadata.get("design_readme_error", ""))
        if invalid_source:
            detail = self.layout_resolution["reason"]
            candidates = self.layout_resolution.get("candidate_roots", [])
            if detail == "ambiguous project roots":
                detail += ": " + ", ".join(f"{item['root']} (score={item['score']})" for item in candidates if item["usable"])
            packet.add_issue("source_layout_missing", detail)
        for item in missing:
            packet.add_issue("required_asset_missing", item)
        if design_error:
            packet.add_issue(design_error, f"invalid preloaded design contract: {packet.design_readme_path}")
        payload = {
            "ok": not missing and not invalid_source and not design_error,
            "required_files_checked": required_files,
            "missing_files": missing,
            "input_root": str(self.input_root),
            "source_root": str(self.source_root),
            "design_readme_path": packet.metadata.get("design_readme_path", ""),
            "design_readme_sha256": packet.metadata.get("design_readme_sha256", ""),
            "design_readme_error": design_error,
            "invalid_source_root": invalid_source,
            "layout_resolution": self.layout_resolution,
            "issues": list(packet.issues),
        }
        self.write_json(self.self_check_path, payload)
        return payload

    def _run_source_analysis(self, packet: AgentTaskPacket) -> Dict[str, Any]:
        """Run deterministic C source analysis via source_analysis.py (pycparser + regex).
        No body_kind classification. No translation judgment. Pure data."""
        legacy = {
            "project_root": str(self.source_root),
            "public_apis": [],
            "functions": [],
            "test_files": [],
        }
        bundle = build_complete_analysis(packet, legacy)
        write_complete_analysis(bundle, self.migration_trace_dir)
        artifacts = bundle.get("artifacts", {})
        inventory = artifacts.get("source-inventory.json", {})
        public_api = artifacts.get("public-api-map.json", {})
        call_graph = artifacts.get("call-graph.json", {})
        type_map = artifacts.get("type-map.json", {})
        globals_map = artifacts.get("global-state-map.json", {})
        verification = artifacts.get("analysis-verification.json", {})
        return {
            "ok": verification.get("passed", False),
            "run_id": bundle["metadata"]["run_id"],
            "project_root": str(self.source_root),
            "source_files": inventory.get("files", []),
            "source_tests": inventory.get("source_tests", []),
            "test_functions": inventory.get("test_functions", []),
            "public_apis": [api["name"] for api in public_api.get("apis", [])],
            "functions": call_graph.get("functions", []),
            "types": type_map.get("types", []),
            "call_graph": call_graph.get("call_edges", []),
            "globals": globals_map.get("globals", []),
            "parse_failures": verification.get("parse_failures", []),
            "design_readme_path": str(packet.design_readme_path),
            "design_readme_sha256": packet.design_readme_sha256,
            "support_level": "supported" if verification.get("passed") else "blocked",
            "verification": verification,
            "source_dirs": [str(d) for d in self.layout_resolution.get("source_dirs", [])],
            "test_dirs": [str(d) for d in self.layout_resolution.get("test_dirs", [])],
            "src_files": [item["path"] for item in inventory.get("files", [])],
            "test_files": [item["path"] for item in inventory.get("source_tests", [])],
            "tests": inventory.get("source_tests", []),
            "module_hints": list({item["path"].split("/")[0] for item in inventory.get("files", []) if "/" in item["path"]}),
            "type_table": type_map.get("types", []),
            "macro_table": artifacts.get("preprocessor-variants.json", {}).get("macros", []),
        }

    def _build_context_package(self, packet: AgentTaskPacket, analysis: Dict[str, Any], source_gate: Dict[str, Any], semantic_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Build the context package for Agent consumption.

        All paths are absolute. The Agent reads this JSON and executes SKILL.md."""
        return {
            "generated_at": utc_now(),
            "SOURCE_ROOT": str(self.source_root),
            "WORK_DIR": str(self.work_dir),
            "OUTPUT_DIR": str(packet.output_project_dir),
            "RESULT_DIR": str(self.result_dir),
            "LOG_DIR": str(self.log_dir),
            "OPENSPEC_CHANGE": "c-to-rust-migration",
            "SOURCE_PROJECT_NAME": packet.source_project_name,
            "OUTPUT_PROJECT_NAME": packet.output_project_name,
            "DESIGN_README_PATH": str(packet.design_readme_path),
            "DESIGN_README_SHA256": packet.design_readme_sha256,
            "MAX_REPAIR_ROUNDS": packet.max_repair_rounds,
            "UNSAFE_RATIO_MAX": packet.unsafe_ratio_max,
            "PRIOR_OUTPUTS": {
                "source_inventory": str(self.migration_trace_dir / "source-inventory.json"),
                "public_api_map": str(self.migration_trace_dir / "public-api-map.json"),
                "call_graph": str(self.migration_trace_dir / "call-graph.json"),
                "type_map": str(self.migration_trace_dir / "type-map.json"),
                "global_state_map": str(self.migration_trace_dir / "global-state-map.json"),
                "analysis_verification": str(self.migration_trace_dir / "analysis-verification.json"),
                "source_analysis_verify_report": str(self.migration_trace_dir / "source-analysis-verify-report.md"),
                "migration_trace_dir": str(self.migration_trace_dir),
                "semantic_planning_dir": str(self.migration_trace_dir),
            },
            "ANALYSIS_SUMMARY": {
                "source_file_count": len(analysis.get("source_files", [])),
                "public_api_count": len(analysis.get("public_apis", [])),
                "test_function_count": len(analysis.get("test_functions", [])),
                "type_count": len(analysis.get("types", [])),
                "call_edge_count": len(analysis.get("call_graph", [])),
                "parse_failures": analysis.get("parse_failures", []),
            },
            "SKILL_PATH": str(self.work_dir / "skills" / "c-to-rust-migration-v2" / "SKILL.md"),
            "SUBAGENT_DIR": str(self.work_dir / "subagent"),
            "TOOLS_PY_PATH": str(self.work_dir / "runtime" / "tools.py"),
            "SUPERPOWER_GUARDS_PATH": str(self.work_dir / "profiles" / "superpower" / "c-to-rust-migration-guards.yaml"),
        }

    def _write_agent_delegation_report(self, packet: AgentTaskPacket, analysis: Dict[str, Any], context_pkg: Dict[str, Any]) -> Dict[str, Any]:
        """Write the result/output.md instructing the operator to run the Agent with SKILL.md."""
        public_apis = analysis.get("public_apis", [])
        source_files = analysis.get("source_files", [])
        test_functions = analysis.get("test_functions", [])

        output_lines = [
            "# Output",
            "",
            "- status: `AGENT_DELEGATION_READY`",
            f"- generated_at: `{utc_now()}`",
            f"- input_root: `{self.display_path(self.input_root)}`",
            f"- source_root: `{self.display_path(self.source_root)}`",
            f"- design_readme: `{self.display_path(analysis.get('design_readme_path') or 'missing')}`",
            f"- design_readme_sha256: `{analysis.get('design_readme_sha256') or 'missing'}`",
            f"- rust_project: `{self.display_path(packet.output_project_dir)}`",
            f"- source_file_count: `{len(source_files)}`",
            f"- public_api_count: `{len(public_apis)}`",
            f"- test_function_count: `{len(test_functions)}`",
            "",
            "## Data Preparation Complete",
            "",
            "Source analysis and semantic planning are complete. All code generation, testing, repair, and auditing phases are delegated to the Agent.",
            "",
            f"### Context Package: `{self.display_path(self.context_pkg_path)}`",
            "",
            "### Agent Execution Instructions",
            "",
            "The Agent MUST:",
            "",
            f"1. Read the skill definition at `{self.display_path(self.work_dir / 'skills' / 'c-to-rust-migration-v2' / 'SKILL.md')}`",
            f"2. Read the context package at `{self.display_path(self.context_pkg_path)}` for all paths and data references",
            "3. Execute phases 0 through 10 in strict order, delegating each phase to the appropriate subagent",
            "4. Use `python tools.py run-verification` for build/test commands (data retrieval only)",
            "5. Use `python tools.py check-unsafe`, `fault-injection`, `neutrality-audit` for quality gates (data retrieval only)",
            "6. Use `python tools.py write-report` for final report generation (data to markdown)",
            "7. NEVER call any Python function for code generation, semantic analysis, or repair judgment — all judgment is Agent responsibility",
            "",
            "### Agent Delegation Flow",
            "",
            "```",
            "Phase 0 (preflight)    → Agent reads c2r-00-preflight.md",
            "Phase 1 (understand)   → Agent reads c2r-01-understand.md + source-inventory.json",
            "Phase 2 (design)       → Agent reads c2r-02-design.md",
            "Phase 3 (spec)         → Agent reads c2r-03-spec.md",
            "Phase 4 (plan)         → Agent reads c2r-04-plan.md",
            "Phase 5 (implement)    → Agent reads c2r-05-implement.md × N batches + C source files",
            "Phase 6 (test)         → Agent reads c2r-06-test.md × N batches + C test files",
            "Phase 7 (repair)       → Agent reads c2r-07-repair.md + error logs",
            "Phase 8 (semantic)     → Agent reads c2r-08-semantic-audit.md + C source",
            "Phase 9 (quality)      → Agent reads c2r-09-quality-gates.md + tools.py",
            "Phase 10 (finalize)    → Agent reads c2r-10-finalize.md + tools.py write-report",
            "```",
            "",
            "### Source APIs Detected",
            "",
        ]
        output_lines.extend([f"- `{api}`" for api in (public_apis or ["none detected"])])
        output_lines.append("")
        self.result_output_path.write_text("\n".join(output_lines), encoding="utf-8")

        issue_lines = [
            "# Issue Summary",
            "",
            "- final_status: AGENT_DELEGATION_READY",
            f"- generated_at: `{utc_now()}`",
            f"- input_root: `{self.display_path(self.input_root)}`",
            f"- source_root: `{self.display_path(self.source_root)}`",
            "- issue_count: 0 (pre-generation phase)",
            "",
            "## Note",
            "",
            "The Python runner has completed data preparation. All further phases are delegated to the Agent.",
            "Check result/output.md for Agent execution instructions.",
            "",
        ]
        self.issue_summary_path.write_text("\n".join(issue_lines), encoding="utf-8")

        return {
            "status": "AGENT_DELEGATION_READY",
            "context_package_path": str(self.context_pkg_path),
            "result_output_path": str(self.result_output_path),
        }

    def run_entrypoint(self) -> Dict[str, Any]:
        """Prepare data and delegate to Agent.

        1. Self-check environment
        2. Run source analysis (deterministic, no body_kind)
        3. Run semantic planning (deterministic migration plan)
        4. Write context package for Agent
        5. Output Agent delegation instructions
        """
        self.ensure_outputs()
        packet = self.create_agent_task_packet()

        # Stage 1: Self-check
        self_check_payload = self.self_check(packet)
        if not self_check_payload["ok"]:
            self._write_blocked_report(packet, self_check_payload, "SELF_CHECK_FAILED")
            return {"ok": False, "status": "BLOCKED_WITH_REPORT", "self_check": self_check_payload}

        # Stage 2: Source analysis (deterministic data extraction, no body_kind)
        analysis = self._run_source_analysis(packet)
        self.write_json(self.migration_trace_dir / "semantic-invariants.json", {"invariants": []})

        if not analysis["ok"]:
            source_gate = {"passed": False, "status": "BLOCKED_WITH_REPORT", "failures": analysis.get("verification", {}).get("failures", []), "first_blocking_point": "C_SOURCE_ANALYSIS"}
            self._write_blocked_report(packet, source_gate, "SOURCE_ANALYSIS_FAILED")
            return {"ok": False, "status": "BLOCKED_WITH_REPORT", "analysis": analysis, "source_gate": source_gate}

        # Source analysis verify gate
        source_gate = build_and_verify_source_analysis(packet, analysis, self.migration_trace_dir)
        if not source_gate.get("passed"):
            self._write_blocked_report(packet, source_gate, "SOURCE_ANALYSIS_VERIFY_FAILED")
            return {"ok": False, "status": "BLOCKED_WITH_REPORT", "analysis": analysis, "source_gate": source_gate}

        # Stage 3: Semantic planning (deterministic migration plan)
        try:
            semantic_plan = plan_from_trace(self.migration_trace_dir)
        except PlanningBlocked as exc:
            plan_gate = {"passed": False, "status": "BLOCKED_WITH_REPORT", "failures": exc.failures, "first_blocking_point": "SEMANTIC_MIGRATION_PLANNING"}
            self._write_blocked_report(packet, plan_gate, "PLANNING_BLOCKED")
            return {"ok": False, "status": "BLOCKED_WITH_REPORT", "analysis": analysis, "plan_gate": plan_gate}

        if not semantic_plan.get("passed"):
            self._write_blocked_report(packet, semantic_plan, "PLANNING_NOT_PASSED")
            return {"ok": False, "status": "BLOCKED_WITH_REPORT", "analysis": analysis, "plan_gate": semantic_plan}

        # Stage 4: Build context package for Agent
        context_pkg = self._build_context_package(packet, analysis, source_gate, semantic_plan)
        self.write_json(self.context_pkg_path, context_pkg)

        # Stage 5: Write delegation report
        delegation = self._write_agent_delegation_report(packet, analysis, context_pkg)

        # Write final report
        final_report = {
            "generated_at": utc_now(),
            "status": "AGENT_DELEGATION_READY",
            "self_check": self_check_payload,
            "source_analysis": analysis.get("verification", {}),
            "source_gate": source_gate,
            "semantic_planning": semantic_plan,
            "context_package_path": str(self.context_pkg_path),
            "instructions": "The Agent must read work/skills/c-to-rust-migration-v2/SKILL.md and execute phases 0-10.",
        }
        self.write_json(self.run_summary_path, final_report)
        self.write_json((self.artifact_dir / "state" / "packet.json"), packet.to_dict())
        self.final_report_path.write_text(
            "# LoopForge Final Report\n\n"
            f"- status: `AGENT_DELEGATION_READY`\n"
            f"- generated_at: `{utc_now()}`\n"
            f"- source_root: `{self.display_path(self.source_root)}`\n"
            f"- output_project_dir: `{self.display_path(packet.output_project_dir)}`\n\n"
            "## Data preparation complete. All judgment phases delegated to Agent.\n\n"
            f"Context Package: `{self.display_path(self.context_pkg_path)}`\n\n"
            f"Skill: `{self.display_path(self.work_dir / 'skills' / 'c-to-rust-migration-v2' / 'SKILL.md')}`\n\n",
            encoding="utf-8",
        )

        return {
            "ok": True,
            "status": "AGENT_DELEGATION_READY",
            "self_check": self_check_payload,
            "analysis": analysis,
            "source_gate": source_gate,
            "semantic_planning": semantic_plan,
            "delegation": delegation,
        }

    def _write_blocked_report(self, packet: AgentTaskPacket, gate: Dict[str, Any], reason: str) -> None:
        """Write BLOCKED_WITH_REPORT output when a pre-generation stage fails."""
        self.result_output_path.write_text(
            "# Output\n\n"
            f"- status: `BLOCKED_WITH_REPORT`\n"
            f"- reason: `{reason}`\n"
            f"- generated_at: `{utc_now()}`\n\n"
            f"## Gate Details\n\n"
            f"```json\n{json.dumps(gate, indent=2, ensure_ascii=True)}\n```\n",
            encoding="utf-8",
        )
        self.issue_summary_path.write_text(
            "# Issue Summary\n\n"
            f"- final_status: BLOCKED_WITH_REPORT\n"
            f"- reason: {reason}\n"
            f"- generated_at: `{utc_now()}`\n\n"
            f"## Gate\n\n"
            f"```json\n{json.dumps(gate, indent=2, ensure_ascii=True)}\n```\n",
            encoding="utf-8",
        )


def resolve_path(base: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = (base / path).resolve()
    return path.resolve()


def resolve_default_source_root(workspace_root: Path, platform_name: Optional[str] = None) -> Path:
    current_platform = platform_name or os.name
    if current_platform == "nt":
        return (workspace_root / "__CONTEST_PLATFORM_SOURCE_ROOT__" / "source").resolve()
    for candidate in [Path("/__CONTEST_PLATFORM_SOURCE_ROOT__/source"), Path("/__CONTEST_PLATFORM_SOURCE_ROOT__")]:
        if candidate.is_dir():
            return candidate.resolve()
    return Path("/__CONTEST_PLATFORM_SOURCE_ROOT__/source").resolve()


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LoopForge execution orchestrator — data preparation + Agent delegation")
    parser.add_argument("--work-dir", default="work")
    parser.add_argument("--source-root")
    parser.add_argument("--result-dir", default="result")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--run", action="store_true")
    return parser.parse_args(argv)


def print_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True))


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    if not any([args.self_check, args.run]):
        print("No action provided.", file=sys.stderr)
        return 2

    script_root = Path(__file__).resolve().parent.parent.parent  # runtime -> work -> repo root
    work_dir = resolve_path(script_root, args.work_dir)
    workspace_root = work_dir.parent
    source_arg = (args.source_root or os.environ.get("SOURCE_ROOT", "")).strip()
    source_root = resolve_path(workspace_root, source_arg) if source_arg else resolve_default_source_root(workspace_root)
    result_dir = resolve_path(workspace_root, args.result_dir)
    log_dir = resolve_path(workspace_root, args.log_dir)

    try:
        runner = LoopForgeRunner(workspace_root, work_dir, source_root, result_dir, log_dir)
        if args.self_check:
            packet = runner.create_agent_task_packet()
            runner.ensure_outputs()
            print_json(runner.self_check(packet))
        if args.run:
            print_json(runner.run_entrypoint())
    except Exception as exc:
        fallback = {
            "ok": False,
            "status": "BLOCKED_WITH_REPORT",
            "exception": {"kind": type(exc).__name__, "detail": str(exc)},
        }
        print_json(fallback)
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
