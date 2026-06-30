from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple

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
            "stdout_tail": completed.stdout.strip().splitlines()[-40:],
            "stderr_tail": completed.stderr.strip().splitlines()[-40:],
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
            "stdout_tail": (exc.stdout or "").strip().splitlines()[-40:],
            "stderr_tail": (exc.stderr or "").strip().splitlines()[-40:],
            "ok": False,
            "error": "timeout",
        }


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _remove_duplicate_pub_use(project_dir: Path, symbol: str) -> bool:
    lib_rs = project_dir / "src" / "lib.rs"
    if not lib_rs.is_file():
        return False
    lines = lib_rs.read_text(encoding="utf-8").splitlines()
    matches = [index for index, line in enumerate(lines) if f"pub use " in line and symbol in line]
    if len(matches) <= 1:
        return False
    first = matches[0]
    kept = []
    for index, line in enumerate(lines):
        if index in matches and index != first:
            continue
        kept.append(line)
    lib_rs.write_text("\n".join(kept) + "\n", encoding="utf-8")
    return True


def _ensure_module_decl(project_dir: Path, module_name: str) -> bool:
    lib_rs = project_dir / "src" / "lib.rs"
    module_rs = project_dir / "src" / f"{module_name}.rs"
    if not lib_rs.is_file() or not module_rs.is_file():
        return False
    text = _load_text(lib_rs)
    decl = f"mod {module_name};"
    if decl in text:
        return False
    lines = text.splitlines()
    insert_at = 1 if lines else 0
    lines.insert(insert_at, decl)
    lib_rs.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def _ensure_missing_file(project_dir: Path, missing_path: str) -> bool:
    candidate = project_dir / missing_path
    if candidate.exists():
        return False
    if candidate.suffix == ".rs":
        _write(candidate, "#![forbid(unsafe_code)]\n\n")
        return True
    return False


def _fix_missing_import(project_dir: Path, file_path: str, symbol: str) -> bool:
    candidate = project_dir / file_path
    if not candidate.is_file():
        return False
    text = _load_text(candidate)
    if f"use std::collections::{symbol};" in text or symbol not in {"BTreeMap", "HashMap"}:
        return False
    insertion = f"use std::collections::{symbol};\n"
    if text.startswith("#!["):
        parts = text.split("\n", 1)
        text = parts[0] + "\n\n" + insertion + (parts[1] if len(parts) > 1 else "")
    else:
        text = insertion + text
    candidate.write_text(text, encoding="utf-8")
    return True


def _repair_action(project_dir: Path, command_result: Dict[str, Any]) -> Dict[str, Any]:
    stderr_text = "\n".join(command_result.get("stderr_tail", []))
    module_match = re.search(r"file not found for module `([^`]+)`", stderr_text)
    if module_match:
        module_name = module_match.group(1)
        if _ensure_missing_file(project_dir, f"src/{module_name}.rs"):
            return {"applied": True, "detail": "created_missing_module_file", "module": module_name}

    duplicate_match = re.search(r"the name `([^`]+)` is defined multiple times", stderr_text)
    if duplicate_match:
        symbol = duplicate_match.group(1)
        if _remove_duplicate_pub_use(project_dir, symbol):
            return {"applied": True, "detail": "removed_duplicate_export", "symbol": symbol}

    unresolved_import_match = re.search(r"unresolved import `[^`]*::([^`]+)`", stderr_text)
    if unresolved_import_match and _fix_missing_import(project_dir, "src/flashdb.rs", unresolved_import_match.group(1)):
        return {"applied": True, "detail": "added_missing_import", "symbol": unresolved_import_match.group(1)}

    missing_module_decl_match = re.search(r"use of undeclared crate or module `([^`]+)`", stderr_text)
    if missing_module_decl_match:
        module_name = missing_module_decl_match.group(1)
        if _ensure_module_decl(project_dir, module_name):
            return {"applied": True, "detail": "added_missing_module_decl", "module": module_name}

    cannot_find_type_match = re.search(r"cannot find (?:function|type|struct) `([^`]+)`", stderr_text)
    if cannot_find_type_match:
        symbol = cannot_find_type_match.group(1)
        if _remove_duplicate_pub_use(project_dir, symbol):
            return {"applied": True, "detail": "deduplicated_symbol_after_missing_lookup", "symbol": symbol}

    return {"applied": False, "detail": "manual_repair_required"}


def _write_repair_artifacts(packet: AgentTaskPacket, payload: Dict[str, Any]) -> None:
    json_path = packet.paths.migration_trace_dir / "repair-rounds.json"
    md_path = packet.paths.migration_trace_dir / "repair-rounds.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    lines = [
        "# Repair Rounds",
        "",
        f"- rounds_executed: `{payload['rounds_executed']}`",
        f"- build_ok: `{payload['build_ok']}`",
        f"- test_ok: `{payload['test_ok']}`",
        "",
    ]
    for attempt in payload["attempts"]:
        lines.extend([f"## Round {attempt['round']}", ""])
        for command in attempt["commands"]:
            lines.append(f"- `{command['command']}` -> returncode `{command['returncode']}`")
        if attempt.get("repair_action"):
            lines.append(f"- repair_action: `{attempt['repair_action']['detail']}`")
        if attempt.get("repair_task_packet"):
            lines.append(f"- repair_task_packet: `{attempt['repair_task_packet']}`")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")


def run_repair_loop(packet: AgentTaskPacket, commands: List[str], timeout_seconds: int) -> Dict[str, Any]:
    attempts: List[Dict[str, Any]] = []
    project_dir = packet.paths.project_dir
    rounds = 0
    build_ok = False
    test_ok = False

    while rounds <= packet.max_repair_rounds:
        round_record: Dict[str, Any] = {"round": rounds, "commands": [], "repair_action": None, "repair_task_packet": None}
        all_ok = True
        for index, command in enumerate(commands):
            command_result = _run_command(command.split(), project_dir, timeout_seconds)
            round_record["commands"].append(command_result)
            if not command_result["ok"]:
                all_ok = False
                issue_code = "cargo_build_failed" if index == 0 else "cargo_test_failed"
                packet.add_issue(issue_code, command_result["command"])
                repair_action = _repair_action(project_dir, command_result)
                round_record["repair_action"] = repair_action
                if not repair_action["applied"]:
                    round_record["repair_task_packet"] = {
                        "reason": repair_action["detail"],
                        "failed_command": command_result["command"],
                        "stderr_tail": command_result["stderr_tail"],
                    }
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

    payload = {
        "ok": build_ok and test_ok,
        "build_ok": build_ok,
        "test_ok": test_ok,
        "rounds_executed": rounds + 1,
        "attempts": attempts,
    }
    _write_repair_artifacts(packet, payload)
    return payload
