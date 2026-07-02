from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from agent_task_packet import AgentTaskPacket
from self_healing_loop import RepairConfig, SelfHealingOrchestrator, normalize_diagnostic


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


def _external_repair_command(packet: AgentTaskPacket) -> Any:
    """Return the configured agent/repair executor command, if available."""
    provider = packet.config.get("execution", {}).get("repair_provider", {}) or {}
    if provider.get("enabled", "auto") is False:
        return None
    override = os.environ.get("LOOPFORGE_REPAIR_COMMAND")
    if override:
        return override
    if provider.get("command"):
        return provider["command"]
    if provider.get("enabled", "auto") in {True, "auto"} and not os.environ.get("LOOPFORGE_REPAIR_AGENT_ACTIVE"):
        if any(shutil.which(name) for name in ("opencode", "opencode.exe", "opencode.ps1")):
            adapter = Path(__file__).with_name("opencode_repair_provider.py")
            if adapter.is_file():
                return [sys.executable, str(adapter)]
    return None


def _run_external_repair_provider(
    packet: AgentTaskPacket,
    project_dir: Path,
    command_result: Dict[str, Any],
    round_number: int,
    timeout_seconds: int,
) -> Dict[str, Any]:
    task = {
        "round": round_number,
        "project_dir": str(project_dir.resolve()),
        "failed_command": command_result.get("command", ""),
        "returncode": command_result.get("returncode"),
        "stdout_tail": command_result.get("stdout_tail", []),
        "stderr_tail": command_result.get("stderr_tail", []),
        "instructions": "Modify the project in place to fix the failure; do not remove tests or bypass verification.",
    }
    return invoke_external_repair_provider(packet, project_dir, task, "repair", round_number, timeout_seconds)


def invoke_external_repair_provider(packet: AgentTaskPacket, project_dir: Path, task: Dict[str, Any],
                                    trace_prefix: str, round_number: int, timeout_seconds: int) -> Dict[str, Any]:
    """Invoke the configured provider with a caller-defined, auditable task packet."""
    command = _external_repair_command(packet)
    if not command:
        return {"applied": False, "detail": "repair_provider_unavailable"}
    task_path = packet.paths.migration_trace_dir / f"{trace_prefix}-task-{round_number + 1:02d}.json"
    task_path.write_text(json.dumps(task, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    replacements = {"{task_packet}": str(task_path), "{project_dir}": str(project_dir)}
    if isinstance(command, list):
        argv = [str(item) for item in command]
    else:
        argv = shlex.split(str(command), posix=os.name != "nt")
    argv = [next((value for token, value in replacements.items() if item == token), item) for item in argv]
    env = os.environ.copy()
    env.update({
        "LOOPFORGE_REPAIR_TASK": str(task_path),
        "LOOPFORGE_PROJECT_DIR": str(project_dir),
        "LOOPFORGE_FAILED_COMMAND": str(task.get("failed_command", "")),
    })
    try:
        completed = subprocess.run(argv, cwd=str(project_dir), capture_output=True, text=True,
                                   timeout=timeout_seconds, check=False, env=env)
        provider_result = {
            "command": argv,
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout.strip().splitlines()[-40:],
            "stderr_tail": completed.stderr.strip().splitlines()[-40:],
        }
        (packet.paths.migration_trace_dir / f"{trace_prefix}-provider-{round_number + 1:02d}.json").write_text(
            json.dumps(provider_result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        return {"applied": completed.returncode == 0,
                "detail": "external_repair_provider_completed" if completed.returncode == 0 else "external_repair_provider_failed",
                "task_packet": str(task_path), "provider": provider_result}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"applied": False, "detail": "external_repair_provider_error",
                "task_packet": str(task_path), "error": str(exc)}


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
    """Run build/test verification through the isolated self-healing boundary.

    The compatibility payload remains stable for existing gates, while detailed
    repair evidence is emitted by ``SelfHealingOrchestrator``.
    """
    attempts: List[Dict[str, Any]] = []
    project_dir = packet.output_project_dir
    build_ok = False
    test_ok = False
    run_id = str(packet.metadata.get("run_id") or packet.design_readme_sha256)
    provider_round = 0

    def isolated_provider(task: Dict[str, Any], isolated_project: Path) -> Dict[str, Any]:
        nonlocal provider_round
        result = invoke_external_repair_provider(
            packet, isolated_project, task, "isolated-repair", provider_round, timeout_seconds,
        )
        provider_round += 1
        return result

    verification_commands = [shlex.split(command, posix=os.name != "nt") for command in commands]
    targeted = tuple(verification_commands[0]) if verification_commands else (sys.executable, "-c", "pass")
    regression = tuple(verification_commands[1]) if len(verification_commands) > 1 else targeted
    orchestrator = SelfHealingOrchestrator(
        run_id=run_id,
        project_root=project_dir,
        trace_dir=packet.paths.migration_trace_dir,
        provider=isolated_provider,
        config=RepairConfig(
            max_local_rounds=max(1, packet.max_repair_rounds),
            timeout_seconds=timeout_seconds,
            targeted_command=targeted,
            regression_command=regression,
        ),
    )

    initial_record: Dict[str, Any] = {"round": 0, "commands": [], "repair_action": None, "repair_task_packet": None}
    failed: Dict[str, Any] | None = None
    for index, command in enumerate(commands):
        command_result = _run_command(shlex.split(command, posix=os.name != "nt"), project_dir, timeout_seconds)
        initial_record["commands"].append(command_result)
        if command_result["ok"]:
            build_ok = build_ok or index == 0
            test_ok = test_ok or index == 1
            continue
        failed = command_result
        evidence_path = packet.paths.migration_trace_dir / "compiler-or-test-error.log"
        raw_diagnostic = "\n".join(command_result.get("stdout_tail", []) + command_result.get("stderr_tail", [])) or command_result.get("error", "unknown command failure")
        evidence_path.write_text(raw_diagnostic + "\n", encoding="utf-8")
        repair_ir = normalize_diagnostic(
            run_id=run_id,
            source="compiler" if index == 0 else "targeted-test",
            tool="cargo",
            text=raw_diagnostic,
            project_root=project_dir,
            evidence_path=evidence_path,
        )
        repaired = orchestrator.process(repair_ir)
        initial_record["repair_action"] = {"applied": repaired, "detail": "isolated_verified_repair" if repaired else "deferred_for_final_retry"}
        break
    attempts.append(initial_record)

    if failed is not None:
        orchestrator.final_retry()
        final_record: Dict[str, Any] = {"round": 1, "commands": [], "repair_action": None, "repair_task_packet": None}
        build_ok = False
        test_ok = False
        for index, command in enumerate(commands):
            result = _run_command(shlex.split(command, posix=os.name != "nt"), project_dir, timeout_seconds)
            final_record["commands"].append(result)
            if not result["ok"]:
                break
            build_ok = build_ok or index == 0
            test_ok = test_ok or index == 1
        attempts.append(final_record)
    else:
        orchestrator.final_retry()
    integrity_report = orchestrator.publish()

    payload = {
        "ok": build_ok and test_ok,
        "build_ok": build_ok,
        "test_ok": test_ok,
        "rounds_executed": len(attempts),
        "attempts": attempts,
        "unresolved_failures": [] if build_ok and test_ok else [
            {"kind": "cargo_verification_failed", "command": command["command"], "stderr_tail": command.get("stderr_tail", [])}
            for attempt in attempts for command in attempt["commands"] if not command.get("ok")
        ][-1:],
        "repair_integrity": integrity_report,
    }
    if not payload["ok"]:
        packet.add_issue("cargo_verification_failed", "build or test failure remained after the repair loop")
    _write_repair_artifacts(packet, payload)
    return payload
