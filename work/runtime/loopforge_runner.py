#!/usr/bin/env python3
"""LoopForge runner for the contest layout with framework assets under work/."""

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
    "consistency",
]
README_CANDIDATES = [
    "README.md",
    "README",
    "readme.md",
    "Readme.md",
]
REQUIRED_ROOT_FILES = [
    "INSTRUCTION.md",
    "README.md",
    "SUBMISSION.md",
]
REQUIRED_WORK_FILES = [
    "loopforge.config.yaml",
    "HARNESS.md",
    "runtime/loopforge_runner.py",
    "scripts/bootstrap.sh",
    "scripts/bootstrap.ps1",
    "scripts/smoke-test.sh",
    "scripts/smoke-test.ps1",
    "skills/loopforge-driver/SKILL.md",
    "docs/DESIGN.md",
    "docs/ADAPTATION_GUIDE.md",
    "docs/CROSS_PLATFORM_DESIGN.md",
    "docs/DAILY_DEV_USAGE.md",
    "profiles/README.md",
]
REQUIRED_SUBAGENT_FILES = [
    "subagent/opencode-preflight-subagent.md",
    "subagent/opencode-design-read-subagent.md",
    "subagent/opencode-implementation-map-subagent.md",
    "subagent/opencode-drift-analysis-subagent.md",
    "subagent/opencode-repair-plan-subagent.md",
    "subagent/opencode-patch-subagent.md",
    "subagent/opencode-verification-subagent.md",
    "subagent/opencode-final-report-subagent.md",
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


def detect_os() -> str:
    system = platform.system().lower()
    if system.startswith("windows"):
        return "windows"
    if system.startswith("linux"):
        return "linux"
    if system.startswith("darwin"):
        return "macos"
    return "unknown"


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
    def __init__(
        self,
        workspace_root: Path,
        work_dir: Path,
        code_dir: Path,
        source_root: Optional[Path] = None,
        result_dir: Optional[Path] = None,
        log_dir: Optional[Path] = None,
    ) -> None:
        self.workspace_root = workspace_root.resolve()
        self.work_dir = work_dir.resolve()
        self.code_dir = code_dir.resolve()
        self.source_root = self.code_dir if source_root is None else source_root.resolve()
        self.result_dir = (self.workspace_root / "result").resolve() if result_dir is None else result_dir.resolve()
        self.log_dir = (self.workspace_root / "logs").resolve() if log_dir is None else log_dir.resolve()
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
        self.consistency_dir = self.artifact_dir / "consistency"
        self.final_report_path = self.artifact_dir / "reports" / "final-report.md"
        self.gate_events_path = self.artifact_dir / "gates" / "gate-events.md"
        self.result_output_path = self.result_dir / "output.md"
        self.result_issue_summary_path = self.result_dir / "issues" / "00-summary.md"
        self.log_trace_dir = self.log_dir / "trace"
        self.interaction_log_path = self.log_dir / "interaction.md"
        self.run_trace_path = self.log_trace_dir / "run-summary.json"
        self.current_os = detect_os()

    def resolve_code_relative_path(self, configured_path: str) -> Path:
        normalized = configured_path.replace("\\", "/").strip()
        if normalized in {"", "."}:
            return self.workspace_root
        if normalized == "code":
            return self.code_dir
        if normalized.startswith("code/"):
            return (self.code_dir / normalized[5:]).resolve()
        return (self.workspace_root / configured_path).resolve()

    def ensure_entrypoint_outputs(self) -> None:
        self.result_dir.mkdir(parents=True, exist_ok=True)
        (self.result_dir / "issues").mkdir(parents=True, exist_ok=True)
        self.log_trace_dir.mkdir(parents=True, exist_ok=True)
        if not self.interaction_log_path.exists():
            self.interaction_log_path.write_text("# Interaction Log\n\nNo manual interaction.\n", encoding="utf-8")

    def ensure_directories(self) -> None:
        self.ensure_entrypoint_outputs()
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
        if self.code_dir == self.work_dir:
            raise ValueError("code_dir must be different from work_dir")
        if self.work_dir.parent != self.workspace_root:
            raise ValueError("work_dir must resolve as the framework directory under the repository root")
        if self.code_dir == self.workspace_root or self.workspace_root in self.code_dir.parents:
            if self.code_dir.parent != self.workspace_root:
                raise ValueError("local fallback code_dir must resolve as a direct child of the repository root")
        platform = self.config.get("platform", {})
        if platform.get("layout") != "single-root":
            raise ValueError("unsupported platform.layout; expected single-root")
        if self.artifact_dir == self.code_dir or self.code_dir not in self.artifact_dir.parents:
            raise ValueError("artifact_dir must resolve under code/")
        forbidden_roots = ["skills", "rules", "runtime", "scripts", "profiles"]
        for name in forbidden_roots:
            candidate = (self.work_dir / name).resolve()
            if self.artifact_dir == candidate or candidate in self.artifact_dir.parents:
                raise ValueError(f"artifact_dir must not resolve under {name}/")

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

    def detect_source_readme(self) -> Dict[str, Any]:
        candidates: List[str] = []
        for name in README_CANDIDATES:
            candidate = self.code_dir / name
            candidates.append(str(candidate))
            if candidate.exists():
                return {
                    "found": True,
                    "selected_path": str(candidate),
                    "candidates": candidates,
                }
        return {
            "found": False,
            "selected_path": "",
            "candidates": candidates,
        }

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
            errors.append("task.profile must resolve under the LoopForge root")
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
        placeholders = {"", "source-root-derived"}
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
        verification_strategy = str(profile_verification.get("strategy", "")).strip()
        if not isinstance(commands, list):
            warnings.append("profile verification.commands is not a list")
        elif not commands and verification_strategy not in {"source-readme-or-framework-default", "source-readme"}:
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

        for relative_path in REQUIRED_ROOT_FILES:
            candidate = self.workspace_root / relative_path
            if candidate.exists():
                existing_required.append(relative_path)
            else:
                missing_required.append(relative_path)

        for relative_path in REQUIRED_WORK_FILES + REQUIRED_SUBAGENT_FILES + REQUIRED_CORE_RULE_FILES:
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
        governance = self.config.get("governance", {})
        coding_skill = self.config.get("coding_skill", {})
        outputs = self.config.get("outputs", {})
        verification = self.config.get("verification", {})
        errors: List[str] = []
        warnings: List[str] = []

        configured_work_dir = str(platform.get("work_dir", ".")).strip() or "."
        configured_code_dir = str(platform.get("code_dir", "code")).strip() or "code"
        expected_work = (self.workspace_root / configured_work_dir).resolve()
        expected_code = self.resolve_code_relative_path(configured_code_dir)
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
        if expected_code != self.code_dir and self.code_dir == (self.workspace_root / configured_code_dir).resolve():
            errors.append(f"platform.code_dir resolves to {expected_code}, but runner is using {self.code_dir}")
        elif expected_code != self.code_dir and self.code_dir != (self.workspace_root / configured_code_dir).resolve():
            warnings.append(f"platform.code_dir default is {expected_code}, overridden source root is {self.code_dir}")
        if str(platform.get("official_submission_os", "")).strip() != "linux":
            errors.append("platform.official_submission_os must be linux")
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

        execution_model = str(execution.get("execution_model", "")).strip()
        if configured_mode == "consistency-check" and execution_model:
            if execution_model != "delegated-staged":
                errors.append("execution.execution_model must be delegated-staged for consistency-check")
            if execution.get("human_intervention_allowed") is not False:
                errors.append("execution.human_intervention_allowed must be false for delegated-staged runs")
            if execution.get("manual_stage_prompt_allowed") is not False:
                errors.append("execution.manual_stage_prompt_allowed must be false for delegated-staged runs")
            if execution.get("monolithic_context_forbidden") is not True:
                errors.append("execution.monolithic_context_forbidden must be true for delegated-staged runs")
            if execution.get("file_handoff_required") is not True:
                errors.append("execution.file_handoff_required must be true for delegated-staged runs")

            governance_summary = self.validate_governance_contract(governance)
            if not governance_summary.get("ok"):
                errors.extend(governance_summary.get("errors", []))
            warnings.extend(governance_summary.get("warnings", []))
            subagent_contract_summary = self.validate_subagent_contract(governance, str(task.get("profile", "")).strip())
            if not subagent_contract_summary.get("ok"):
                errors.extend(subagent_contract_summary.get("errors", []))
            warnings.extend(subagent_contract_summary.get("warnings", []))
        else:
            governance_summary = {
                "ok": True,
                "superspec": "",
                "superpower": "",
                "mode_rules": [],
                "delegated_staged_ready": False,
            }
            subagent_contract_summary = {
                "ok": True,
                "errors": [],
                "warnings": [],
                "stage_count": 0,
                "stages": [],
            }

        final_report = self.resolve_code_relative_path(str(outputs.get("final_report", "code/.loopforge/reports/final-report.md")))
        snapshot_dir = self.resolve_code_relative_path(str(outputs.get("patch_snapshot_dir", "code/.loopforge/snapshots")))
        consistency_dir = self.resolve_code_relative_path(str(outputs.get("consistency_dir", "code/.loopforge/consistency")))
        if self.code_dir not in final_report.parents:
            errors.append("outputs.final_report must resolve under code/")
        if self.code_dir not in snapshot_dir.parents:
            errors.append("outputs.patch_snapshot_dir must resolve under code/")
        if self.code_dir not in consistency_dir.parents:
            errors.append("outputs.consistency_dir must resolve under code/")

        coding_skill_summary = self.validate_coding_skill_contract(coding_skill, governance, consistency_dir)
        if not coding_skill_summary.get("ok"):
            errors.extend(coding_skill_summary.get("errors", []))
        warnings.extend(coding_skill_summary.get("warnings", []))

        working_directory = str(verification.get("working_directory", "code")).strip()
        verification_cwd = self.resolve_code_relative_path(working_directory) if working_directory not in {"", "."} else self.work_dir
        if verification_cwd != self.code_dir and self.code_dir not in verification_cwd.parents:
            errors.append("verification.working_directory must resolve to code/ or a descendant of code/")
        if not verification_cwd.exists():
            warnings.append(f"verification.working_directory does not exist yet: {verification_cwd}")

        commands_summary = self.normalize_verification_commands(verification.get("commands", []))
        if not commands_summary["ok"]:
            errors.extend(commands_summary["errors"])
        warnings.extend(commands_summary["warnings"])

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
                "commands_format": commands_summary["format"],
                "available_profiles": commands_summary["available_profiles"],
                "selected_profile": commands_summary["selected_profile"],
                "fallback_used": commands_summary["fallback_used"],
                "commands_count": commands_summary["selected_count"],
            },
            "governance": governance_summary,
            "subagent_contract": subagent_contract_summary,
            "coding_skill": coding_skill_summary,
            "outputs": {
                "consistency_dir": str(consistency_dir),
                "final_report": str(final_report),
                "patch_snapshot_dir": str(snapshot_dir),
            },
            "profile_summary": profile_summary,
            "work_package_summary": work_package_summary,
        }

    def validate_coding_skill_contract(
        self, coding_skill: Dict[str, Any], governance: Dict[str, Any], consistency_dir: Path
    ) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []

        enabled = coding_skill.get("enabled")
        required = coding_skill.get("required")
        skill_path_value = str(coding_skill.get("skill", "")).strip()
        apply_at = coding_skill.get("apply_at", [])
        output_value = str(coding_skill.get("output", "")).strip()
        skill_path = (self.work_dir / skill_path_value).resolve() if skill_path_value else None
        output_path = self.resolve_code_relative_path(output_value) if output_value else None

        references_ready = False
        stage_declared = False
        superpower_policy_ready = False

        if enabled is not True:
            errors.append("coding_skill.enabled must be true")
        if required is not True:
            errors.append("coding_skill.required must be true")
        if skill_path_value != "skills/code-implementation/SKILL.md":
            errors.append("coding_skill.skill must be skills/code-implementation/SKILL.md")
        if not isinstance(apply_at, list) or "patch_implementation" not in [str(item) for item in apply_at]:
            errors.append("coding_skill.apply_at must include patch_implementation")
        if output_value != "code/.loopforge/consistency/05-patch-summary.md":
            errors.append("coding_skill.output must be code/.loopforge/consistency/05-patch-summary.md")
        if output_path is None:
            errors.append("coding_skill.output is required")
        elif output_path != consistency_dir / "05-patch-summary.md":
            errors.append("coding_skill.output must match outputs.consistency_dir/05-patch-summary.md")

        if skill_path is None or not skill_path.exists():
            errors.append("CODING_SKILL_MISSING: coding skill file not found")
        else:
            references_dir = skill_path.parent / "references"
            references_ready = references_dir.exists()
            if not references_ready:
                errors.append("CODING_SKILL_MISSING: coding skill references directory not found")
            else:
                for name in (
                    "java-secure-coding.md",
                    "minimal-patch-rules.md",
                    "patch-summary-template.md",
                ):
                    if not (references_dir / name).exists():
                        errors.append(f"CODING_SKILL_MISSING: coding skill reference not found: {name}")

        superspec_value = str(governance.get("superspec", "")).strip()
        if superspec_value:
            superspec_path = (self.work_dir / superspec_value).resolve()
            if superspec_path.exists():
                superspec_text = superspec_path.read_text(encoding="utf-8")
                stage_declared = 'skill: "skills/code-implementation/SKILL.md"' in superspec_text
                if not stage_declared:
                    errors.append("CODING_SKILL_MISSING: 05-patch stage must declare skills/code-implementation/SKILL.md")
            else:
                warnings.append("cannot validate coding skill stage declaration because superspec file is missing")

        superpower_value = str(governance.get("superpower", "")).strip()
        if superpower_value:
            superpower_path = (self.work_dir / superpower_value).resolve()
            if superpower_path.exists():
                superpower_text = superpower_path.read_text(encoding="utf-8")
                superpower_policy_ready = (
                    "coding_skill_policy:" in superpower_text
                    and 'skill: "skills/code-implementation/SKILL.md"' in superpower_text
                )
                if not superpower_policy_ready:
                    errors.append(
                        "CODING_SKILL_MISSING: superpower must declare coding_skill_policy for skills/code-implementation/SKILL.md"
                    )
            else:
                warnings.append("cannot validate coding skill policy because superpower file is missing")

        return {
            "ok": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "enabled": enabled is True,
            "required": required is True,
            "skill": skill_path_value,
            "apply_at": [str(item) for item in apply_at] if isinstance(apply_at, list) else [],
            "output": output_value,
            "ready_status": "CODING_SKILL_READY" if len(errors) == 0 else "CODING_SKILL_MISSING",
            "skill_exists": bool(skill_path and skill_path.exists()),
            "references_ready": references_ready,
            "stage_declared": stage_declared,
            "superpower_policy_ready": superpower_policy_ready,
        }

    def validate_governance_contract(self, governance: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []

        superspec = str(governance.get("superspec", "")).strip()
        superpower = str(governance.get("superpower", "")).strip()
        mode_rules = governance.get("mode_rules", [])

        if not superspec:
            errors.append("BLOCKED_CONFIG_MISSING_GOVERNANCE: governance.superspec is required")
        if not superpower:
            errors.append("BLOCKED_CONFIG_MISSING_GOVERNANCE: governance.superpower is required")
        if not isinstance(mode_rules, list) or not mode_rules:
            errors.append("BLOCKED_CONFIG_MISSING_GOVERNANCE: governance.mode_rules must be a non-empty list")

        resolved_rules: List[str] = []
        for relative_path in mode_rules if isinstance(mode_rules, list) else []:
            resolved = (self.work_dir / str(relative_path)).resolve()
            resolved_rules.append(str(resolved))
            if not resolved.exists():
                errors.append(f"BLOCKED_CONFIG_MISSING_GOVERNANCE: mode rule file not found: {relative_path}")

        if superspec:
            superspec_path = (self.work_dir / superspec).resolve()
            if not superspec_path.exists():
                errors.append(f"BLOCKED_CONFIG_MISSING_GOVERNANCE: superspec file not found: {superspec}")
        if superpower:
            superpower_path = (self.work_dir / superpower).resolve()
            if not superpower_path.exists():
                errors.append(f"BLOCKED_CONFIG_MISSING_GOVERNANCE: superpower file not found: {superpower}")

        return {
            "ok": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "superspec": superspec,
            "superpower": superpower,
            "mode_rules": resolved_rules,
            "delegated_staged_ready": len(errors) == 0,
        }

    def strip_yaml_scalar(self, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'"}:
            return cleaned[1:-1]
        return cleaned

    def parse_superspec_stage_contracts(self, superspec_path: Path) -> List[Dict[str, str]]:
        stages: List[Dict[str, str]] = []
        current: Optional[Dict[str, str]] = None
        for raw in superspec_path.read_text(encoding="utf-8").splitlines():
            stripped = raw.strip()
            if stripped.startswith("- id:"):
                if current is not None:
                    stages.append(current)
                current = {"id": self.strip_yaml_scalar(stripped.split(":", 1)[1])}
                continue
            if current is None:
                continue
            for key in (
                "name",
                "subagent",
                "output",
                "success_gate",
                "degraded_gate",
                "failure_gate",
                "blocked_gate",
                "parent_direct_execution_allowed",
            ):
                prefix = f"{key}:"
                if stripped.startswith(prefix):
                    current[key] = self.strip_yaml_scalar(stripped.split(":", 1)[1])
                    break
        if current is not None:
            stages.append(current)
        return stages

    def validate_subagent_contract(self, governance: Dict[str, Any], profile_value: str) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []
        banned_phrases = [
            "if subagents are available",
            "subagent preferred",
            "emulate staged workers",
            "fallback to main context",
            "continue in main context",
        ]

        instruction_text = (self.workspace_root / "INSTRUCTION.md").read_text(encoding="utf-8")
        skill_text = (self.work_dir / "skills" / "loopforge-driver" / "SKILL.md").read_text(encoding="utf-8")
        superpower_path = (self.work_dir / str(governance.get("superpower", ""))).resolve()
        superspec_path = (self.work_dir / str(governance.get("superspec", ""))).resolve()
        profile_path = (self.work_dir / profile_value).resolve() if profile_value else None
        delegated_rule_path = self.work_dir / "rules" / "loopforge" / "modes" / "consistency-check" / "delegated-execution.md"
        artifact_rule_path = self.work_dir / "rules" / "loopforge" / "modes" / "consistency-check" / "02-required-artifacts.md"
        final_report_rule_path = self.work_dir / "rules" / "loopforge" / "core" / "05-final-report.md"

        for phrase in banned_phrases:
            if phrase in instruction_text.lower():
                errors.append(f"BANNED_SUBAGENT_FALLBACK: INSTRUCTION.md contains {phrase!r}")
            if phrase in skill_text.lower():
                errors.append(f"BANNED_SUBAGENT_FALLBACK: skills/loopforge-driver/SKILL.md contains {phrase!r}")

        if "required subagent unavailable" not in instruction_text:
            errors.append("SUBAGENT_REQUIRED_CONTRACT_MISSING: INSTRUCTION.md must block on required subagent unavailable")
        if "required subagent unavailable" not in skill_text:
            errors.append("SUBAGENT_REQUIRED_CONTRACT_MISSING: skills/loopforge-driver/SKILL.md must block on required subagent unavailable")

        if not superpower_path.exists():
            errors.append("SUBAGENT_REQUIRED_CONTRACT_MISSING: superpower file not found")
            superpower_text = ""
        else:
            superpower_text = superpower_path.read_text(encoding="utf-8")
        for required_literal in (
            "subagent_required: true",
            "fallback_to_main_context_allowed: false",
            'missing_subagent_policy: "BLOCKED_WITH_REPORT"',
            "parent_direct_execution_allowed: false",
            "file_handoff_required: true",
        ):
            if required_literal not in superpower_text:
                errors.append(f"SUBAGENT_REQUIRED_CONTRACT_MISSING: superpower missing {required_literal}")

        profile_text = ""
        if profile_path is not None and profile_path.exists():
            profile_text = profile_path.read_text(encoding="utf-8")
            for required_literal in (
                "subagent_required: true",
                "fallback_to_main_context_allowed: false",
                'missing_subagent_policy: "BLOCKED_WITH_REPORT"',
                "parent_direct_execution_allowed: false",
                "file_handoff_required: true",
            ):
                if required_literal not in profile_text:
                    errors.append(f"SUBAGENT_REQUIRED_CONTRACT_MISSING: profile missing {required_literal}")
        elif profile_value:
            warnings.append(f"profile file unavailable for subagent contract validation: {profile_value}")

        if not delegated_rule_path.exists():
            errors.append("SUBAGENT_REQUIRED_CONTRACT_MISSING: delegated execution rule not found")
        else:
            delegated_rule_text = delegated_rule_path.read_text(encoding="utf-8")
            if "required subagent unavailable" not in delegated_rule_text:
                errors.append("SUBAGENT_REQUIRED_CONTRACT_MISSING: delegated execution rule must block on required subagent unavailable")
            if "executed_by_subagent" not in delegated_rule_text:
                errors.append("SUBAGENT_REQUIRED_CONTRACT_MISSING: delegated execution rule must require stage artifact subagent metadata")

        if not artifact_rule_path.exists():
            errors.append("SUBAGENT_REQUIRED_CONTRACT_MISSING: required artifacts rule not found")
        else:
            artifact_rule_text = artifact_rule_path.read_text(encoding="utf-8")
            for required_literal in ("executed_by_subagent", "parent_direct_execution: false"):
                if required_literal not in artifact_rule_text:
                    errors.append(f"SUBAGENT_REQUIRED_CONTRACT_MISSING: required artifacts rule missing {required_literal}")

        if not final_report_rule_path.exists():
            errors.append("SUBAGENT_REQUIRED_CONTRACT_MISSING: final report rule not found")
        else:
            final_report_rule_text = final_report_rule_path.read_text(encoding="utf-8")
            if "## Subagent Execution Evidence" not in final_report_rule_text:
                errors.append("SUBAGENT_REQUIRED_CONTRACT_MISSING: final report rule must require Subagent Execution Evidence")

        stage_contracts: List[Dict[str, str]] = []
        available_subagent_files = {path.stem for path in (self.work_dir / "subagent").glob("*.md")} if (self.work_dir / "subagent").exists() else set()
        if not superspec_path.exists():
            errors.append("SUBAGENT_REQUIRED_CONTRACT_MISSING: superspec file not found")
        else:
            superspec_text = superspec_path.read_text(encoding="utf-8")
            for required_literal in (
                "subagent_required: true",
                "fallback_to_main_context_allowed: false",
                'missing_subagent_policy: "BLOCKED_WITH_REPORT"',
                "parent_direct_execution_allowed: false",
                "file_handoff_required: true",
            ):
                if required_literal not in superspec_text:
                    errors.append(f"SUBAGENT_REQUIRED_CONTRACT_MISSING: superspec missing {required_literal}")
            stage_contracts = self.parse_superspec_stage_contracts(superspec_path)
            if not stage_contracts:
                errors.append("SUBAGENT_REQUIRED_CONTRACT_MISSING: superspec must declare stages")
            for stage in stage_contracts:
                stage_id = stage.get("id", "<unknown>")
                if not stage.get("subagent"):
                    errors.append(f"SUBAGENT_REQUIRED_CONTRACT_MISSING: stage {stage_id} missing subagent")
                elif stage["subagent"] not in available_subagent_files:
                    errors.append(
                        f"SUBAGENT_REQUIRED_CONTRACT_MISSING: missing subagent definition file: subagent/{stage['subagent']}.md"
                    )
                if not stage.get("output"):
                    errors.append(f"SUBAGENT_REQUIRED_CONTRACT_MISSING: stage {stage_id} missing output artifact")
                if stage.get("parent_direct_execution_allowed") != "false":
                    errors.append(
                        f"SUBAGENT_REQUIRED_CONTRACT_MISSING: stage {stage_id} must set parent_direct_execution_allowed: false"
                    )
                if not (stage.get("failure_gate") == "BLOCKED_WITH_REPORT" or stage.get("blocked_gate") == "BLOCKED_WITH_REPORT"):
                    errors.append(f"SUBAGENT_REQUIRED_CONTRACT_MISSING: stage {stage_id} must block with BLOCKED_WITH_REPORT")

        return {
            "ok": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "stage_count": len(stage_contracts),
            "stages": stage_contracts,
        }

    def read_stage_artifact_metadata(self, artifact_path: Path) -> Dict[str, str]:
        metadata: Dict[str, str] = {}
        if not artifact_path.exists():
            return metadata
        for raw in artifact_path.read_text(encoding="utf-8").splitlines():
            stripped = raw.strip()
            if ":" not in stripped:
                continue
            key, value = stripped.split(":", 1)
            key = key.strip()
            if key in {
                "stage_id",
                "executed_by_subagent",
                "parent_direct_execution",
                "output_artifact",
                "gate",
                "summary",
                "next_stage",
            }:
                metadata[key] = self.strip_yaml_scalar(value)
        return metadata

    def normalize_verification_commands(self, raw_commands: Any) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []
        available_profiles: List[str] = []
        selected_profile = ""
        fallback_used = False
        selected_commands: List[str] = []
        command_format = "invalid"

        if isinstance(raw_commands, list):
            command_format = "legacy-list"
            selected_commands = [str(item) for item in raw_commands if str(item).strip()]
            available_profiles = ["default"] if selected_commands else []
            selected_profile = "default" if selected_commands else ""
        elif isinstance(raw_commands, dict):
            command_format = "platform-map"
            available_profiles = [str(key) for key, value in raw_commands.items() if isinstance(value, list) and value]
            preferred = raw_commands.get(self.current_os)
            if isinstance(preferred, list):
                selected_commands = [str(item) for item in preferred if str(item).strip()]
                if selected_commands:
                    selected_profile = self.current_os
            if not selected_commands:
                default_commands = raw_commands.get("default")
                if isinstance(default_commands, list):
                    selected_commands = [str(item) for item in default_commands if str(item).strip()]
                    if selected_commands:
                        selected_profile = "default"
                        fallback_used = self.current_os != "default"
        else:
            errors.append("verification.commands must be a list or a platform command map")

        return {
            "ok": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "format": command_format,
            "available_profiles": available_profiles,
            "selected_profile": selected_profile,
            "fallback_used": fallback_used,
            "selected_count": len(selected_commands),
            "selected_commands": selected_commands,
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
        commands_summary = self.normalize_verification_commands(verification.get("commands", []))
        checks = {
            "python_version": sys.version.split()[0],
            "workspace_root": str(self.workspace_root),
            "work_dir_exists": self.work_dir.exists(),
            "code_dir_exists": self.code_dir.exists(),
            "config_exists": self.config_path.exists(),
            "artifact_dir_target": str(self.artifact_dir),
            "artifact_dir_under_code": str(self.artifact_dir).startswith(str(self.code_dir)),
            "verification_commands_configured": commands_summary["selected_count"] > 0,
            "verification_working_directory": verification.get("working_directory", ""),
            "runner_copied": self.runtime_copy_path.exists(),
            "config_contract_ok": config_summary.get("ok", False),
            "profile_contract_ok": config_summary.get("profile_summary", {}).get("ok", False),
            "work_package_contract_ok": config_summary.get("work_package_summary", {}).get("ok", False),
            "coding_skill_status": config_summary.get("coding_skill", {}).get("ready_status", "CODING_SKILL_MISSING"),
            "coding_skill_contract_ok": config_summary.get("coding_skill", {}).get("ok", False),
            "source_readme_found": self.detect_source_readme().get("found", False),
        }
        ok = all(
            [
                checks["work_dir_exists"],
                checks["code_dir_exists"],
                checks["config_exists"],
                checks["artifact_dir_under_code"],
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
        readme_summary = self.detect_source_readme()
        indicators = {
            "pom.xml": (self.code_dir / "pom.xml").exists(),
            "mvnw": (self.code_dir / "mvnw").exists() or (self.code_dir / "mvnw.cmd").exists(),
            "pyproject.toml": (self.code_dir / "pyproject.toml").exists(),
            "requirements.txt": (self.code_dir / "requirements.txt").exists(),
            "package.json": (self.code_dir / "package.json").exists(),
            "go.mod": (self.code_dir / "go.mod").exists(),
            "git_worktree": bool(git_probe and git_probe.returncode == 0 and git_probe.stdout.strip().lower() == "true"),
            "source_readme": readme_summary["found"],
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
        payload = {
            "project_type": project_type,
            "indicators": indicators,
            "source_readme": readme_summary,
        }
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
        normalized = self.normalize_verification_commands(verification.get("commands", []))
        if normalized["errors"]:
            raise ValueError("; ".join(str(item) for item in normalized["errors"]))
        working_directory = str(verification.get("working_directory", "code"))
        timeout_seconds = int(verification.get("timeout_seconds", 300))
        if working_directory in {".", ""}:
            cwd = self.work_dir
        else:
            cwd = self.resolve_code_relative_path(working_directory)
        return cwd, timeout_seconds, [str(item) for item in normalized["selected_commands"]]

    def write_entrypoint_result(
        self,
        verify_payload: Dict[str, Any],
        finalize_payload: Dict[str, Any],
        self_check_payload: Dict[str, Any],
        detect_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        self.ensure_entrypoint_outputs()
        lines = [
            "# Output",
            "",
            f"- source_root: `{self.source_root}`",
            f"- resolved_code_dir: `{self.code_dir}`",
            f"- artifact_dir: `{self.artifact_dir}`",
            f"- result: `{finalize_payload.get('result', 'UNKNOWN')}`",
            f"- verification_status: `{verify_payload.get('status', 'not-run')}`",
            f"- selected_source_readme: `{detect_payload.get('source_readme', {}).get('selected_path', '') or 'missing'}`",
            f"- final_report: `{self.final_report_path}`",
            "",
            "## Self Check",
            "",
            json.dumps(self_check_payload, indent=2, ensure_ascii=True),
            "",
            "## Detection",
            "",
            json.dumps(detect_payload, indent=2, ensure_ascii=True),
            "",
            "## Verification",
            "",
            json.dumps(verify_payload, indent=2, ensure_ascii=True),
            "",
        ]
        self.result_output_path.write_text("\n".join(lines), encoding="utf-8")

        issues_text = "# Issues Summary\n\n"
        if verify_payload.get("ok") is True and self_check_payload.get("ok") is True:
            issues_text += "No execution issues recorded.\n"
        else:
            issues: List[str] = []
            contract_summary = self_check_payload.get("contract_summary", {})
            if isinstance(contract_summary, dict):
                issues.extend(str(item) for item in contract_summary.get("errors", []))
            if verify_payload.get("reason"):
                issues.append(str(verify_payload["reason"]))
            source_readme = detect_payload.get("source_readme", {}) if isinstance(detect_payload, dict) else {}
            if isinstance(source_readme, dict) and not source_readme.get("found", False):
                issues.append("source README not found near SOURCE_ROOT")
            if not issues:
                issues.append("Execution completed with non-passing status. See result/output.md and logs/trace/run-summary.json.")
            issues_text += "\n".join(f"- {item}" for item in issues) + "\n"
        self.result_issue_summary_path.write_text(issues_text, encoding="utf-8")

        trace_payload = {
            "source_root": str(self.source_root),
            "code_dir": str(self.code_dir),
            "artifact_dir": str(self.artifact_dir),
            "result_dir": str(self.result_dir),
            "log_dir": str(self.log_dir),
            "self_check": self_check_payload,
            "detect": detect_payload,
            "verify": verify_payload,
            "finalize": finalize_payload,
        }
        self.run_trace_path.write_text(json.dumps(trace_payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        return {"output": str(self.result_output_path), "issues": str(self.result_issue_summary_path), "trace": str(self.run_trace_path)}

    def run_entrypoint(self) -> Dict[str, Any]:
        init_payload = self.init_workspace()
        self_check_payload = self.self_check()
        detect_payload = self.detect_project()
        verify_payload = self.verify()
        finalize_payload = self.finalize()
        output_paths = self.write_entrypoint_result(verify_payload, finalize_payload, self_check_payload, detect_payload)
        return {
            "ok": True,
            "source_root": str(self.source_root),
            "code_dir": str(self.code_dir),
            "artifact_dir": str(self.artifact_dir),
            "init": init_payload,
            "self_check": self_check_payload,
            "detect": detect_payload,
            "verify": verify_payload,
            "finalize": finalize_payload,
            "entrypoint_outputs": output_paths,
        }

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
        readme_summary = self.detect_source_readme()
        cwd, timeout_seconds, commands = self.verification_context()
        commands_summary = self.normalize_verification_commands(self.config.get("verification", {}).get("commands", []))
        attempted: List[Dict[str, Any]] = []
        self.snapshot_diff("before-verify")
        state = self.load_state()
        state["phase"] = "VERIFY"
        self.save_state(state)

        if not commands:
            reasons: List[str] = []
            if not readme_summary.get("found", False):
                reasons.append("source README not found")
            reasons.append("no runnable verification commands were derived from source README or framework defaults")
            payload = {
                "ok": False,
                "status": "blocked-with-report",
                "detected_os": self.current_os,
                "selected_command_profile": commands_summary["selected_profile"],
                "fallback_used": commands_summary["fallback_used"],
                "working_directory": str(cwd),
                "timeout_seconds": timeout_seconds,
                "commands_attempted": attempted,
                "source_readme": readme_summary,
                "reason": "; ".join(reasons),
            }
            self.save_json(self.verify_path, payload)
            state["result"] = "BLOCKED_WITH_REPORT"
            self.save_state(state)
            self.record_gate("VERIFY", "FAIL", "verification blocked", payload["reason"])
            return payload

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
                    "detected_os": self.current_os,
                    "selected_command_profile": commands_summary["selected_profile"],
                    "fallback_used": commands_summary["fallback_used"],
                    "working_directory": str(cwd),
                    "timeout_seconds": timeout_seconds,
                    "commands_attempted": attempted,
                    "selected_command": command,
                    "source_readme": readme_summary,
                }
                self.save_json(self.verify_path, payload)
                state["result"] = "DONE"
                self.save_state(state)
                self.record_gate("VERIFY", "PASS", "verification succeeded", command)
                return payload

        payload = {
            "ok": False,
            "status": "blocked-with-report",
            "detected_os": self.current_os,
            "selected_command_profile": commands_summary["selected_profile"],
            "fallback_used": commands_summary["fallback_used"],
            "working_directory": str(cwd),
            "timeout_seconds": timeout_seconds,
            "commands_attempted": attempted,
            "source_readme": readme_summary,
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
        subagent_contract = config_summary.get("subagent_contract", {})
        coding_skill_contract = config_summary.get("coding_skill", {})
        mode_artifact_summary = (
            self.mode_artifact_summary_path.read_text(encoding="utf-8")
            if self.mode_artifact_summary_path.exists()
            else "No mode artifact summary was generated."
        )
        platform_config = self.config.get("platform", {})
        verification_config = self.config.get("verification", {})
        verification_contract = config_summary.get("verification", {})
        stage_rows: List[str] = []
        declared_stages = subagent_contract.get("stages", []) if isinstance(subagent_contract.get("stages", []), list) else []
        for stage in declared_stages:
            if not isinstance(stage, dict):
                continue
            artifact_path = (self.work_dir / str(stage.get("output", ""))).resolve() if stage.get("output") else None
            metadata = self.read_stage_artifact_metadata(artifact_path) if artifact_path is not None else {}
            if str(stage.get("id", "")) == "07-final-report":
                artifact_display = str(self.final_report_path)
                gate_value = "FINAL_REPORT_READY"
                subagent_value = str(stage.get("subagent", ""))
                parent_direct_value = "false"
            else:
                artifact_display = str(artifact_path) if artifact_path is not None else ""
                gate_value = metadata.get("gate", stage.get("blocked_gate", stage.get("success_gate", "")))
                subagent_value = metadata.get("executed_by_subagent", str(stage.get("subagent", "")))
                parent_direct_value = metadata.get("parent_direct_execution", "MISSING")
            stage_rows.append(
                f"| {stage.get('id', '')} | {subagent_value} | {artifact_display} | {gate_value} | {parent_direct_value} |"
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
            "## Runtime Platform",
            "",
            f"- Detected OS: {self.current_os}",
            f"- Official submission OS: {platform_config.get('official_submission_os', '')}",
            f"- Local development OS: {', '.join(platform_config.get('local_development_os', [])) if isinstance(platform_config.get('local_development_os', []), list) else platform_config.get('local_development_os', '')}",
            f"- Runner: {self.runtime_copy_path}",
            f"- Python version: {sys.version.split()[0]}",
            "",
            "## Verification Command Selection",
            "",
            f"- Command source: {verification_config.get('source', '')}",
            f"- Selected command profile: {verification_contract.get('selected_profile', '')}",
            f"- Fallback used: {verification_contract.get('fallback_used', False)}",
            f"- Working directory: {verification_contract.get('working_directory', '')}",
            f"- Timeout seconds: {verification_config.get('timeout_seconds', '')}",
            "",
            "## Applied Coding Skill",
            "",
            f"- Enabled: {coding_skill_contract.get('enabled', False)}",
            f"- Required: {coding_skill_contract.get('required', False)}",
            f"- Skill: {coding_skill_contract.get('skill', '')}",
            "- Stage: 05-patch",
            f"- Patch summary: {coding_skill_contract.get('output', '')}",
            f"- Result: {self.infer_coding_skill_result(verification, coding_skill_contract)}",
            *(
                [f"- Reason: {coding_skill_contract['errors'][0]}"]
                if coding_skill_contract.get("errors")
                and self.infer_coding_skill_result(verification, coding_skill_contract) == "BLOCKED_WITH_REPORT"
                else []
            ),
            "",
            "## Cross-platform Notes",
            "",
            "- Windows development path: powershell -ExecutionPolicy Bypass -File work/scripts/bootstrap.ps1",
            "- Linux submission path: bash work/scripts/bootstrap.sh",
            f"- Git available: {'true' if shutil.which('git') else 'false'}",
            f"- Shell used for verification: {'cmd.exe or PowerShell child shell' if self.current_os == 'windows' else '/bin/sh-compatible shell'}",
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
            "## Subagent Execution Evidence",
            "",
            "| Stage | Subagent | Artifact | Gate | Parent Direct Execution |",
            "|---|---|---|---|---|",
            *(stage_rows if stage_rows else ["| MISSING | MISSING | MISSING | MISSING | MISSING |"]),
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
            "- Static files in the LoopForge root are read-only during execution.",
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

    def infer_coding_skill_result(self, verification: Dict[str, Any], coding_skill_contract: Dict[str, Any]) -> str:
        if not coding_skill_contract.get("ok", False):
            return "BLOCKED_WITH_REPORT"
        if verification.get("ok") is True:
            return "READY_FOR_VERIFICATION"
        if verification:
            return "DEGRADED_BUT_READY_FOR_VERIFICATION"
        return "READY_FOR_VERIFICATION"


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LoopForge runner")
    parser.add_argument("--work-dir", default="work", help="path to the framework work directory")
    parser.add_argument("--code-dir", default="code", help="path to the target code directory")
    parser.add_argument("--source-root", help="path to the source project root")
    parser.add_argument("--result-dir", help="path to the root-level result directory")
    parser.add_argument("--log-dir", help="path to the root-level log directory")
    parser.add_argument("--init", action="store_true", help="initialize code/.loopforge")
    parser.add_argument("--self-check", action="store_true", help="validate runtime and configuration")
    parser.add_argument("--detect", action="store_true", help="detect target project shape")
    parser.add_argument("--snapshot", metavar="NAME", help="write a git diff snapshot into code/.loopforge/snapshots")
    parser.add_argument("--verify", action="store_true", help="run configured verification.commands")
    parser.add_argument("--finalize", action="store_true", help="write code/.loopforge/reports/final-report.md")
    parser.add_argument("--run", action="store_true", help="execute the entrypoint workflow and mirror outputs to result/ and logs/")
    return parser.parse_args(argv)


def print_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True))


def resolve_path_from_workspace(workspace_root: Path, path_arg: str) -> Path:
    candidate = Path(path_arg)
    if not candidate.is_absolute():
        candidate = (workspace_root / candidate).resolve()
    else:
        candidate = candidate.resolve()
    return candidate


def resolve_work_dir(cwd: Path, work_arg: str) -> Path:
    work_path = Path(work_arg)
    if not work_path.is_absolute():
        work_path = (cwd / work_path).resolve()
    else:
        work_path = work_path.resolve()
    return work_path


def resolve_workspace_root(work_path: Path) -> Path:
    return work_path.parent


def resolve_default_source_root(workspace_root: Path, code_arg: str) -> str:
    if platform.system().lower().startswith("linux"):
        linux_candidates = [
            Path("/__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB"),
            Path("/__CONTEST_PLATFORM_SOURCE_ROOT__"),
        ]
        for candidate in linux_candidates:
            if candidate.exists():
                return str(candidate)
    return code_arg


def resolve_effective_source_arg(workspace_root: Path, code_arg: str, source_arg: Optional[str]) -> str:
    if source_arg and source_arg.strip():
        return source_arg.strip()

    env_source_root = os.environ.get("SOURCE_ROOT", "").strip()
    if env_source_root:
        return env_source_root

    return resolve_default_source_root(workspace_root, code_arg)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    if not any([args.init, args.self_check, args.detect, args.snapshot, args.verify, args.finalize, args.run]):
        print("No action provided.", file=sys.stderr)
        return 2

    try:
        work_dir = resolve_work_dir(Path.cwd().resolve(), args.work_dir)
        workspace_root = resolve_workspace_root(work_dir)
        effective_source_arg = resolve_effective_source_arg(workspace_root, args.code_dir, args.source_root)
        code_dir = resolve_path_from_workspace(workspace_root, effective_source_arg)
        result_dir = None
        if args.result_dir:
            result_dir = resolve_path_from_workspace(Path.cwd().resolve(), args.result_dir)
        log_dir = None
        if args.log_dir:
            log_dir = resolve_path_from_workspace(Path.cwd().resolve(), args.log_dir)
        runner = LoopForgeRunner(workspace_root, work_dir, code_dir, code_dir, result_dir, log_dir)

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
        if args.run:
            print_json(runner.run_entrypoint())
    except Exception as exc:
        print_json({"ok": False, "error": str(exc)})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
