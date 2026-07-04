"""Non-interactive OpenCode adapter for LoopForge repair task packets."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def find_opencode_cli() -> Optional[str]:
    for name in ("opencode", "opencode.exe", "opencode.ps1"):
        found = shutil.which(name)
        if found:
            return found
    return None


def build_opencode_command(cli: str, project_dir: Path, prompt: str, workspace_root: Optional[Path] = None) -> List[str]:
    # Use workspace root as --dir so evidence directories are within scope
    # This prevents external_directory permission issues for logs/evidence access
    opencode_dir = str(workspace_root) if workspace_root else str(project_dir)
    args = ["run", "--dir", opencode_dir, "--auto", prompt]
    if Path(cli).suffix.lower() == ".ps1":
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if not powershell:
            raise FileNotFoundError("OpenCode is a PowerShell script but pwsh/powershell is unavailable")
        return [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", cli, *args]
    return [cli, *args]


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
    if os.environ.get("LOOPFORGE_REPAIR_AGENT_ACTIVE"):
        print("recursive repair-agent invocation refused", file=sys.stderr)
        return 78
    task_value = os.environ.get("LOOPFORGE_REPAIR_TASK") or (sys.argv[1] if len(sys.argv) > 1 else "")
    if not task_value:
        print("LOOPFORGE_REPAIR_TASK is required", file=sys.stderr)
        return 64
    task = json.loads(Path(task_value).resolve().read_text(encoding="utf-8"))
    project_dir = Path(task["project_dir"]).resolve()
    # Get workspace root from task or derive from project_dir
    workspace_root = Path(task["workspace_root"]).resolve() if "workspace_root" in task else None
    if not project_dir.is_dir():
        print(f"project directory does not exist: {project_dir}", file=sys.stderr)
        return 66
    cli = find_opencode_cli()
    if not cli:
        print("OpenCode CLI is unavailable", file=sys.stderr)
        return 69
    try:
        command = build_opencode_command(cli, project_dir, repair_prompt(task), workspace_root)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 69
    env = os.environ.copy()
    env["LOOPFORGE_REPAIR_AGENT_ACTIVE"] = "1"
    return subprocess.run(command, cwd=str(project_dir), text=True, env=env, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
