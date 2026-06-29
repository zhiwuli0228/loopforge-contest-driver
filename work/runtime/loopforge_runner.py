#!/usr/bin/env python3
"""LoopForge runner for the work/code platform layout."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


VERSION = "1.0.0"
ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
ARTIFACT_SUBDIRS = [
    "runtime",
    "state",
    "gates",
    "snapshots",
    "reports",
    "plan",
]
REQUIRED_WORK_FILES = [
    "INSTRUCTION.md",
    "README.md",
    "SUBMISSION.md",
    "loopforge.config.yaml",
    "runtime/loopforge_runner.py",
    "scripts/bootstrap.sh",
    "scripts/smoke-test.sh",
    "skills/loopforge-driver/SKILL.md",
    "docs/DESIGN.md",
    "docs/ADAPTATION_GUIDE.md",
    "docs/DAILY_DEV_USAGE.md",
    "profiles/README.md",
]
REQUIRED_CORE_RULE_FILES = [
    "rules/loopforge/core/00-core.md",
    "rules/loopforge/core/01-work-code-boundary.md",
    "rules/loopforge/core/02-static-rule-ownership.md",
    "rules/loopforge/core/03-verification-contract.md",
    "rules/loopforge/core/04-gate-policy.md",
    "rules/loopforge/core/05-final-report.md",
    "rules/loopforge/core/06-code-generation-boundary.md",
]
REQUIRED_MODE_RULE_FILES = [
    "00-flow.md",
    "01-phase-policy.md",
    "02-required-artifacts.md",
    "03-forbidden-actions.md",
    "04-final-report.md",
]
MODE_ARTIFACT_HINTS = {
    "feature-development": [
        "requirements.md",
        "brainstorm.md",
        "design-draft.md",
        "implementation-plan.md",
    ],
    "migration": [
        "source-inventory.md",
        "target-architecture.md",
        "compatibility-contract.md",
        "migration-plan.md",
    ],
    "defect-repair": [
        "failure-summary.md",
        "root-cause.md",
        "minimal-patch-plan.md",
        "changed-files.md",
    ],
    "consistency-check": [
        "design-summary.md",
        "implementation-mapping.md",
        "traceability-matrix.md",
        "drift-report.md",
    ],
    "skill-generation": [
        "capability-inventory.md",
        "usage-contract.md",
        "skill-draft-summary.md",
        "example-coverage.md",
    ],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FORMAT)


def parse_scalar(value: str) -> Any:
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "~"}:
        return None
    if value.lstrip("-").isdigit():
        try:
            return int(value)
        except ValueError:
            return value
    return value


def parse_simple_yaml(text: str) -> Dict[str, Any]:
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Any]] = [(-1, root)]

    def next_meaningful(index: int, lines: List[str]) -> Optional[str]:
        for candidate in lines[index + 1 :]:
            stripped = candidate.strip()
            if stripped and not stripped.startswith("#"):
                return candidate
        return None

    lines = text.splitlines()
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
            container.append(parse_scalar(stripped[2:].strip()))
            continue

        if ":" not in stripped:
            raise ValueError(f"invalid yaml syntax near line {index + 1}")
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value:
            if isinstance(container, list):
                raise ValueError(f"unexpected mapping item in list near line {index + 1}")
            container[key] = parse_scalar(value)
            continue

        upcoming = next_meaningful(index, lines)
        next_container: Any = {}
        if upcoming is not None:
            next_indent = len(upcoming) - len(upcoming.lstrip(" "))
            next_stripped = upcoming.strip()
            if next_indent > indent and next_stripped.startswith("- "):
                next_container = []

        if isinstance(container, list):
            raise ValueError(f"unexpected nested mapping in list near line {index + 1}")
        container[key] = next_container
        stack.append((indent, next_container))

    return root


@dataclass
class CommandResult:
    command: str
    returncode: int
    stdout: str
    stderr: str
    error: Optional[str] = None


class LoopForgeRunner:
    def __init__(self, workspace_root: Path, work_dir: Path, code_dir: Path) -> None:
        self.workspace_root = workspace_root.resolve()
        self.work_dir = work_dir.resolve()
        self.code_dir = code_dir.resolve()
        self.config_path = self.work_dir / "loopforge.config.yaml"
        self.config = self.load_config()
        self.artifact_dir = self.code_dir / str(self.config.get("platform", {}).get("artifact_dir", ".loopforge"))
        self.runtime_copy_path = self.artifact_dir / "runtime" / "loopforge_runner.py"
        self.state_path = self.artifact_dir / "state" / "loop-state.json"
        self.config_check_path = self.artifact_dir / "state" / "config-check-summary.json"
        self.profile_check_path = self.artifact_dir / "state" / "profile-check-summary.json"
        self.package_check_path = self.artifact_dir / "state" / "work-package-summary.json"
        self.detect_path = self.artifact_dir / "state" / "detect-summary.json"
        self.verify_path = self.artifact_dir / "state" / "verification-summary.json"
        self.mode_artifact_summary_path = self.artifact_dir / "plan" / "mode-artifacts.md"
        self.final_report_path = self.artifact_dir / "reports" / "final-report.md"
        self.gate_events_path = self.artifact_dir / "gates" / "gate-events.md"

    def ensure_directories(self) -> None:
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        for name in ARTIFACT_SUBDIRS:
            (self.artifact_dir / name).mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.work_dir / "runtime" / "loopforge_runner.py", self.runtime_copy_path)
        if not self.gate_events_path.exists():
            self.gate_events_path.write_text(
                "# Gate Events\n\n| Phase | Status | Action | Reason |\n|---|---|---|---|\n",
                encoding="utf-8",
            )
        self.ensure_mode_artifact_summary()

    def ensure_mode_artifact_summary(self) -> None:
        if self.mode_artifact_summary_path.exists():
            return
        configured_mode = str(self.config.get("task", {}).get("mode", "")).strip()
        hints = MODE_ARTIFACT_HINTS.get(configured_mode, [])
        lines = [
            "# Mode Artifacts",
            "",
            f"- mode: `{configured_mode or 'unknown'}`",
            f"- generated_at: `{utc_now()}`",
            "",
            "This file indexes mode-specific planning and analysis artifacts under `code/.loopforge/plan/`.",
            "",
            "## Recommended Artifacts",
            "",
        ]
        if hints:
            lines.extend([f"- `{item}`" for item in hints])
        else:
            lines.append("- No mode-specific artifact hints available.")
        lines.extend(
            [
                "",
                "## Produced Artifacts",
                "",
                "- No mode-specific artifacts have been recorded yet.",
                "",
            ]
        )
        self.mode_artifact_summary_path.write_text("\n".join(lines), encoding="utf-8")

    def load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"missing config: {self.config_path}")
        return parse_simple_yaml(self.config_path.read_text(encoding="utf-8"))

    def assert_layout(self) -> None:
        if not self.work_dir.exists():
            raise FileNotFoundError(f"work dir not found: {self.work_dir}")
        if not self.code_dir.exists():
            raise FileNotFoundError(f"code dir not found: {self.code_dir}")
        if self.code_dir == self.work_dir or self.work_dir in self.code_dir.parents or self.code_dir in self.work_dir.parents:
            raise ValueError("work/ and code/ must be isolated sibling trees")
        platform = self.config.get("platform", {})
        if platform.get("layout") != "work-code":
            raise ValueError("unsupported platform.layout; expected work-code")
        if self.artifact_dir == self.code_dir or self.code_dir not in self.artifact_dir.parents:
            raise ValueError("artifact_dir must resolve under code/")

    def load_state(self) -> Dict[str, Any]:
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    data["version"] = VERSION
                    return data
            except json.JSONDecodeError:
                pass
        return {
            "version": VERSION,
            "phase": "BOOTSTRAP",
            "result": "RUNNING",
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "task": self.config.get("task", {}),
        }

    def save_state(self, state: Dict[str, Any]) -> None:
        state["updated_at"] = utc_now()
        self.state_path.write_text(json.dumps(state, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    def save_json(self, path: Path, payload: Dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    def load_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def read_gate_events(self) -> List[str]:
        if not self.gate_events_path.exists():
            return []
        lines = self.gate_events_path.read_text(encoding="utf-8").splitlines()
        events: List[str] = []
        for line in lines:
            if not line.startswith("| ") or line.startswith("|---"):
                continue
            columns = [part.strip() for part in line.strip().strip("|").split("|")]
            if len(columns) >= 2 and columns[0].lower() == "phase" and columns[1].lower() == "status":
                continue
            events.append(line)
        return events

    def gate_status_counts(self, gate_lines: List[str]) -> Dict[str, int]:
        counts: Dict[str, int] = {"PASS": 0, "WARN": 0, "FAIL": 0, "DEGRADE": 0}
        for line in gate_lines:
            columns = [part.strip() for part in line.strip().strip("|").split("|")]
            if len(columns) < 2:
                continue
            status = columns[1].upper()
            counts[status] = counts.get(status, 0) + 1
        return counts

    def artifact_summary(self) -> List[str]:
        return [
            str(self.runtime_copy_path),
            str(self.state_path),
            str(self.config_check_path),
            str(self.profile_check_path),
            str(self.package_check_path),
            str(self.detect_path),
            str(self.verify_path) if self.verify_path.exists() else "verification-summary.json not generated",
            str(self.mode_artifact_summary_path) if self.mode_artifact_summary_path.exists() else "mode-artifacts.md not generated",
            str(self.final_report_path),
        ]

    def validate_profile(self) -> Dict[str, Any]:
        task = self.config.get("task", {})
        configured_mode = str(task.get("mode", "")).strip()
        configured_profile = str(task.get("profile", "")).strip()
        configured_language = task.get("language", {})
        errors: List[str] = []
        warnings: List[str] = []

        if not configured_profile:
            errors.append("task.profile is required")
            return {"ok": False, "errors": errors, "warnings": warnings}

        profile_path = (self.work_dir / configured_profile).resolve()
        if self.work_dir not in profile_path.parents and profile_path != self.work_dir:
            errors.append("task.profile must resolve under work/")
            return {
                "ok": False,
                "errors": errors,
                "warnings": warnings,
                "profile_path": str(profile_path),
            }
        if not profile_path.exists():
            errors.append(f"profile file not found: {profile_path}")
            return {
                "ok": False,
                "errors": errors,
                "warnings": warnings,
                "profile_path": str(profile_path),
            }

        profile_data = parse_simple_yaml(profile_path.read_text(encoding="utf-8"))
        profile_meta = profile_data.get("profile", {})
        profile_task = profile_data.get("task", {})
        profile_inputs = profile_data.get("inputs", {})
        profile_execution = profile_data.get("execution", {})
        profile_verification = profile_data.get("verification", {})
        profile_reporting = profile_data.get("reporting", {})

        for key in ["profile", "task", "inputs", "execution", "verification", "reporting"]:
            if key not in profile_data:
                errors.append(f"profile is missing required top-level section: {key}")

        profile_name = str(profile_meta.get("name", "")).strip()
        if not profile_name:
            errors.append("profile.name is required")
        profile_class = str(profile_meta.get("class", "")).strip()
        if profile_class not in {"template", "example"}:
            errors.append(f"profile.class must be template or example, got: {profile_class or '<empty>'}")

        profile_mode = str(profile_task.get("mode", "")).strip()
        if not profile_mode:
            errors.append("profile task.mode is required")
        if configured_mode and profile_mode and configured_mode != profile_mode:
            errors.append(f"task.mode ({configured_mode}) does not match profile task.mode ({profile_mode})")

        if not str(profile_task.get("objective", "")).strip():
            warnings.append("profile task.objective is empty")
        profile_primary = str(profile_task.get("language", {}).get("primary", "")).strip()
        config_primary = str(configured_language.get("primary", "")).strip()
        placeholders = {"", "fill-by-human"}
        if config_primary not in placeholders and profile_primary not in placeholders and config_primary != profile_primary:
            warnings.append(
                f"task.language.primary ({config_primary}) differs from profile task.language.primary ({profile_primary})"
            )
        if profile_primary == "":
            warnings.append("profile task.language.primary is empty")

        required_inputs = profile_inputs.get("required", [])
        if not isinstance(required_inputs, list) or not required_inputs:
            warnings.append("profile inputs.required is empty or missing")
        if not isinstance(profile_execution, dict) or not profile_execution:
            warnings.append("profile execution section is empty or missing")

        commands = profile_verification.get("commands", [])
        if not isinstance(commands, list) or not commands:
            warnings.append("profile verification.commands is empty or missing")
        if not isinstance(profile_reporting.get("highlight", []), list) or not profile_reporting.get("highlight", []):
            warnings.append("profile reporting.highlight is empty or missing")

        return {
            "ok": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "profile_path": str(profile_path),
            "profile_name": profile_name,
            "profile_class": profile_class,
            "task_mode": profile_mode,
        }

    def validate_work_package(self) -> Dict[str, Any]:
        task = self.config.get("task", {})
        configured_mode = str(task.get("mode", "")).strip()
        errors: List[str] = []
        warnings: List[str] = []
        existing_required: List[str] = []
        missing_required: List[str] = []

        for relative_path in REQUIRED_WORK_FILES + REQUIRED_CORE_RULE_FILES:
            candidate = self.work_dir / relative_path
            if candidate.exists():
                existing_required.append(relative_path)
            else:
                missing_required.append(relative_path)

        if missing_required:
            errors.extend([f"missing required work file: {item}" for item in missing_required])

        available_modes: Dict[str, List[str]] = {}
        modes_root = self.work_dir / "rules" / "loopforge" / "modes"
        if modes_root.exists():
            for child in sorted(modes_root.iterdir()):
                if child.is_dir():
                    available_modes[child.name] = []
                    for relative_name in REQUIRED_MODE_RULE_FILES:
                        if (child / relative_name).exists():
                            available_modes[child.name].append(relative_name)

        if configured_mode:
            mode_dir = modes_root / configured_mode
            if not mode_dir.exists():
                errors.append(f"mode rule directory not found: rules/loopforge/modes/{configured_mode}")
            else:
                missing_mode_files = [
                    relative_name for relative_name in REQUIRED_MODE_RULE_FILES if not (mode_dir / relative_name).exists()
                ]
                if missing_mode_files:
                    errors.extend(
                        [
                            f"missing required mode rule: rules/loopforge/modes/{configured_mode}/{relative_name}"
                            for relative_name in missing_mode_files
                        ]
                    )

        templates_root = self.work_dir / "profiles" / "templates"
        examples_root = self.work_dir / "profiles" / "examples"
        template_count = len(list(templates_root.glob("*.yaml"))) if templates_root.exists() else 0
        example_count = len(list(examples_root.glob("*.yaml"))) if examples_root.exists() else 0
        if template_count < 5:
            warnings.append("profiles/templates contains fewer than 5 yaml templates")
        if example_count < 5:
            warnings.append("profiles/examples contains fewer than 5 yaml examples")

        return {
            "ok": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "required_files_present": existing_required,
            "required_files_missing": missing_required,
            "available_modes": available_modes,
            "configured_mode": configured_mode,
            "template_count": template_count,
            "example_count": example_count,
        }

    def validate_runtime_contract(self) -> Dict[str, Any]:
        platform = self.config.get("platform", {})
        task = self.config.get("task", {})
        execution = self.config.get("execution", {})
        outputs = self.config.get("outputs", {})
        verification = self.config.get("verification", {})
        errors: List[str] = []
        warnings: List[str] = []

        expected_work = (self.workspace_root / str(platform.get("work_dir", "work"))).resolve()
        expected_code = (self.workspace_root / str(platform.get("code_dir", "code"))).resolve()
        configured_mode = str(task.get("mode", "")).strip()
        allowed_modes = {
            "feature-development",
            "migration",
            "defect-repair",
            "consistency-check",
            "skill-generation",
        }

        if expected_work != self.work_dir:
            errors.append(f"platform.work_dir resolves to {expected_work}, but runner is using {self.work_dir}")
        if expected_code != self.code_dir:
            errors.append(f"platform.code_dir resolves to {expected_code}, but runner is using {self.code_dir}")
        if configured_mode not in allowed_modes:
            errors.append(f"task.mode must be one of {sorted(allowed_modes)}, got: {configured_mode or '<empty>'}")
        if execution.get("commit") is not False:
            errors.append("execution.commit must be false")
        if execution.get("push") is not False:
            errors.append("execution.push must be false")
        if execution.get("create_pr") is not False:
            errors.append("execution.create_pr must be false")
        if execution.get("allow_static_rule_modification") is not False:
            errors.append("execution.allow_static_rule_modification must be false")

        final_report = (self.workspace_root / str(outputs.get("final_report", "code/.loopforge/reports/final-report.md"))).resolve()
        snapshot_dir = (self.workspace_root / str(outputs.get("patch_snapshot_dir", "code/.loopforge/snapshots"))).resolve()
        if self.code_dir not in final_report.parents:
            errors.append("outputs.final_report must resolve under code/")
        if self.code_dir not in snapshot_dir.parents:
            errors.append("outputs.patch_snapshot_dir must resolve under code/")

        working_directory = str(verification.get("working_directory", "code")).strip()
        verification_cwd = (self.workspace_root / working_directory).resolve() if working_directory not in {"", "."} else self.workspace_root
        if verification_cwd != self.code_dir and self.code_dir not in verification_cwd.parents:
            errors.append("verification.working_directory must resolve to code/ or a descendant of code/")
        if not verification_cwd.exists():
            warnings.append(f"verification.working_directory does not exist yet: {verification_cwd}")

        commands = verification.get("commands", [])
        if not isinstance(commands, list) or not commands:
            errors.append("verification.commands must be a non-empty list")

        profile_summary = self.validate_profile()
        work_package_summary = self.validate_work_package()
        if not profile_summary.get("ok"):
            errors.extend([f"profile: {item}" for item in profile_summary.get("errors", [])])
        warnings.extend([f"profile: {item}" for item in profile_summary.get("warnings", [])])
        if not work_package_summary.get("ok"):
            errors.extend([f"work-package: {item}" for item in work_package_summary.get("errors", [])])
        warnings.extend([f"work-package: {item}" for item in work_package_summary.get("warnings", [])])

        return {
            "ok": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "platform": {
                "configured_work_dir": str(expected_work),
                "configured_code_dir": str(expected_code),
                "artifact_dir": str(self.artifact_dir),
            },
            "task": {
                "mode": configured_mode,
                "profile": task.get("profile", ""),
            },
            "verification": {
                "working_directory": str(verification_cwd),
                "commands_count": len(commands) if isinstance(commands, list) else 0,
            },
            "profile_summary": profile_summary,
            "work_package_summary": work_package_summary,
        }

    def record_gate(self, phase: str, status: str, action: str, reason: str) -> None:
        safe_action = " ".join(action.replace("|", "/").split())
        safe_reason = " ".join(reason.replace("|", "/").split())
        with self.gate_events_path.open("a", encoding="utf-8") as handle:
            handle.write(f"| {phase} | {status} | {safe_action} | {safe_reason} |\n")

    def init_workspace(self) -> Dict[str, Any]:
        self.assert_layout()
        self.ensure_directories()
        config_summary = self.validate_runtime_contract()
        self.save_json(self.config_check_path, config_summary)
        self.save_json(self.profile_check_path, config_summary.get("profile_summary", {}))
        self.save_json(self.package_check_path, config_summary.get("work_package_summary", {}))
        state = self.load_state()
        state["phase"] = "BOOTSTRAP"
        self.save_state(state)
        self.record_gate(
            "BOOTSTRAP",
            "PASS" if config_summary.get("ok") else "WARN",
            "initialize artifact tree",
            str(self.artifact_dir),
        )
        return {
            "ok": True,
            "artifact_dir": str(self.artifact_dir),
            "state_path": str(self.state_path),
            "contract_ok": config_summary.get("ok", False),
        }

    def self_check(self) -> Dict[str, Any]:
        self.assert_layout()
        self.ensure_directories()
        config_summary = self.validate_runtime_contract()
        self.save_json(self.config_check_path, config_summary)
        self.save_json(self.profile_check_path, config_summary.get("profile_summary", {}))
        self.save_json(self.package_check_path, config_summary.get("work_package_summary", {}))
        verification = self.config.get("verification", {})
        commands = verification.get("commands", [])
        checks = {
            "python_version": sys.version.split()[0],
            "workspace_root": str(self.workspace_root),
            "work_dir_exists": self.work_dir.exists(),
            "code_dir_exists": self.code_dir.exists(),
            "config_exists": self.config_path.exists(),
            "artifact_dir_target": str(self.artifact_dir),
            "artifact_dir_under_code": str(self.artifact_dir).startswith(str(self.code_dir)),
            "verification_commands_configured": isinstance(commands, list) and len(commands) > 0,
            "verification_working_directory": verification.get("working_directory", ""),
            "runner_copied": self.runtime_copy_path.exists(),
            "config_contract_ok": config_summary.get("ok", False),
            "profile_contract_ok": config_summary.get("profile_summary", {}).get("ok", False),
            "work_package_contract_ok": config_summary.get("work_package_summary", {}).get("ok", False),
        }
        ok = all(
            [
                checks["work_dir_exists"],
                checks["code_dir_exists"],
                checks["config_exists"],
                checks["artifact_dir_under_code"],
                checks["verification_commands_configured"],
                checks["config_contract_ok"],
                checks["profile_contract_ok"],
            ]
        )
        state = self.load_state()
        state["phase"] = "SELF_CHECK"
        self.save_state(state)
        self.record_gate("SELF_CHECK", "PASS" if ok else "WARN", "validate runtime contract", "self-check completed")
        return {
            "ok": ok,
            "checks": checks,
            "contract_summary": config_summary,
        }

    def detect_project(self) -> Dict[str, Any]:
        self.assert_layout()
        self.ensure_directories()
        git_probe = self.run_command("git rev-parse --is-inside-work-tree", self.code_dir, 30) if shutil.which("git") else None
        indicators = {
            "pom.xml": (self.code_dir / "pom.xml").exists(),
            "mvnw": (self.code_dir / "mvnw").exists() or (self.code_dir / "mvnw.cmd").exists(),
            "pyproject.toml": (self.code_dir / "pyproject.toml").exists(),
            "requirements.txt": (self.code_dir / "requirements.txt").exists(),
            "package.json": (self.code_dir / "package.json").exists(),
            "go.mod": (self.code_dir / "go.mod").exists(),
            "git_worktree": bool(git_probe and git_probe.returncode == 0 and git_probe.stdout.strip().lower() == "true"),
        }
        project_type = "unknown"
        if indicators["pom.xml"] or indicators["mvnw"]:
            project_type = "java-maven"
        elif indicators["pyproject.toml"] or indicators["requirements.txt"]:
            project_type = "python"
        elif indicators["package.json"]:
            project_type = "node"
        elif indicators["go.mod"]:
            project_type = "go"
        payload = {"project_type": project_type, "indicators": indicators}
        self.save_json(self.detect_path, payload)
        state = self.load_state()
        state["phase"] = "DETECT"
        state["project_type"] = project_type
        self.save_state(state)
        self.record_gate("DETECT", "PASS", "detect project shape", project_type)
        return payload

    def run_command(self, command: str, cwd: Path, timeout_seconds: int) -> CommandResult:
        try:
            completed = subprocess.run(
                command,
                cwd=str(cwd),
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            return CommandResult(
                command=command,
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        except subprocess.TimeoutExpired as exc:
            return CommandResult(
                command=command,
                returncode=124,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                error=f"timeout after {timeout_seconds}s",
            )
        except OSError as exc:
            return CommandResult(command=command, returncode=1, stdout="", stderr="", error=str(exc))

    def snapshot_diff(self, name: str) -> Dict[str, Any]:
        self.assert_layout()
        self.ensure_directories()
        snapshot_path = self.artifact_dir / "snapshots" / f"{name}.diff"
        if shutil.which("git") is None:
            snapshot_path.write_text("git not available; snapshot skipped\n", encoding="utf-8")
            self.record_gate("SNAPSHOT", "WARN", f"write {name}.diff", "git not available")
            return {"ok": False, "snapshot": str(snapshot_path), "reason": "git not available"}

        probe = self.run_command("git rev-parse --is-inside-work-tree", self.code_dir, 30)
        if probe.returncode != 0 or probe.stdout.strip().lower() != "true":
            snapshot_path.write_text("git work tree not detected; snapshot skipped\n", encoding="utf-8")
            self.record_gate("SNAPSHOT", "WARN", f"write {name}.diff", "code dir is not a git work tree")
            return {"ok": False, "snapshot": str(snapshot_path), "reason": "code dir is not a git work tree"}

        diff = self.run_command("git diff", self.code_dir, 60)
        content = diff.stdout
        if diff.error:
            content = f"git diff error: {diff.error}\n"
        elif diff.returncode != 0:
            detail = diff.stderr.strip() or f"exit={diff.returncode}"
            content = f"git diff failed: {detail}\n"
        snapshot_path.write_text(content, encoding="utf-8")
        self.record_gate("SNAPSHOT", "PASS" if diff.returncode == 0 and diff.error is None else "WARN", f"write {name}.diff", "snapshot completed")
        state = self.load_state()
        state["phase"] = "SNAPSHOT"
        self.save_state(state)
        return {"ok": diff.returncode == 0 and diff.error is None, "snapshot": str(snapshot_path)}

    def verification_context(self) -> Tuple[Path, int, List[str]]:
        verification = self.config.get("verification", {})
        commands = verification.get("commands", [])
        if not isinstance(commands, list) or not commands:
            raise ValueError("verification.commands is required and must be a non-empty list")
        working_directory = str(verification.get("working_directory", "code"))
        timeout_seconds = int(verification.get("timeout_seconds", 300))
        if working_directory in {".", ""}:
            cwd = self.workspace_root
        else:
            cwd = (self.workspace_root / working_directory).resolve()
        return cwd, timeout_seconds, [str(item) for item in commands]

    def verify(self) -> Dict[str, Any]:
        self.assert_layout()
        self.ensure_directories()
        config_summary = self.validate_runtime_contract()
        self.save_json(self.config_check_path, config_summary)
        self.save_json(self.profile_check_path, config_summary.get("profile_summary", {}))
        self.save_json(self.package_check_path, config_summary.get("work_package_summary", {}))
        if not config_summary.get("ok"):
            payload = {
                "ok": False,
                "status": "blocked-with-report",
                "reason": "runtime contract validation failed before verification",
                "contract_summary": config_summary,
            }
            self.save_json(self.verify_path, payload)
            state = self.load_state()
            state["phase"] = "VERIFY"
            state["result"] = "BLOCKED_WITH_REPORT"
            self.save_state(state)
            self.record_gate("VERIFY", "FAIL", "verification blocked", payload["reason"])
            return payload
        cwd, timeout_seconds, commands = self.verification_context()
        attempted: List[Dict[str, Any]] = []
        self.snapshot_diff("before-verify")
        state = self.load_state()
        state["phase"] = "VERIFY"
        self.save_state(state)

        for command in commands:
            result = self.run_command(command, cwd, timeout_seconds)
            attempted.append(
                {
                    "command": command,
                    "ok": result.returncode == 0 and result.error is None,
                    "returncode": result.returncode,
                    "stdout_tail": result.stdout.strip().splitlines()[-20:],
                    "stderr_tail": result.stderr.strip().splitlines()[-20:],
                    "error": result.error,
                }
            )
            if result.returncode == 0 and result.error is None:
                payload = {
                    "ok": True,
                    "status": "passed",
                    "working_directory": str(cwd),
                    "timeout_seconds": timeout_seconds,
                    "commands_attempted": attempted,
                    "selected_command": command,
                }
                self.save_json(self.verify_path, payload)
                state["result"] = "DONE"
                self.save_state(state)
                self.record_gate("VERIFY", "PASS", "verification succeeded", command)
                return payload

        payload = {
            "ok": False,
            "status": "blocked-with-report",
            "working_directory": str(cwd),
            "timeout_seconds": timeout_seconds,
            "commands_attempted": attempted,
            "reason": "all configured verification commands failed",
        }
        self.save_json(self.verify_path, payload)
        state["result"] = "BLOCKED_WITH_REPORT"
        self.save_state(state)
        self.record_gate("VERIFY", "FAIL", "verification failed", payload["reason"])
        return payload

    def finalize(self) -> Dict[str, Any]:
        self.assert_layout()
        self.ensure_directories()
        state = self.load_state()
        config_summary = self.validate_runtime_contract()
        self.save_json(self.config_check_path, config_summary)
        self.save_json(self.profile_check_path, config_summary.get("profile_summary", {}))
        self.save_json(self.package_check_path, config_summary.get("work_package_summary", {}))
        detect = self.load_json(self.detect_path)
        verification = self.load_json(self.verify_path)
        gate_lines = self.read_gate_events()
        gate_counts = self.gate_status_counts(gate_lines)
        profile_summary = config_summary.get("profile_summary", {})
        work_package_summary = config_summary.get("work_package_summary", {})
        mode_artifact_summary = (
            self.mode_artifact_summary_path.read_text(encoding="utf-8")
            if self.mode_artifact_summary_path.exists()
            else "No mode artifact summary was generated."
        )
        result_value = "PARTIAL_DONE"
        if verification.get("ok") is True:
            result_value = "DONE"
        elif verification:
            result_value = "BLOCKED_WITH_REPORT"
        elif not config_summary.get("ok"):
            result_value = "BLOCKED_WITH_REPORT"

        report_lines = [
            "# LoopForge Final Report",
            "",
            "## Result",
            "",
            result_value,
            "",
            "## Task",
            "",
            json.dumps(self.config.get("task", {}), indent=2, ensure_ascii=True),
            "",
            "## Mode And Profile",
            "",
            json.dumps(
                {
                    "mode": self.config.get("task", {}).get("mode", ""),
                    "profile": self.config.get("task", {}).get("profile", ""),
                    "profile_name": profile_summary.get("profile_name", ""),
                    "profile_class": profile_summary.get("profile_class", ""),
                },
                indent=2,
                ensure_ascii=True,
            ),
            "",
            "## Platform",
            "",
            json.dumps(self.config.get("platform", {}), indent=2, ensure_ascii=True),
            "",
            "## Detection",
            "",
            json.dumps(detect, indent=2, ensure_ascii=True) if detect else "No detection summary available.",
            "",
            "## Contract Validation",
            "",
            json.dumps(config_summary, indent=2, ensure_ascii=True),
            "",
            "## Contract Verdict",
            "",
            "PASS" if config_summary.get("ok") else "FAIL",
            "",
            "## Work Package Contract",
            "",
            json.dumps(work_package_summary, indent=2, ensure_ascii=True),
            "",
            "## Mode Artifact Summary",
            "",
            mode_artifact_summary,
            "",
            "## Verification",
            "",
            json.dumps(verification, indent=2, ensure_ascii=True) if verification else "No verification summary available.",
            "",
            "## Gate Summary",
            "",
            json.dumps(gate_counts, indent=2, ensure_ascii=True),
            "",
            "## Gate Events",
            "",
            *(gate_lines if gate_lines else ["No gate events recorded."]),
            "",
            "## Artifact Location",
            "",
            f"- `{self.artifact_dir}`",
            "",
            "## Key Artifacts",
            "",
            *[f"- `{path}`" for path in self.artifact_summary()],
            "",
            "## Boundaries",
            "",
            "- Static files under work/ are read-only during execution.",
            "- Code changes are allowed only inside code/.",
            "- Runtime artifacts are written only under code/.loopforge/.",
            "- LoopForge does not commit, push, create PRs, or submit results.",
            "",
        ]
        self.final_report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
        state["phase"] = "FINALIZE"
        state["result"] = result_value
        self.save_state(state)
        self.record_gate("FINALIZE", "PASS", "write final report", str(self.final_report_path))
        return {"ok": True, "report": str(self.final_report_path), "result": result_value}


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LoopForge runner")
    parser.add_argument("--work-dir", default="work", help="path to the LoopForge work directory")
    parser.add_argument("--code-dir", default="code", help="path to the target code directory")
    parser.add_argument("--init", action="store_true", help="initialize code/.loopforge")
    parser.add_argument("--self-check", action="store_true", help="validate runtime and configuration")
    parser.add_argument("--detect", action="store_true", help="detect target project shape")
    parser.add_argument("--snapshot", metavar="NAME", help="write a git diff snapshot into code/.loopforge/snapshots")
    parser.add_argument("--verify", action="store_true", help="run configured verification.commands")
    parser.add_argument("--finalize", action="store_true", help="write code/.loopforge/reports/final-report.md")
    return parser.parse_args(argv)


def print_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True))


def resolve_workspace_root(cwd: Path, work_arg: str, code_arg: str) -> Path:
    work_path = Path(work_arg)
    code_path = Path(code_arg)
    if not work_path.is_absolute():
        work_path = (cwd / work_path).resolve()
    else:
        work_path = work_path.resolve()
    if not code_path.is_absolute():
        code_path = (cwd / code_path).resolve()
    else:
        code_path = code_path.resolve()

    if work_path == code_path:
        raise ValueError("work_dir and code_dir must be different paths")

    common_parent = Path(os.path.commonpath([str(work_path), str(code_path)]))
    if common_parent == work_path or common_parent == code_path:
        raise ValueError("work/ and code/ must be isolated sibling trees")
    return common_parent


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    if not any([args.init, args.self_check, args.detect, args.snapshot, args.verify, args.finalize]):
        print("No action provided.", file=sys.stderr)
        return 2

    try:
        workspace_root = resolve_workspace_root(Path.cwd().resolve(), args.work_dir, args.code_dir)
        work_dir = Path(args.work_dir)
        code_dir = Path(args.code_dir)
        if not work_dir.is_absolute():
            work_dir = (Path.cwd().resolve() / work_dir).resolve()
        else:
            work_dir = work_dir.resolve()
        if not code_dir.is_absolute():
            code_dir = (Path.cwd().resolve() / code_dir).resolve()
        else:
            code_dir = code_dir.resolve()
        runner = LoopForgeRunner(workspace_root, work_dir, code_dir)

        if args.init:
            print_json(runner.init_workspace())
        if args.self_check:
            print_json(runner.self_check())
        if args.detect:
            print_json(runner.detect_project())
        if args.snapshot:
            print_json(runner.snapshot_diff(args.snapshot))
        if args.verify:
            print_json(runner.verify())
        if args.finalize:
            print_json(runner.finalize())
    except Exception as exc:
        print_json({"ok": False, "error": str(exc)})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
