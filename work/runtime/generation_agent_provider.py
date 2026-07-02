"""Evidence-driven OpenCode provider for complex generated Rust projects."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping

from rust_project_generation import validate_candidate
from timeout_policy import JUDGING_PLATFORM_TIMEOUT_SECONDS


def _rust_text(project_dir: Path) -> str:
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in sorted((project_dir / "src").glob("*.rs")))
    text = re.sub(r'"(?:\\.|[^"\\])*"', '""', text)
    return re.sub(r"(?m)//.*$", "", text)


def _has_one_definition(text: str, symbol: str) -> bool:
    if not symbol or symbol in {"if", "for", "while", "switch"}:
        return False
    pattern = re.compile(r"(?m)\b(?:pub(?:\([^)]*\))?\s+)?fn\s+" + re.escape(symbol) + r"(?:\s*<[^>{}]*>)?\s*\(")
    return len(pattern.findall(text)) == 1


def resolve_diagnostics(project_dir: Path, diagnostics: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    text = _rust_text(project_dir)
    result = []
    for item in diagnostics:
        record = dict(item)
        module_file = project_dir / "src" / f"{str(record.get('module', '')).strip()}.rs"
        scoped_text = text
        if module_file.is_file():
            scoped_text = re.sub(r'"(?:\\.|[^"\\])*"', '""', module_file.read_text(encoding="utf-8", errors="ignore"))
        symbol = str(record.get("symbol", ""))
        record["resolved"] = _has_one_definition(scoped_text or text, symbol) or _has_one_definition(text, symbol)
        result.append(record)
    return result


def build_opencode_command(cli: str, project_dir: Path, prompt: str, model: str = "") -> list[str]:
    args = ["run", "--dir", str(project_dir), "--dangerously-skip-permissions"]
    if model:
        args.extend(["--model", model])
    args.append(prompt)
    if Path(cli).suffix.lower() == ".ps1":
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if not powershell:
            raise FileNotFoundError("OpenCode is a PowerShell script but pwsh/powershell is unavailable")
        return [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", cli, *args]
    return [cli, *args]


def _prompt(project_dir: Path, source_root: Path, trace_dir: Path, failures: Iterable[str], missing: Iterable[str], final: bool) -> str:
    return "\n".join([
        "You are the generic unattended C-to-Rust generation repair agent.",
        f"Generated Rust project (the only writable root): {project_dir}",
        f"Read-only C source: {source_root}",
        f"Current-run evidence: {trace_dir}",
        f"This is {'the single final retry' if final else 'the initial generation repair'}.",
        f"Strict validation failures: {', '.join(failures) or 'not yet evaluated'}",
        f"Missing, duplicate, or unresolved symbols: {', '.join(missing) or 'derive from evidence'}",
        "Implement every real source function and public API exactly once in Rust, preserving observable behavior, state, persistence, errors, ordering, recovery, and call relationships.",
        "Use source structure and current-run evidence only. Never dispatch on project name, symbol prefix, domain name, known path, fixed API list, or golden output.",
        "Do not use FFI, compile/link/copy C, placeholders, todo/unimplemented, constant-return pseudo implementations, vacuous tests, or weakened assertions.",
        "Keep unsafe strictly below ten percent and justify every unsafe site; prefer safe ownership and explicit storage abstractions.",
        "Run cargo build --locked and cargo test --locked -- --nocapture. Continue until both pass and all evidence symbols have exactly one implementation.",
        "Do not modify the source, trace, harness, rules, prompts, or reports.",
    ])


def repair_generation(
    project_dir: Path,
    source_root: Path,
    trace_dir: Path,
    inputs: Mapping[str, Any],
    diagnostics: Iterable[Mapping[str, Any]],
    *,
    model: str = "",
    timeout_seconds: int = JUDGING_PLATFORM_TIMEOUT_SECONDS,
    attempts: int = 2,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cli = shutil.which(os.environ.get("LOOPFORGE_GENERATION_AGENT_COMMAND", "opencode"))
    records: list[dict[str, Any]] = []
    current = [dict(item) for item in diagnostics]
    if not cli:
        return current, {"status": "unavailable", "reason": "OpenCode CLI unavailable", "attempts": records}
    for index in range(max(0, min(attempts, 2))):
        current = resolve_diagnostics(project_dir, current)
        validation = validate_candidate(project_dir, inputs, generation_diagnostics=current)
        if validation["passed"]:
            return current, {"status": "repaired", "attempts": records, "verification": validation}
        missing = [item.get("source_symbol", "") for item in validation.get("unsupported_functions", [])]
        missing.extend(item.get("symbol", "") for item in validation.get("unresolved_generation_diagnostics", []))
        prompt = _prompt(project_dir, source_root, trace_dir, validation.get("failures", []), sorted(set(filter(None, missing))), index == 1)
        env = os.environ.copy()
        env["LOOPFORGE_GENERATION_AGENT_ACTIVE"] = "1"
        try:
            completed = subprocess.run(
                build_opencode_command(cli, project_dir, prompt, model), cwd=project_dir,
                text=True, capture_output=True, timeout=timeout_seconds, check=False, env=env,
            )
            record = {"attempt": index + 1, "final_retry": index == 1, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
        except (OSError, subprocess.TimeoutExpired) as exc:
            record = {"attempt": index + 1, "final_retry": index == 1, "returncode": -1, "stdout": "", "stderr": f"{type(exc).__name__}: {exc}"}
        records.append(record)
    current = resolve_diagnostics(project_dir, current)
    validation = validate_candidate(project_dir, inputs, generation_diagnostics=current)
    return current, {"status": "repaired" if validation["passed"] else "unresolved", "attempts": records, "verification": validation}


def write_report(trace_dir: Path, report: Mapping[str, Any]) -> None:
    trace_dir.mkdir(parents=True, exist_ok=True)
    (trace_dir / "generation-agent-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
