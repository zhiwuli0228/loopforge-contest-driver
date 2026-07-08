from __future__ import annotations

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


COMMAND_PREFIXES = ("./mvnw", "mvn ", "./gradlew", "gradle ", "pytest", "python -m pytest", "npm test", "pnpm test", "yarn test")


def _read_submission_metadata(submission_root: Path) -> Dict[str, Any]:
    for name in ("contest.meta.yaml", "contest.meta.yml"):
        candidate = submission_root / name
        if candidate.is_file():
            with candidate.open("r", encoding="utf-8") as handle:
                return yaml.safe_load(handle) or {}
    return {}


def _commands_from_metadata(metadata: Mapping[str, Any]) -> List[Dict[str, Any]]:
    verification = metadata.get("verification", {})
    if isinstance(verification, Mapping):
        commands = verification.get("commands")
        if isinstance(commands, list):
            normalized: List[Dict[str, Any]] = []
            for index, item in enumerate(commands):
                if isinstance(item, str):
                    normalized.append(
                        {
                            "name": f"metadata_{index}",
                            "command": item,
                            "verification_class": "metadata",
                            "requires": [],
                            "source": "submission-metadata",
                        }
                    )
                elif isinstance(item, Mapping) and isinstance(item.get("command"), str):
                    normalized.append(
                        {
                            "name": str(item.get("name") or f"metadata_{index}"),
                            "command": item["command"],
                            "verification_class": str(item.get("verification_class") or item.get("class") or item.get("name") or "metadata"),
                            "requires": list(item.get("requires", [])),
                            "source": "submission-metadata",
                        }
                    )
            if normalized:
                return normalized
    return []


def _commands_from_readme(readme_path: Path) -> List[Dict[str, Any]]:
    if not readme_path.is_file():
        return []
    commands: List[Dict[str, Any]] = []
    inside_fence = False
    lines = readme_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    for raw_line in lines:
        line = raw_line.strip()
        if line.startswith("```"):
            inside_fence = not inside_fence
            continue
        normalized = line.strip("` ")
        if not normalized:
            continue
        if inside_fence or normalized.startswith(("-", "#")) or normalized.startswith("mvn ") or normalized.startswith("./mvnw") or normalized.startswith("./gradlew") or normalized.startswith("gradle "):
            candidate = normalized.lstrip("-* ").strip()
            if any(candidate.startswith(prefix) for prefix in COMMAND_PREFIXES):
                verification_class = "project_verification"
                name = f"readme_{len(commands)}"
                requires: List[str] = []
                lowered = candidate.lower()
                if "code/pom.xml test" in lowered:
                    verification_class = "project_tests"
                    name = "project_tests"
                elif "code/pom.xml install" in lowered:
                    verification_class = "project_install"
                    name = "project_install"
                elif "test-cases/pom.xml test" in lowered:
                    verification_class = "black_box_tests"
                    name = "black_box_tests"
                    requires = ["project_install"]
                commands.append(
                    {
                        "name": name,
                        "command": candidate,
                        "verification_class": verification_class,
                        "requires": requires,
                        "source": "submission-readme",
                    }
                )
    return commands


def _commands_from_profile(profile: Mapping[str, Any], adapter_id: str | None) -> List[Dict[str, Any]]:
    verification = profile.get("verification", {}).get("command_selection", {})
    ordered = verification.get("ordered_classes", [])
    normalized: List[Dict[str, Any]] = []
    for item in ordered:
        if not isinstance(item, Mapping) or not isinstance(item.get("command"), str):
            continue
        name = str(item.get("name") or f"profile_{len(normalized)}")
        normalized.append(
            {
                "name": name,
                "command": item["command"],
                "verification_class": name,
                "requires": list(item.get("required_before", [])),
                "source": "profile-ordered",
            }
        )
    if normalized:
        return normalized

    adapter = adapter_id or "generic"
    adapter_config = profile.get("language", {}).get("adapters", {}).get(adapter, {}).get("verification", {})
    preferred = list(adapter_config.get("preferred_commands", []))
    fallback = list(adapter_config.get("fallback_commands", []))
    commands = preferred or fallback
    return [
        {
            "name": f"profile_{index}",
            "command": command,
            "verification_class": "profile_default",
            "requires": [],
            "source": "profile-or-framework-default",
        }
        for index, command in enumerate(commands)
    ]


def resolve_verification_commands(
    source_root: str | Path,
    profile_path: str | Path | None = None,
    *,
    adapter_id: str | None = None,
    submission_root: str | Path | None = None,
    commands_override: Sequence[str] | None = None,
) -> Dict[str, Any]:
    if commands_override is not None:
        return {
            "commands": [
                {
                    "name": f"override_{index}",
                    "command": command,
                    "verification_class": "override",
                    "requires": [],
                    "source": "override",
                }
                for index, command in enumerate(commands_override)
            ],
            "command_source": "override",
        }

    resolved_submission_root = Path(submission_root).resolve() if submission_root else None
    if resolved_submission_root and resolved_submission_root.is_dir():
        metadata = _read_submission_metadata(resolved_submission_root)
        metadata_commands = _commands_from_metadata(metadata)
        if metadata_commands:
            return {"commands": metadata_commands, "command_source": "submission-metadata"}
        readme_commands = _commands_from_readme(resolved_submission_root / "README.md")
        if readme_commands:
            return {"commands": readme_commands, "command_source": "submission-readme"}

    profile = _load_profile(profile_path)
    commands = _commands_from_profile(profile, adapter_id)
    return {"commands": commands, "command_source": "profile-or-framework-default"}


def run_verification(
    project_dir: str | Path,
    *,
    commands: Sequence[Mapping[str, Any]] | Sequence[str] | None = None,
    timeout: int = 300,
    command_source: str = "explicit",
) -> Dict[str, Any]:
    root = Path(project_dir)
    if not root.is_dir():
        raise ValueError(f"project-dir does not exist: {root}")

    raw_commands = list(commands or [])
    planned_commands: List[Dict[str, Any]] = []
    for index, item in enumerate(raw_commands):
        if isinstance(item, str):
            planned_commands.append(
                {
                    "name": f"command_{index}",
                    "command": item,
                    "verification_class": "explicit",
                    "requires": [],
                    "source": command_source,
                }
            )
        else:
            planned_commands.append(
                {
                    "name": str(item.get("name") or f"command_{index}"),
                    "command": str(item.get("command") or ""),
                    "verification_class": str(item.get("verification_class") or item.get("name") or "explicit"),
                    "requires": list(item.get("requires", [])),
                    "source": str(item.get("source") or command_source),
                }
            )

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
                "blocked_count": 0,
                "skipped_count": 1,
            },
            "reason": "No verification commands were declared for the selected adapter or invocation.",
        }

    results: List[Dict[str, Any]] = []
    statuses_by_name: Dict[str, str] = {}
    for command_info in planned_commands:
        name = command_info["name"]
        command = command_info["command"]
        requires = command_info.get("requires", [])
        verification_class = command_info["verification_class"]

        blocked_requires = [required for required in requires if statuses_by_name.get(required) != "success"]
        if blocked_requires:
            result = {
                "name": name,
                "command": command,
                "verification_class": verification_class,
                "status": "blocked",
                "exit_code": None,
                "timed_out": False,
                "stdout": "",
                "stderr": "",
                "reason": f"blocked by prerequisites: {', '.join(blocked_requires)}",
                "requires": requires,
                "command_source": command_info["source"],
            }
            results.append(result)
            statuses_by_name[name] = "blocked"
            continue

        available, unavailable_reason = _command_is_available(root, command)
        if not available:
            result = {
                "name": name,
                "command": command,
                "verification_class": verification_class,
                "status": "unavailable",
                "exit_code": None,
                "timed_out": False,
                "stdout": "",
                "stderr": "",
                "reason": unavailable_reason,
                "requires": requires,
                "command_source": command_info["source"],
            }
            results.append(result)
            statuses_by_name[name] = "unavailable"
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
            status = "success" if completed.returncode == 0 else "failed"
            result = {
                "name": name,
                "command": command,
                "verification_class": verification_class,
                "status": status,
                "exit_code": completed.returncode,
                "timed_out": False,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "reason": "",
                "requires": requires,
                "command_source": command_info["source"],
            }
            results.append(result)
            statuses_by_name[name] = status
        except subprocess.TimeoutExpired:
            result = {
                "name": name,
                "command": command,
                "verification_class": verification_class,
                "status": "timeout",
                "exit_code": None,
                "timed_out": True,
                "stdout": "",
                "stderr": "",
                "reason": f"Timed out after {timeout}s",
                "requires": requires,
                "command_source": command_info["source"],
            }
            results.append(result)
            statuses_by_name[name] = "timeout"

    statuses = [item["status"] for item in results]
    if statuses and all(status == "success" for status in statuses):
        overall_status = "success"
    elif "failed" in statuses:
        overall_status = "failed"
    elif "timeout" in statuses:
        overall_status = "timeout"
    elif "blocked" in statuses:
        overall_status = "blocked"
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
            "blocked_count": len([item for item in results if item["status"] == "blocked"]),
            "skipped_count": 0,
        },
    }
