from __future__ import annotations

import json
import re
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


def _sanitize_lib_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value).strip("_").lower()
    return cleaned or "c_to_rust_output"


def _sanitize_package_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "-", value).strip("-").lower()
    return cleaned or "c-to-rust-output"


def _sanitize_text(text: str, workspace_root: Path) -> str:
    normalized_text = text.replace("\\", "/")
    roots = {str(workspace_root), str(workspace_root).replace("\\", "/")}
    for root in roots:
        normalized_text = normalized_text.replace(root, ".")
        normalized_text = re.sub(re.escape(root), ".", normalized_text, flags=re.IGNORECASE)
    return normalized_text


def _sanitize_value(value: Any, workspace_root: Path) -> Any:
    if isinstance(value, dict):
        return {key: _sanitize_value(item, workspace_root) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_value(item, workspace_root) for item in value]
    if isinstance(value, str):
        return _sanitize_text(value, workspace_root)
    return value


def _remove_duplicate_pub_use(project_dir: Path, symbol: str) -> bool:
    lib_rs = project_dir / "src" / "lib.rs"
    if not lib_rs.is_file():
        return False
    lines = lib_rs.read_text(encoding="utf-8").splitlines()
    matches = [index for index, line in enumerate(lines) if "pub use " in line and symbol in line]
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
    decl = f"pub mod {module_name};"
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


def _fix_missing_import(project_dir: Path, symbol: str) -> bool:
    for candidate in (project_dir / "src").glob("*.rs"):
        text = _load_text(candidate)
        if symbol == "c_char" and "use std::ffi::c_char;" not in text:
            candidate.write_text("use std::ffi::c_char;\n" + text, encoding="utf-8")
            return True
        if symbol == "c_void" and "use std::ffi::c_void;" not in text:
            candidate.write_text("use std::ffi::c_void;\n" + text, encoding="utf-8")
            return True
    return False


def _ensure_cargo_manifest(packet: AgentTaskPacket, project_dir: Path) -> bool:
    cargo_toml = project_dir / "Cargo.toml"
    if cargo_toml.is_file():
        return False
    content = "\n".join(
        [
            "[package]",
            f'name = "{_sanitize_package_name(packet.output_project_name)}"',
            'version = "0.1.0"',
            'edition = "2021"',
            "",
            "[lib]",
            f'name = "{_sanitize_lib_name(packet.output_project_name)}"',
            'path = "src/lib.rs"',
            "",
        ]
    )
    _write(cargo_toml, content)
    return True


def _repair_reset_storage(project_dir: Path) -> bool:
    """Repair a count-only reset for a generated Vec-backed C array model."""
    for candidate in (project_dir / "src").glob("*.rs"):
        text = _load_text(candidate)
        struct_match = re.search(r"pub struct\s+\w+\s*\{(?P<body>.*?)\n\}", text, re.DOTALL)
        if not struct_match:
            continue
        vec_match = re.search(r"pub\s+(\w+)\s*:\s*Vec<", struct_match.group("body"))
        count_match = re.search(r"pub\s+(\w+)\s*:\s*usize", struct_match.group("body"))
        if not vec_match or not count_match:
            continue
        records, count = vec_match.group(1), count_match.group(1)
        reset = re.compile(rf"(?P<indent>\s*)(?P<state>\w+)\.{re.escape(count)}\s*=\s*0;")
        match = reset.search(text)
        if not match:
            continue
        clear_line = f"{match.group('indent')}{match.group('state')}.{records}.clear();"
        if clear_line.strip() in text:
            continue
        candidate.write_text(text[:match.start()] + clear_line + "\n" + text[match.start():], encoding="utf-8")
        return True
    return False


def _repair_action(packet: AgentTaskPacket, project_dir: Path, command_result: Dict[str, Any]) -> Dict[str, Any]:
    stderr_text = "\n".join(command_result.get("stderr_tail", []))
    output_text = "\n".join(command_result.get("stdout_tail", []) + command_result.get("stderr_tail", []))
    if "test_reset_after_mutation" in output_text and _repair_reset_storage(project_dir):
        return {"applied": True, "detail": "synchronized_logical_storage_on_reset", "failed_test": "test_reset_after_mutation"}
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
    if unresolved_import_match and _fix_missing_import(project_dir, unresolved_import_match.group(1)):
        return {"applied": True, "detail": "added_missing_import", "symbol": unresolved_import_match.group(1)}

    missing_module_decl_match = re.search(r"use of undeclared crate or module `([^`]+)`", stderr_text)
    if missing_module_decl_match:
        module_name = missing_module_decl_match.group(1)
        if _ensure_module_decl(project_dir, module_name):
            return {"applied": True, "detail": "added_missing_module_decl", "module": module_name}

    missing_manifest = re.search(r"could not find `Cargo\.toml`", stderr_text) or "could not find `cargo.toml`" in stderr_text.lower()
    if missing_manifest and _ensure_cargo_manifest(packet, project_dir):
        return {"applied": True, "detail": "created_missing_cargo_manifest"}

    return {"applied": False, "detail": "manual_repair_required"}


def _write_repair_artifacts(packet: AgentTaskPacket, payload: Dict[str, Any]) -> None:
    json_path = packet.paths.migration_trace_dir / "repair-rounds.json"
    md_path = packet.paths.migration_trace_dir / "repair-rounds.md"
    sanitized_payload = _sanitize_value(payload, packet.paths.workspace_root)
    json_path.write_text(json.dumps(sanitized_payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    lines = [
        "# Repair Rounds",
        "",
        f"- rounds_executed: `{payload['rounds_executed']}`",
        f"- build_ok: `{payload['build_ok']}`",
        f"- test_ok: `{payload['test_ok']}`",
        "",
    ]
    for attempt in sanitized_payload["attempts"]:
        lines.extend([f"## Round {attempt['round']}", ""])
        for command in attempt["commands"]:
            lines.append(f"- `{command['command']}` -> returncode `{command['returncode']}`")
        if attempt.get("repair_action"):
            lines.append(f"- repair_action: `{attempt['repair_action']['detail']}`")
        if attempt.get("repair_task_packet"):
            lines.append(f"- repair_task_packet: `{json.dumps(attempt['repair_task_packet'], ensure_ascii=True)}`")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    for attempt in sanitized_payload["attempts"]:
        round_lines = [f"# Repair Round {attempt['round']:02d}", "", f"- result: `{'passed' if all(command.get('ok') for command in attempt['commands']) else 'failed'}`"]
        if attempt.get("repair_action"):
            round_lines.append(f"- repair_action: `{attempt['repair_action']['detail']}`")
        round_lines.append("")
        (packet.paths.migration_trace_dir / f"repair-round-{attempt['round'] + 1:02d}.md").write_text("\n".join(round_lines), encoding="utf-8")


def run_repair_loop(packet: AgentTaskPacket, commands: List[str], timeout_seconds: int) -> Dict[str, Any]:
    attempts: List[Dict[str, Any]] = []
    project_dir = packet.output_project_dir
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
                repair_action = _repair_action(packet, project_dir, command_result)
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
        "unresolved_failures": [] if build_ok and test_ok else [
            {"kind": "cargo_verification_failed", "command": command["command"], "stderr_tail": command.get("stderr_tail", [])}
            for attempt in attempts for command in attempt["commands"] if not command.get("ok")
        ][-1:],
    }
    if not payload["ok"]:
        packet.add_issue("cargo_verification_failed", "build or test failure remained after the repair loop")
    _write_repair_artifacts(packet, payload)
    return payload
