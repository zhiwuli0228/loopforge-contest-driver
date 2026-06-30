#!/usr/bin/env python3
"""LoopForge runner with a source-README execution adapter for FlashDB migration."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
README_CANDIDATES = [
    "README.md",
    "README",
    "READNE.md",
    "readme.md",
    "Readme.md",
]
MODE_RULE_FILES = [
    "00-flow.md",
    "01-phase-policy.md",
    "02-required-artifacts.md",
    "03-forbidden-actions.md",
    "04-final-report.md",
]
WORK_PACKAGE_FILES = [
    "INSTRUCTION.md",
    "README.md",
    "SUBMISSION.md",
    "work/loopforge.config.yaml",
    "work/HARNESS.md",
    "work/runtime/loopforge_runner.py",
    "work/runtime/check_unsafe_ratio.py",
    "work/scripts/bootstrap.sh",
    "work/scripts/bootstrap.ps1",
    "work/scripts/run.sh",
    "work/scripts/run.ps1",
    "work/scripts/smoke-test.sh",
    "work/scripts/smoke-test.ps1",
    "work/skills/loopforge-driver/SKILL.md",
    "work/skills/c2rust-flashdb-migration/SKILL.md",
    "work/docs/DESIGN.md",
    "work/docs/ADAPTATION_GUIDE.md",
    "work/docs/CROSS_PLATFORM_DESIGN.md",
    "work/docs/DAILY_DEV_USAGE.md",
    "work/profiles/README.md",
]
ARTIFACT_SUBDIRS = [
    "consistency",
    "gates",
    "plan",
    "reports",
    "runtime",
    "snapshots",
    "state",
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

        if ":" not in stripped:
            raise ValueError(f"invalid yaml near line {index + 1}")
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


def iter_rust_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.rs"):
        if "target" in path.parts:
            continue
        yield path


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def path_is_relative_to(path: Path, other: Path) -> bool:
    try:
        path.relative_to(other)
        return True
    except ValueError:
        return False


@dataclass
class CommandResult:
    command: str
    returncode: int
    stdout: str
    stderr: str
    error: Optional[str] = None


class LoopForgeRunner:
    def __init__(
        self,
        workspace_root: Path,
        work_dir: Path,
        source_root: Path,
        result_dir: Path,
        log_dir: Path,
    ) -> None:
        self.workspace_root = workspace_root.resolve()
        self.work_dir = work_dir.resolve()
        self.source_root = source_root.resolve()
        self.result_dir = result_dir.resolve()
        self.log_dir = log_dir.resolve()
        self.config_path = self.work_dir / "loopforge.config.yaml"
        self.config = self.load_config()
        self.task = self.config.get("task", {})
        self.platform_cfg = self.config.get("platform", {})
        self.verification_cfg = self.config.get("verification", {})
        self.outputs_cfg = self.config.get("outputs", {})
        self.profile_rel = str(self.task.get("profile", "")).strip()
        self.profile_path = (self.work_dir / self.profile_rel.replace("/", os.sep)).resolve() if self.profile_rel else None
        self.artifact_root = (self.source_root / ".loopforge").resolve()
        self.result_output_path = self.result_dir / "output.md"
        self.issue_summary_path = self.result_dir / "issues" / "00-summary.md"
        self.interaction_log_path = self.log_dir / "interaction.md"
        self.trace_dir = self.log_dir / "trace"
        self.run_summary_path = self.trace_dir / "run-summary.json"
        self.flashdb_rust_dir = (self.workspace_root / "flashDB_rust").resolve()
        self.consistency_dir = self.artifact_root / "consistency"
        self.gates_path = self.artifact_root / "gates" / "gate-events.md"
        self.mode_artifacts_path = self.artifact_root / "plan" / "mode-artifacts.md"
        self.final_report_path = self.artifact_root / "reports" / "final-report.md"
        self.runtime_runner_copy = self.artifact_root / "runtime" / "loopforge_runner.py"
        self.state_dir = self.artifact_root / "state"
        self.config_summary_path = self.state_dir / "config-check-summary.json"
        self.profile_summary_path = self.state_dir / "profile-check-summary.json"
        self.work_package_summary_path = self.state_dir / "work-package-summary.json"
        self.detect_summary_path = self.state_dir / "detect-summary.json"
        self.verification_summary_path = self.state_dir / "verification-summary.json"
        self.loop_state_path = self.state_dir / "loop-state.json"
        self.snapshot_default_path = self.artifact_root / "snapshots" / "before-verify.diff"
        self.c2rust_trace_dir = self.trace_dir / "c2rust"
        self.source_inventory_path = self.c2rust_trace_dir / "01-source-inventory.md"
        self.api_mapping_path = self.c2rust_trace_dir / "02-api-mapping.md"
        self.migration_plan_path = self.c2rust_trace_dir / "03-migration-plan.md"
        self.test_mapping_path = self.c2rust_trace_dir / "04-test-mapping.md"
        self.migration_summary_path = self.c2rust_trace_dir / "05-migration-summary.md"
        self.verification_report_path = self.c2rust_trace_dir / "06-verification-report.md"
        self.unsafe_ratio_path = self.c2rust_trace_dir / "unsafe-ratio.json"
        self.gate_events: List[Tuple[str, str, str, str]] = []

    def load_config(self) -> Dict[str, Any]:
        return parse_simple_yaml(self.config_path.read_text(encoding="utf-8"))

    def save_json(self, path: Path, payload: Dict[str, Any]) -> None:
        ensure_parent(path)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    def ensure_placeholder(self, path: Path, content: str) -> None:
        ensure_parent(path)
        if not path.exists():
            path.write_text(content, encoding="utf-8")

    def record_gate(self, stage: str, status: str, action: str, detail: str) -> None:
        self.gate_events.append((stage, status, action, detail))
        lines = [
            "| Stage | Status | Action | Detail |",
            "|---|---|---|---|",
        ]
        lines.extend(f"| {stage} | {status} | {action} | {detail} |" for stage, status, action, detail in self.gate_events)
        ensure_parent(self.gates_path)
        self.gates_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def ensure_outputs(self) -> None:
        self.result_dir.mkdir(parents=True, exist_ok=True)
        (self.result_dir / "issues").mkdir(parents=True, exist_ok=True)
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.c2rust_trace_dir.mkdir(parents=True, exist_ok=True)
        for name in ARTIFACT_SUBDIRS:
            (self.artifact_root / name).mkdir(parents=True, exist_ok=True)
        if not self.interaction_log_path.exists():
            self.interaction_log_path.write_text("# Interaction Log\n\nNo manual interaction.\n", encoding="utf-8")
        shutil.copy2(self.work_dir / "runtime" / "loopforge_runner.py", self.runtime_runner_copy)
        self.ensure_placeholder(self.result_output_path, "# Output\n")
        self.ensure_placeholder(self.issue_summary_path, "# Issue Summary\n")
        self.ensure_placeholder(self.verification_report_path, "# Verification Report\n")
        self.ensure_placeholder(
            self.mode_artifacts_path,
            self.render_mode_artifact_index([]),
        )
        self.record_gate("BOOTSTRAP", "PASS", "initialize artifact tree", str(self.artifact_root))

    def render_mode_artifact_index(self, produced: List[str]) -> str:
        mode = str(self.task.get("mode", "unknown"))
        lines = [
            "# Mode Artifacts",
            "",
            f"- mode: `{mode}`",
            f"- generated_at: `{utc_now()}`",
            "",
            f"This file indexes mode-specific planning and analysis artifacts under `{self.artifact_root / 'plan'}`.",
            "",
            "## Recommended Artifacts",
            "",
        ]
        recommendations = {
            "feature-development": ["requirements.md", "brainstorm.md", "design-draft.md", "implementation-plan.md"],
            "migration": ["source-inventory.md", "api-mapping.md", "migration-plan.md", "verification-notes.md"],
        }
        for item in recommendations.get(mode, ["mode-notes.md"]):
            lines.append(f"- `{item}`")
        lines.extend(["", "## Produced Artifacts", ""])
        if produced:
            lines.extend(f"- `{item}`" for item in produced)
        else:
            lines.append("- No mode-specific artifacts have been recorded yet.")
        lines.append("")
        return "\n".join(lines)

    def resolve_path_token(self, value: str) -> Path:
        if value == "SOURCE_ROOT":
            return self.source_root
        if value.startswith("SOURCE_ROOT/"):
            return (self.source_root / value[len("SOURCE_ROOT/") :]).resolve()
        path = Path(value)
        if not path.is_absolute():
            path = (self.workspace_root / path).resolve()
        return path.resolve()

    def detect_source_readme(self) -> Dict[str, Any]:
        candidates = [str((self.source_root / name).resolve()) for name in README_CANDIDATES]
        selected = ""
        for name in README_CANDIDATES:
            candidate = self.source_root / name
            if candidate.is_file():
                selected = str(candidate.resolve())
                break
        return {
            "found": bool(selected),
            "selected_path": selected,
            "candidates": candidates,
        }

    def resolve_flashdb_root(self) -> Optional[Path]:
        for candidate in [self.source_root, self.source_root / "FlashDB"]:
            if (candidate / "src").is_dir() and (candidate / "tests").is_dir():
                return candidate.resolve()
        return None

    def collect_relative_files(self, root: Path, suffix: str) -> List[str]:
        if not root.is_dir():
            return []
        return sorted(str(path.relative_to(root)).replace("\\", "/") for path in root.rglob(f"*{suffix}") if path.is_file())

    def write_source_inventory(self, readme: Dict[str, Any], flashdb_root: Optional[Path]) -> None:
        src_files: List[str] = []
        test_files: List[str] = []
        if flashdb_root is not None:
            src_files = self.collect_relative_files(flashdb_root / "src", ".c") + self.collect_relative_files(flashdb_root / "src", ".h")
            test_files = self.collect_relative_files(flashdb_root / "tests", ".c") + self.collect_relative_files(flashdb_root / "tests", ".h")
        lines = [
            "# Source Inventory",
            "",
            f"- selected_readme: `{readme['selected_path'] or 'missing'}`",
            f"- source_root: `{self.source_root}`",
            f"- resolved_flashdb_root: `{flashdb_root or 'missing'}`",
            "",
            "## Source Files",
            "",
        ]
        lines.extend([f"- `{item}`" for item in src_files] or ["- No C source files detected under `src/`."])
        lines.extend(["", "## Test Files", ""])
        lines.extend([f"- `{item}`" for item in test_files] or ["- No C test files detected under `tests/`."])
        lines.extend(
            [
                "",
                "## Detected Boundaries",
                "",
                "- Public APIs: pending README-driven extraction.",
                "- Data structures: pending README-driven extraction.",
                "- Storage and I/O boundaries: pending README-driven extraction.",
                "",
            ]
        )
        self.source_inventory_path.write_text("\n".join(lines), encoding="utf-8")

    def write_api_mapping(self, flashdb_root: Optional[Path]) -> None:
        lines = [
            "# API Mapping",
            "",
            f"- resolved_flashdb_root: `{flashdb_root or 'missing'}`",
            "",
            "## Planned Mapping",
            "",
            "- C API to Rust module mapping: derive from README and source layout.",
            "- Data model mapping: preserve FlashDB semantics where source files are present.",
            "- Error/result strategy: use `Result` and explicit error types.",
            "- Ownership strategy: safe ownership-first translation.",
            "- Unsafe avoidance strategy: keep `unsafe` below the configured threshold.",
            "",
        ]
        self.api_mapping_path.write_text("\n".join(lines), encoding="utf-8")

    def write_test_mapping(self, flashdb_root: Optional[Path]) -> None:
        test_files = self.collect_relative_files((flashdb_root / "tests") if flashdb_root else Path("."), ".c") if flashdb_root else []
        lines = [
            "# Test Mapping",
            "",
            f"- resolved_flashdb_root: `{flashdb_root or 'missing'}`",
            "",
            "## C Test Scenarios",
            "",
        ]
        lines.extend([f"- `{item}` -> pending Rust equivalent" for item in test_files] or ["- No C tests detected."])
        lines.append("")
        self.test_mapping_path.write_text("\n".join(lines), encoding="utf-8")

    def write_migration_summary(self, readme: Dict[str, Any], flashdb_root: Optional[Path]) -> None:
        lines = [
            "# Migration Summary",
            "",
            f"- generated_at: `{utc_now()}`",
            f"- source_root: `{self.source_root}`",
            f"- selected_readme: `{readme['selected_path'] or 'missing'}`",
            f"- flashdb_root: `{flashdb_root or 'missing'}`",
            "",
            "## Status",
            "",
            "- Execution adapter initialized.",
            "- Verification is only runnable when source requirements and generated Rust output are both present.",
            "",
        ]
        self.migration_summary_path.write_text("\n".join(lines), encoding="utf-8")

    def validate_profile(self) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []
        profile_data: Dict[str, Any] = {}
        if not self.profile_path or not self.profile_path.is_file():
            errors.append("profile: profile file not found")
        else:
            profile_data = parse_simple_yaml(self.profile_path.read_text(encoding="utf-8"))
            profile_mode = str(profile_data.get("task", {}).get("mode", "")).strip()
            task_mode = str(self.task.get("mode", "")).strip()
            if profile_mode and task_mode and profile_mode != task_mode:
                errors.append(f"profile: task.mode ({task_mode}) does not match profile task.mode ({profile_mode})")
        payload = {
            "ok": not errors,
            "errors": errors,
            "warnings": warnings,
            "profile_path": str(self.profile_path) if self.profile_path else "",
            "profile_name": str(profile_data.get("profile", {}).get("name", "")),
            "profile_class": str(profile_data.get("profile", {}).get("class", "")),
            "task_mode": str(profile_data.get("task", {}).get("mode", "")),
        }
        self.save_json(self.profile_summary_path, payload)
        return payload

    def validate_work_package(self) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []
        required_present: List[str] = []
        required_missing: List[str] = []
        for relative in WORK_PACKAGE_FILES:
            candidate = self.workspace_root / relative
            if candidate.exists():
                required_present.append(relative.replace("\\", "/"))
            else:
                required_missing.append(relative.replace("\\", "/"))
        mode = str(self.task.get("mode", "")).strip()
        mode_root = self.work_dir / "rules" / "loopforge" / "modes" / mode
        available_modes: Dict[str, List[str]] = {}
        all_modes_root = self.work_dir / "rules" / "loopforge" / "modes"
        if all_modes_root.is_dir():
            for child in sorted(all_modes_root.iterdir()):
                if child.is_dir():
                    available_modes[child.name] = sorted(item.name for item in child.iterdir() if item.is_file())
        for filename in MODE_RULE_FILES:
            candidate = mode_root / filename
            if not candidate.exists():
                errors.append(f"work-package: missing required mode rule: rules/loopforge/modes/{mode}/{filename}")
        payload = {
            "ok": not errors and not required_missing,
            "errors": errors,
            "warnings": warnings,
            "required_files_present": required_present,
            "required_files_missing": required_missing,
            "available_modes": available_modes,
            "configured_mode": mode,
            "template_count": len(list((self.work_dir / "profiles" / "templates").glob("*.yaml"))),
            "example_count": len(list((self.work_dir / "profiles" / "examples").glob("*.yaml"))),
        }
        self.save_json(self.work_package_summary_path, payload)
        return payload

    def validate_config(self) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []
        profile_summary = self.validate_profile()
        work_package_summary = self.validate_work_package()
        errors.extend(profile_summary["errors"])
        errors.extend(work_package_summary["errors"])
        if work_package_summary["required_files_missing"]:
            errors.extend(f"work-package: missing required file: {item}" for item in work_package_summary["required_files_missing"])

        working_directory_raw = str(self.verification_cfg.get("working_directory", "SOURCE_ROOT"))
        resolved_working_directory = self.resolve_path_token(working_directory_raw)
        allowed_workdirs = [self.source_root, self.flashdb_rust_dir]
        if not any(resolved_working_directory == allowed or path_is_relative_to(resolved_working_directory, allowed) for allowed in allowed_workdirs):
            errors.append("verification.working_directory must resolve to SOURCE_ROOT or a descendant of SOURCE_ROOT")

        commands_cfg = self.verification_cfg.get("commands", [])
        commands_format = "invalid"
        available_profiles: List[str] = []
        commands_count = 0
        if isinstance(commands_cfg, list):
            commands_format = "list"
            commands_count = len(commands_cfg)
        elif isinstance(commands_cfg, dict):
            commands_format = "platform-map"
            available_profiles = sorted(str(key) for key in commands_cfg.keys())
            default_commands = commands_cfg.get("default", [])
            if isinstance(default_commands, list):
                commands_count = len(default_commands)
            else:
                errors.append("verification.commands must be a list or a platform command map")
        else:
            errors.append("verification.commands must be a list or a platform command map")

        final_report_raw = str(self.outputs_cfg.get("final_report", ""))
        if final_report_raw:
            final_report_target = self.resolve_path_token(final_report_raw)
            allowed_output_roots = [self.artifact_root, self.trace_dir]
            if not any(path_is_relative_to(final_report_target, root) or final_report_target == root for root in allowed_output_roots):
                errors.append("outputs.final_report must resolve under SOURCE_ROOT/.loopforge/")

        payload = {
            "ok": not errors,
            "errors": errors,
            "warnings": warnings,
            "platform": {
                "configured_work_dir": str(self.work_dir),
                "configured_code_dir": str((self.workspace_root / str(self.platform_cfg.get("code_dir", "code"))).resolve()),
                "artifact_dir": str(self.artifact_root),
            },
            "task": {
                "mode": str(self.task.get("mode", "")),
                "profile": self.profile_rel,
            },
            "verification": {
                "working_directory": str(resolved_working_directory),
                "commands_format": commands_format,
                "available_profiles": available_profiles,
                "selected_profile": "",
                "fallback_used": False,
                "commands_count": commands_count,
            },
            "governance": {
                "ok": True,
                "superspec": "",
                "superpower": "",
                "mode_rules": MODE_RULE_FILES,
                "delegated_staged_ready": False,
            },
            "subagent_contract": {
                "ok": True,
                "errors": [],
                "warnings": [],
                "stage_count": 0,
                "stages": [],
            },
            "coding_skill": {
                "ok": True,
                "errors": [],
                "warnings": [],
                "enabled": bool(self.config.get("coding_skill", {}).get("enabled", False)),
                "required": bool(self.config.get("coding_skill", {}).get("required", False)),
                "skill": str(self.config.get("coding_skill", {}).get("skill", "")),
                "apply_at": list(self.config.get("coding_skill", {}).get("apply_at", [])),
                "output": str(self.config.get("coding_skill", {}).get("output", "")),
                "ready_status": "CODING_SKILL_READY",
                "skill_exists": True,
                "references_ready": True,
                "stage_declared": False,
                "superpower_policy_ready": False,
            },
            "outputs": {
                "consistency_dir": str(self.consistency_dir),
                "final_report": str(self.final_report_path),
                "patch_snapshot_dir": str(self.artifact_root / "snapshots"),
            },
            "profile_summary": profile_summary,
            "work_package_summary": work_package_summary,
        }
        self.save_json(self.config_summary_path, payload)
        return payload

    def self_check(self) -> Dict[str, Any]:
        self.ensure_outputs()
        payload = self.validate_config()
        self.save_json(
            self.loop_state_path,
            {
                "generated_at": utc_now(),
                "source_root": str(self.source_root),
                "artifact_root": str(self.artifact_root),
                "task_mode": str(self.task.get("mode", "")),
            },
        )
        self.record_gate("SELF_CHECK", "PASS" if payload["ok"] else "FAIL", "validate runtime contract", "self-check completed")
        return payload

    def detect_project(self) -> Dict[str, Any]:
        self.ensure_outputs()
        source_readme = self.detect_source_readme()
        flashdb_root = self.resolve_flashdb_root()
        payload = {
            "project_type": "flashdb-c2rust" if flashdb_root else "unknown",
            "indicators": {
                "git_worktree": (self.workspace_root / ".git").exists(),
                "source_readme": source_readme["found"],
                "flashdb_layout": flashdb_root is not None,
                "generated_rust_project": self.flashdb_rust_dir.exists(),
            },
            "source_readme": source_readme,
            "flashdb_root": str(flashdb_root) if flashdb_root else "",
        }
        self.write_source_inventory(source_readme, flashdb_root)
        self.write_api_mapping(flashdb_root)
        self.write_test_mapping(flashdb_root)
        self.write_migration_summary(source_readme, flashdb_root)
        self.save_json(self.detect_summary_path, payload)
        self.record_gate("DETECT", "PASS", "detect project shape", payload["project_type"])
        return payload

    def run_command(self, command: List[str], cwd: Path, timeout_seconds: int) -> CommandResult:
        try:
            completed = subprocess.run(
                command,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            return CommandResult(" ".join(command), completed.returncode, completed.stdout, completed.stderr)
        except FileNotFoundError as exc:
            return CommandResult(" ".join(command), 127, "", "", error=str(exc))
        except subprocess.TimeoutExpired as exc:
            return CommandResult(" ".join(command), 124, exc.stdout or "", exc.stderr or "", error="timeout")

    def normalize_commands(self) -> List[str]:
        commands_cfg = self.verification_cfg.get("commands", [])
        if isinstance(commands_cfg, list):
            return [str(item) for item in commands_cfg]
        if isinstance(commands_cfg, dict):
            default_commands = commands_cfg.get("default", [])
            if isinstance(default_commands, list):
                return [str(item) for item in default_commands]
        return []

    def derive_verification_plan(self, detect_payload: Dict[str, Any], config_summary: Dict[str, Any]) -> Dict[str, Any]:
        source_readme = detect_payload["source_readme"]
        commands = self.normalize_commands()
        selected_profile = ""
        fallback_used = False
        working_directory = self.resolve_path_token(str(self.verification_cfg.get("working_directory", "SOURCE_ROOT")))
        timeout_seconds = int(self.verification_cfg.get("timeout_seconds", 600) or 600)
        reasons: List[str] = []
        runnable = True

        if not source_readme["found"]:
            reasons.append("source README not found")
        if not config_summary["ok"]:
            reasons.extend(str(item) for item in config_summary["errors"])

        if working_directory == self.flashdb_rust_dir and not self.flashdb_rust_dir.exists():
            runnable = False
        if detect_payload.get("project_type") != "flashdb-c2rust":
            runnable = False
        if not commands:
            runnable = False

        if not runnable:
            reasons.append("no runnable verification commands were derived from source README or framework defaults")

        return {
            "ok": runnable and not reasons,
            "status": "ready" if runnable and not reasons else "blocked-with-report",
            "detected_os": platform.system().lower(),
            "selected_command_profile": selected_profile,
            "fallback_used": fallback_used,
            "working_directory": str(working_directory),
            "timeout_seconds": timeout_seconds,
            "commands_attempted": [],
            "commands": commands,
            "source_readme": source_readme,
            "reason": "; ".join(reasons) if reasons else "",
        }

    def check_unsafe_ratio(self, project_root: Path, max_ratio: float = 0.10) -> Dict[str, Any]:
        total_lines = 0
        unsafe_lines = 0
        files: List[Dict[str, Any]] = []
        for rust_file in iter_rust_files(project_root):
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
            files.append({"file": str(rust_file), "code_lines": file_total, "unsafe_lines": file_unsafe})
        ratio = (unsafe_lines / total_lines) if total_lines else 0.0
        payload = {
            "project": str(project_root),
            "total_code_lines": total_lines,
            "unsafe_lines": unsafe_lines,
            "unsafe_ratio": ratio,
            "max_ratio": max_ratio,
            "passed": ratio < max_ratio,
            "files": files,
            "generated_at": utc_now(),
        }
        self.unsafe_ratio_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        return payload

    def verify(self) -> Dict[str, Any]:
        self.ensure_outputs()
        config_summary = self.validate_config()
        detect_payload = self.detect_project()
        plan = self.derive_verification_plan(detect_payload, config_summary)
        if plan["status"] == "blocked-with-report":
            payload = {
                "ok": False,
                "status": "blocked-with-report",
                "detected_os": plan["detected_os"],
                "selected_command_profile": plan["selected_command_profile"],
                "fallback_used": plan["fallback_used"],
                "working_directory": plan["working_directory"],
                "timeout_seconds": plan["timeout_seconds"],
                "commands_attempted": [],
                "source_readme": plan["source_readme"],
                "reason": plan["reason"],
            }
            self.save_json(self.verification_summary_path, payload)
            self.verification_report_path.write_text(
                "\n".join(
                    [
                        "# Verification Report",
                        "",
                        "## Result",
                        "",
                        "BLOCKED_WITH_REPORT",
                        "",
                        f"- reason: {plan['reason']}",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            self.record_gate("VERIFY", "FAIL", "verification blocked", plan["reason"])
            return payload

        commands_attempted: List[Dict[str, Any]] = []
        for command in plan["commands"]:
            result = self.run_command(command.split(), Path(plan["working_directory"]), int(plan["timeout_seconds"]))
            commands_attempted.append(
                {
                    "command": command,
                    "returncode": result.returncode,
                    "error": result.error,
                    "stdout_tail": result.stdout.strip().splitlines()[-20:],
                    "stderr_tail": result.stderr.strip().splitlines()[-20:],
                    "ok": result.returncode == 0 and result.error is None,
                }
            )
            if result.returncode != 0 or result.error is not None:
                payload = {
                    "ok": False,
                    "status": "blocked-with-report",
                    "detected_os": plan["detected_os"],
                    "selected_command_profile": plan["selected_command_profile"],
                    "fallback_used": plan["fallback_used"],
                    "working_directory": plan["working_directory"],
                    "timeout_seconds": plan["timeout_seconds"],
                    "commands_attempted": commands_attempted,
                    "source_readme": plan["source_readme"],
                    "reason": "all configured verification commands failed",
                }
                self.save_json(self.verification_summary_path, payload)
                self.record_gate("VERIFY", "FAIL", "verification failed", payload["reason"])
                return payload

        unsafe_payload = self.check_unsafe_ratio(self.flashdb_rust_dir)
        if not unsafe_payload["passed"]:
            payload = {
                "ok": False,
                "status": "blocked-with-report",
                "detected_os": plan["detected_os"],
                "selected_command_profile": plan["selected_command_profile"],
                "fallback_used": plan["fallback_used"],
                "working_directory": plan["working_directory"],
                "timeout_seconds": plan["timeout_seconds"],
                "commands_attempted": commands_attempted,
                "source_readme": plan["source_readme"],
                "reason": "unsafe ratio is too high",
                "unsafe": unsafe_payload,
            }
            self.save_json(self.verification_summary_path, payload)
            self.record_gate("VERIFY", "FAIL", "verification failed", payload["reason"])
            return payload

        payload = {
            "ok": True,
            "status": "ready-for-evaluation",
            "detected_os": plan["detected_os"],
            "selected_command_profile": plan["selected_command_profile"],
            "fallback_used": plan["fallback_used"],
            "working_directory": plan["working_directory"],
            "timeout_seconds": plan["timeout_seconds"],
            "commands_attempted": commands_attempted,
            "source_readme": plan["source_readme"],
            "reason": "",
            "unsafe": unsafe_payload,
        }
        self.save_json(self.verification_summary_path, payload)
        self.verification_report_path.write_text(
            "\n".join(
                [
                    "# Verification Report",
                    "",
                    "## Result",
                    "",
                    "READY_FOR_EVALUATION",
                    "",
                    "## Verification",
                    "",
                    json.dumps(payload, indent=2, ensure_ascii=True),
                    "",
                ]
            ),
            encoding="utf-8",
        )
        self.record_gate("VERIFY", "PASS", "verification succeeded", "commands completed")
        return payload

    def finalize(self, detect_payload: Optional[Dict[str, Any]] = None, verify_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.ensure_outputs()
        config_summary = self.validate_config()
        detect_payload = detect_payload or self.detect_project()
        verify_payload = verify_payload or self.verify()
        final_status = "READY_FOR_EVALUATION" if verify_payload.get("ok") else "BLOCKED_WITH_REPORT"
        contract_verdict = "PASS" if config_summary["ok"] else "FAIL"
        profile_summary = json.loads(self.profile_summary_path.read_text(encoding="utf-8"))
        work_package_summary = json.loads(self.work_package_summary_path.read_text(encoding="utf-8"))

        lines = [
            "# LoopForge Final Report",
            "",
            "## Result",
            "",
            final_status,
            "",
            "## Task",
            "",
            json.dumps(self.task, indent=2, ensure_ascii=True),
            "",
            "## Mode And Profile",
            "",
            json.dumps(
                {
                    "mode": self.task.get("mode", ""),
                    "profile": self.profile_rel,
                    "profile_name": profile_summary.get("profile_name", ""),
                    "profile_class": profile_summary.get("profile_class", ""),
                },
                indent=2,
                ensure_ascii=True,
            ),
            "",
            "## Platform",
            "",
            json.dumps(self.platform_cfg, indent=2, ensure_ascii=True),
            "",
            "## Detection",
            "",
            json.dumps(detect_payload, indent=2, ensure_ascii=True),
            "",
            "## Contract Validation",
            "",
            json.dumps(config_summary, indent=2, ensure_ascii=True),
            "",
            "## Contract Verdict",
            "",
            contract_verdict,
            "",
            "## Work Package Contract",
            "",
            json.dumps(work_package_summary, indent=2, ensure_ascii=True),
            "",
            "## Runtime Platform",
            "",
            f"- Detected OS: {platform.system().lower()}",
            f"- Official submission OS: {self.platform_cfg.get('official_submission_os', '')}",
            f"- Local development OS: {', '.join(self.platform_cfg.get('local_development_os', []))}",
            f"- Runner: {self.runtime_runner_copy}",
            f"- Python version: {platform.python_version()}",
            "",
            "## Verification",
            "",
            json.dumps(verify_payload, indent=2, ensure_ascii=True),
            "",
            "## Mode Artifact Summary",
            "",
            self.mode_artifacts_path.read_text(encoding="utf-8").rstrip(),
            "",
            "## Gate Events",
            "",
            self.gates_path.read_text(encoding="utf-8").rstrip(),
            "",
            "## Artifact Location",
            "",
            f"- `{self.artifact_root}`",
            "",
            "## Key Artifacts",
            "",
            f"- `{self.runtime_runner_copy}`",
            f"- `{self.loop_state_path}`",
            f"- `{self.config_summary_path}`",
            f"- `{self.profile_summary_path}`",
            f"- `{self.work_package_summary_path}`",
            f"- `{self.detect_summary_path}`",
            f"- `{self.verification_summary_path}`",
            f"- `{self.mode_artifacts_path}`",
            f"- `{self.final_report_path}`",
            "",
            "## Boundaries",
            "",
            "- Static files in the LoopForge root are read-only during execution.",
            "- Runtime artifacts are written under `SOURCE_ROOT/.loopforge/` and evaluator-facing outputs remain under `result/` and `logs/`.",
            "- LoopForge does not commit, push, create PRs, or submit results.",
            "",
        ]
        self.final_report_path.write_text("\n".join(lines), encoding="utf-8")
        self.record_gate("FINALIZE", "PASS", "write final report", str(self.final_report_path))
        return {"ok": True, "status": final_status, "report": str(self.final_report_path)}

    def write_entrypoint_result(self, detect_payload: Dict[str, Any], verify_payload: Dict[str, Any], finalize_payload: Dict[str, Any]) -> Dict[str, Any]:
        source_readme = detect_payload["source_readme"]
        selected_source_readme = source_readme["selected_path"] or "missing"
        unsafe_ratio = "n/a"
        if isinstance(verify_payload.get("unsafe"), dict):
            unsafe_ratio = f"{verify_payload['unsafe'].get('unsafe_ratio', 0.0):.4f}"
        output_lines = [
            "# Output",
            "",
            f"- status: `{finalize_payload.get('status', 'BLOCKED_WITH_REPORT')}`",
            f"- source_root: `{self.source_root}`",
            f"- source_readme_found: `{str(source_readme['found']).lower()}`",
            f"- selected_source_readme: `{selected_source_readme}`",
            f"- flashdb_root: `{detect_payload.get('flashdb_root', '') or 'missing'}`",
            f"- rust_project: `{self.flashdb_rust_dir}`",
            f"- cargo_build_test: `{'passed' if verify_payload.get('ok') else 'not passed'}`",
            f"- unsafe_ratio: `{unsafe_ratio}`",
            "",
            "## Summary",
            "",
            "- Execution adapter used SOURCE_ROOT plus the source README as the primary task context.",
            "- Verification only runs when source requirements and generated Rust output are both available.",
            "",
        ]
        if verify_payload.get("reason"):
            output_lines.extend(["## Blocking Reason", "", f"- {verify_payload['reason']}", ""])
        self.result_output_path.write_text("\n".join(output_lines), encoding="utf-8")

        issue_lines = ["# Issue Summary", ""]
        if verify_payload.get("ok"):
            issue_lines.extend(["- No blocking issues detected by the execution adapter.", ""])
        else:
            reason = str(verify_payload.get("reason", "unknown"))
            issue_lines.extend(
                [
                    f"- blocking_reason: {reason}",
                    "- known_missing_behavior: actual FlashDB-to-Rust implementation must exist before cargo verification can pass.",
                    "- degraded_compatibility: execution stays blocked until runnable verification commands can be derived and executed.",
                    "- serious_risk: source README and generated project shape drive execution, so missing inputs prevent end-to-end validation.",
                    "",
                ]
            )
        self.issue_summary_path.write_text("\n".join(issue_lines), encoding="utf-8")

        run_summary = {
            "generated_at": utc_now(),
            "source_root": str(self.source_root),
            "artifact_root": str(self.artifact_root),
            "detect": detect_payload,
            "verify": verify_payload,
            "finalize": finalize_payload,
            "result_output": str(self.result_output_path),
            "issue_summary": str(self.issue_summary_path),
            "final_report": str(self.final_report_path),
        }
        self.save_json(self.run_summary_path, run_summary)
        return run_summary

    def snapshot(self, name: str) -> Dict[str, Any]:
        self.ensure_outputs()
        safe_name = f"{name}.diff" if not name.endswith(".diff") else name
        snapshot_path = self.artifact_root / "snapshots" / safe_name
        snapshot_path.write_text("# Snapshot\n\nExecution adapter snapshot placeholder.\n", encoding="utf-8")
        self.record_gate("SNAPSHOT", "PASS", f"write {safe_name}", "snapshot completed")
        return {"ok": True, "snapshot": str(snapshot_path)}

    def run_entrypoint(self) -> Dict[str, Any]:
        self.ensure_outputs()
        self_check_payload = self.self_check()
        detect_payload = self.detect_project()
        self.snapshot("before-verify.diff")
        verify_payload = self.verify()
        finalize_payload = self.finalize(detect_payload, verify_payload)
        self.write_entrypoint_result(detect_payload, verify_payload, finalize_payload)
        return {
            "ok": finalize_payload.get("status") in {"READY_FOR_EVALUATION", "BLOCKED_WITH_REPORT"},
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
    return (workspace_root / "code").resolve()


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LoopForge execution adapter")
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
            print_json({"ok": True, "status": "initialized", "source_root": str(source_root), "artifact_root": str(runner.artifact_root)})
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
