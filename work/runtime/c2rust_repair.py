from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from agent_task_packet import AgentTaskPacket


def _run_command(command: List[str], cwd: Path, timeout_seconds: int) -> Dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return {
            "command": " ".join(command),
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout.strip().splitlines()[-20:],
            "stderr_tail": completed.stderr.strip().splitlines()[-20:],
            "ok": completed.returncode == 0,
            "error": "",
        }
    except FileNotFoundError as exc:
        return {
            "command": " ".join(command),
            "returncode": 127,
            "stdout_tail": [],
            "stderr_tail": [],
            "ok": False,
            "error": str(exc),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": " ".join(command),
            "returncode": 124,
            "stdout_tail": (exc.stdout or "").strip().splitlines()[-20:],
            "stderr_tail": (exc.stderr or "").strip().splitlines()[-20:],
            "ok": False,
            "error": "timeout",
        }


def _repair_action(project_dir: Path, command_result: Dict[str, Any]) -> Dict[str, Any]:
    stderr_text = "\n".join(command_result.get("stderr_tail", []))
    if "Cargo.toml" in stderr_text and not (project_dir / "Cargo.toml").is_file():
        return {"applied": False, "detail": "manifest_missing_and_unrecoverable"}
    if "could not find `Cargo.toml`" in stderr_text:
        return {"applied": False, "detail": "wrong_working_directory"}
    return {"applied": False, "detail": "no_safe_repair_rule_matched"}


def run_repair_loop(packet: AgentTaskPacket, commands: List[str], timeout_seconds: int) -> Dict[str, Any]:
    attempts: List[Dict[str, Any]] = []
    project_dir = packet.paths.project_dir
    rounds = 0
    build_ok = False
    test_ok = False

    while rounds <= packet.max_repair_rounds:
        round_record: Dict[str, Any] = {"round": rounds, "commands": [], "repair_action": None}
        all_ok = True
        for index, command in enumerate(commands):
            command_result = _run_command(command.split(), project_dir, timeout_seconds)
            round_record["commands"].append(command_result)
            if not command_result["ok"]:
                all_ok = False
                if index == 0:
                    packet.add_issue("cargo_build_failed", command_result["command"])
                else:
                    packet.add_issue("cargo_test_failed", command_result["command"])
                if rounds < packet.max_repair_rounds:
                    round_record["repair_action"] = _repair_action(project_dir, command_result)
                break
            if index == 0:
                build_ok = True
            if index == 1:
                test_ok = True
        attempts.append(round_record)
        if all_ok:
            break
        if rounds >= packet.max_repair_rounds or not round_record["repair_action"] or not round_record["repair_action"]["applied"]:
            break
        rounds += 1

    return {
        "ok": build_ok and test_ok,
        "build_ok": build_ok,
        "test_ok": test_ok,
        "rounds_executed": rounds + 1,
        "attempts": attempts,
    }
