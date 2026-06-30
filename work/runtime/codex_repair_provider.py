"""Non-interactive Codex adapter for LoopForge repair task packets."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def find_codex_cli() -> Optional[str]:
    for name in ("codex", "codex.exe", "codex.ps1"):
        found = shutil.which(name)
        if found:
            return found
    return None


def build_codex_command(cli: str, project_dir: Path) -> List[str]:
    # Approval/sandbox/cwd are global options and must precede the subcommand;
    # current Codex releases reject them when placed after `exec`.
    codex_args = [
        "--sandbox", "workspace-write", "--ask-for-approval", "never", "--cd", str(project_dir),
        "exec", "--ephemeral", "--skip-git-repo-check", "--color", "never", "-",
    ]
    if Path(cli).suffix.lower() == ".ps1":
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if not powershell:
            raise FileNotFoundError("Codex is a PowerShell script but pwsh/powershell is unavailable")
        return [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", cli, *codex_args]
    return [cli, *codex_args]


def repair_prompt(task: dict) -> str:
    return "\n".join([
        "You are the unattended repair executor for a generated Rust project.",
        f"Project directory: {task['project_dir']}",
        f"Failed verification command: {task.get('failed_command', '')}",
        f"Return code: {task.get('returncode', '')}",
        "Failure output:",
        *task.get("stdout_tail", []),
        *task.get("stderr_tail", []),
        "Modify files only inside the project directory. Fix the underlying build/test failure.",
        "Do not delete, disable, weaken, or rewrite tests to force success. Do not bypass verification.",
        "Do not invoke LoopForge, run-e2e, this repair provider, or any parent harness recursively.",
        "Run the failed Cargo command and relevant tests before finishing. Continue until they pass.",
    ])


def main() -> int:
    if os.environ.get("LOOPFORGE_CODEX_REPAIR_ACTIVE"):
        print("recursive Codex repair invocation refused", file=sys.stderr)
        return 78
    task_value = os.environ.get("LOOPFORGE_REPAIR_TASK") or (sys.argv[1] if len(sys.argv) > 1 else "")
    if not task_value:
        print("LOOPFORGE_REPAIR_TASK is required", file=sys.stderr)
        return 64
    task_path = Path(task_value).resolve()
    task = json.loads(task_path.read_text(encoding="utf-8"))
    project_dir = Path(task["project_dir"]).resolve()
    if not project_dir.is_dir():
        print(f"project directory does not exist: {project_dir}", file=sys.stderr)
        return 66
    cli = find_codex_cli()
    if not cli:
        print("Codex CLI is unavailable", file=sys.stderr)
        return 69
    try:
        command = build_codex_command(cli, project_dir)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 69
    env = os.environ.copy()
    env["LOOPFORGE_CODEX_REPAIR_ACTIVE"] = "1"
    completed = subprocess.run(command, cwd=str(project_dir), input=repair_prompt(task), text=True, env=env, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
