from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import yaml


def _load_profile(path: str | Path | None) -> Dict[str, Any]:
    if path is None:
        return {}
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _parse_command_tokens(command: str) -> List[str]:
    try:
        return shlex.split(command, posix=os.name != "nt")
    except ValueError:
        return command.split()


def _command_is_available(project_dir: Path, command: str) -> tuple[bool, str]:
    tokens = _parse_command_tokens(command)
    if not tokens:
        return False, "empty command"
    executable = tokens[0]
    if executable.startswith("./") or executable.startswith(".\\") or "/" in executable or "\\" in executable:
        if (project_dir / executable).exists():
            return True, ""
        return False, f"executable not found relative to project dir: {executable}"
    if shutil.which(executable):
        return True, ""
    return False, f"executable not found in PATH: {executable}"


def resolve_verification_commands(
    source_root: str | Path,
    profile_path: str | Path | None = None,
    *,
    adapter_id: str | None = None,
    commands_override: Sequence[str] | None = None,
) -> Dict[str, Any]:
    if commands_override is not None:
        return {"commands": list(commands_override), "command_source": "override"}

    profile = _load_profile(profile_path)
    adapter = adapter_id or "generic"
    adapter_config = (
        profile.get("language", {})
        .get("adapters", {})
        .get(adapter, {})
        .get("verification", {})
    )
    preferred = list(adapter_config.get("preferred_commands", []))
    fallback = list(adapter_config.get("fallback_commands", []))
    command_source = "profile-or-framework-default"
    return {"commands": preferred or fallback, "command_source": command_source}


def run_verification(
    project_dir: str | Path,
    *,
    commands: Sequence[str] | None = None,
    timeout: int = 300,
    command_source: str = "explicit",
) -> Dict[str, Any]:
    root = Path(project_dir)
    if not root.is_dir():
        raise ValueError(f"project-dir does not exist: {root}")

    planned_commands = list(commands or [])
    if not planned_commands:
        return {
            "project_dir": str(root),
            "command_source": command_source,
            "overall_status": "skipped",
            "results": [],
            "summary": {
                "planned_command_count": 0,
                "executed_command_count": 0,
                "successful_command_count": 0,
                "failed_command_count": 0,
                "timeout_count": 0,
                "unavailable_count": 0,
                "skipped_count": 1,
            },
            "reason": "No verification commands were declared for the selected adapter or invocation.",
        }

    results: List[Dict[str, Any]] = []
    for command in planned_commands:
        available, unavailable_reason = _command_is_available(root, command)
        if not available:
            results.append(
                {
                    "command": command,
                    "status": "unavailable",
                    "exit_code": None,
                    "timed_out": False,
                    "stdout": "",
                    "stderr": "",
                    "reason": unavailable_reason,
                }
            )
            continue

        try:
            completed = subprocess.run(
                command,
                shell=True,
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            results.append(
                {
                    "command": command,
                    "status": "success" if completed.returncode == 0 else "failed",
                    "exit_code": completed.returncode,
                    "timed_out": False,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                    "reason": "",
                }
            )
        except subprocess.TimeoutExpired:
            results.append(
                {
                    "command": command,
                    "status": "timeout",
                    "exit_code": None,
                    "timed_out": True,
                    "stdout": "",
                    "stderr": "",
                    "reason": f"Timed out after {timeout}s",
                }
            )

    statuses = [item["status"] for item in results]
    if statuses and all(status == "success" for status in statuses):
        overall_status = "success"
    elif "failed" in statuses:
        overall_status = "failed"
    elif "timeout" in statuses:
        overall_status = "timeout"
    elif "unavailable" in statuses and set(statuses) == {"unavailable"}:
        overall_status = "unavailable"
    else:
        overall_status = "partial"

    return {
        "project_dir": str(root),
        "command_source": command_source,
        "overall_status": overall_status,
        "results": results,
        "summary": {
            "planned_command_count": len(planned_commands),
            "executed_command_count": len([item for item in results if item["status"] in {"success", "failed", "timeout"}]),
            "successful_command_count": len([item for item in results if item["status"] == "success"]),
            "failed_command_count": len([item for item in results if item["status"] == "failed"]),
            "timeout_count": len([item for item in results if item["status"] == "timeout"]),
            "unavailable_count": len([item for item in results if item["status"] == "unavailable"]),
            "skipped_count": 0,
        },
    }
