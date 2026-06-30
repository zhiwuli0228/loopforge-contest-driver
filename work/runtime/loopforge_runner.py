#!/usr/bin/env python3
"""LoopForge runner for the FlashDB C-to-Rust contest branch."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
README_CANDIDATES = [
    "README.md",
    "README",
    "READNE.md",
    "readme.md",
    "Readme.md",
]
REQUIRED_WORK_FILES = [
    "loopforge.config.yaml",
    "HARNESS.md",
    "runtime/loopforge_runner.py",
    "runtime/check_unsafe_ratio.py",
    "scripts/run.sh",
    "scripts/run.ps1",
    "skills/loopforge-driver/SKILL.md",
    "skills/c2rust-flashdb-migration/SKILL.md",
    "profiles/examples/c2rust-flashdb-migration.yaml",
]
REQUIRED_ADAPTER_FILES = [
    "rules/loopforge/adapters/c2rust-flashdb/source-contract.md",
    "rules/loopforge/adapters/c2rust-flashdb/output-contract.md",
    "rules/loopforge/adapters/c2rust-flashdb/test-migration-contract.md",
    "rules/loopforge/adapters/c2rust-flashdb/unsafe-contract.md",
    "rules/loopforge/adapters/c2rust-flashdb/verification-contract.md",
]
REQUIRED_SUBAGENT_FILES = [
    "subagent/c2rust-source-inventory-subagent.md",
    "subagent/c2rust-api-mapping-subagent.md",
    "subagent/c2rust-implementation-subagent.md",
    "subagent/c2rust-test-migration-subagent.md",
    "subagent/c2rust-verification-subagent.md",
    "subagent/c2rust-final-report-subagent.md",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FORMAT)


def parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "~"}:
        return None
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    if value.lstrip("-").isdigit():
        try:
            return int(value)
        except ValueError:
            return value
    return value


def parse_simple_yaml(text: str) -> Dict[str, Any]:
    root: Dict[str, Any] = {}
    stack: List[tuple[int, Any]] = [(-1, root)]
    lines = text.splitlines()

    def next_meaningful(start: int) -> Optional[str]:
        for candidate in lines[start + 1 :]:
            stripped = candidate.strip()
            if stripped and not stripped.startswith("#"):
                return candidate
        return None

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
            raise ValueError(f"invalid yaml near line {index + 1}")
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value:
            if isinstance(container, list):
                raise ValueError(f"unexpected mapping item near line {index + 1}")
            container[key] = parse_scalar(value)
            continue

        upcoming = next_meaningful(index)
        next_container: Any = {}
        if upcoming is not None:
            next_indent = len(upcoming) - len(upcoming.lstrip(" "))
            if next_indent > indent and upcoming.strip().startswith("- "):
                next_container = []

        if isinstance(container, list):
            raise ValueError(f"unexpected nested mapping near line {index + 1}")
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


def iter_rust_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.rs"):
        if "target" in path.parts:
            continue
        yield path


class LoopForgeRunner:
    def __init__(
        self,
        workspace_root: Path,
        work_dir: Path,
        source_root: Path,
        result_dir: Path,
        log_dir: Path,
    ) -> None:
        self.workspace_root = workspace_root.resolve()
        self.work_dir = work_dir.resolve()
        self.source_root = source_root.resolve()
        self.result_dir = result_dir.resolve()
        self.log_dir = log_dir.resolve()
        self.trace_dir = self.log_dir / "trace"
        self.c2rust_trace_dir = self.trace_dir / "c2rust"
        self.result_output_path = self.result_dir / "output.md"
        self.issue_summary_path = self.result_dir / "issues" / "00-summary.md"
        self.interaction_log_path = self.log_dir / "interaction.md"
        self.final_report_path = self.trace_dir / "final-report.md"
        self.run_summary_path = self.trace_dir / "run-summary.json"
        self.source_inventory_path = self.c2rust_trace_dir / "01-source-inventory.md"
        self.api_mapping_path = self.c2rust_trace_dir / "02-api-mapping.md"
        self.migration_plan_path = self.c2rust_trace_dir / "03-migration-plan.md"
        self.test_mapping_path = self.c2rust_trace_dir / "04-test-mapping.md"
        self.migration_summary_path = self.c2rust_trace_dir / "05-migration-summary.md"
        self.verification_report_path = self.c2rust_trace_dir / "06-verification-report.md"
        self.unsafe_ratio_path = self.c2rust_trace_dir / "unsafe-ratio.json"
        self.flashdb_rust_dir = self.workspace_root / "flashDB_rust"
        self.config_path = self.work_dir / "loopforge.config.yaml"
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        return parse_simple_yaml(self.config_path.read_text(encoding="utf-8"))

    def ensure_outputs(self) -> None:
        self.result_dir.mkdir(parents=True, exist_ok=True)
        (self.result_dir / "issues").mkdir(parents=True, exist_ok=True)
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.c2rust_trace_dir.mkdir(parents=True, exist_ok=True)
        if not self.interaction_log_path.exists():
            self.interaction_log_path.write_text("# Interaction Log\n\nNo manual interaction.\n", encoding="utf-8")
        self.ensure_placeholder(self.result_output_path, "# Output\n\nNot executed yet.\n")
        self.ensure_placeholder(self.issue_summary_path, "# Issue Summary\n\nNot executed yet.\n")
        self.ensure_placeholder(self.source_inventory_path, "# Source Inventory\n\nNot executed yet.\n")
        self.ensure_placeholder(self.api_mapping_path, "# API Mapping\n\nNot executed yet.\n")
        self.ensure_placeholder(self.migration_plan_path, "# Migration Plan\n\nNot executed yet.\n")
        self.ensure_placeholder(self.test_mapping_path, "# Test Mapping\n\nNot executed yet.\n")
        self.ensure_placeholder(self.migration_summary_path, "# Migration Summary\n\nNot executed yet.\n")
        self.ensure_placeholder(self.verification_report_path, "# Verification Report\n\nNot executed yet.\n")
        if not self.unsafe_ratio_path.exists():
            self.unsafe_ratio_path.write_text(
                json.dumps(
                    {
                        "project": str(self.flashdb_rust_dir),
                        "total_code_lines": 0,
                        "unsafe_lines": 0,
                        "unsafe_ratio": 0.0,
                        "max_ratio": 0.10,
                        "passed": False,
                        "files": [],
                        "generated_at": utc_now(),
                    },
                    indent=2,
                    ensure_ascii=True,
                )
                + "\n",
                encoding="utf-8",
            )

    def ensure_placeholder(self, path: Path, content: str) -> None:
        if not path.exists():
            path.write_text(content, encoding="utf-8")

    def save_json(self, path: Path, payload: Dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    def required_work_items(self) -> List[str]:
        required = ["INSTRUCTION.md", "README.md"]
        required.extend(f"work/{item}" for item in REQUIRED_WORK_FILES)
        required.extend(f"work/{item}" for item in REQUIRED_ADAPTER_FILES)
        required.extend(f"work/{item}" for item in REQUIRED_SUBAGENT_FILES)
        return required

    def self_check(self) -> Dict[str, Any]:
        self.ensure_outputs()
        missing: List[str] = []
        for relative in self.required_work_items():
            candidate = self.workspace_root / relative
            if not candidate.exists():
                missing.append(relative)
        payload = {
            "ok": not missing,
            "workspace_root": str(self.workspace_root),
            "source_root": str(self.source_root),
            "missing": missing,
            "checked_at": utc_now(),
        }
        return payload

    def validate_source_readme(self, source_root: Path) -> Path:
        for name in README_CANDIDATES:
            candidate = source_root / name
            if candidate.is_file():
                return candidate
        raise FileNotFoundError("source README not found")

    def resolve_flashdb_source(self, source_root: Path) -> Path:
        direct_root = source_root
        nested_root = source_root / "FlashDB"
        for candidate in [direct_root, nested_root]:
            if (candidate / "src").is_dir() and (candidate / "tests").is_dir():
                return candidate
        raise FileNotFoundError("FlashDB source layout not found under SOURCE_ROOT")

    def validate_flashdb_source_layout(self, flashdb_root: Path) -> None:
        missing = [name for name in ["src", "tests"] if not (flashdb_root / name).is_dir()]
        if missing:
            raise FileNotFoundError(f"missing required FlashDB directories: {', '.join(missing)}")

    def collect_relative_files(self, root: Path, suffix: str) -> List[str]:
        return sorted(str(path.relative_to(root)).replace("\\", "/") for path in root.rglob(f"*{suffix}") if path.is_file())

    def write_source_inventory(self, source_root: Path, flashdb_root: Path, readme_path: Path) -> None:
        src_files = self.collect_relative_files(flashdb_root / "src", ".c") + self.collect_relative_files(flashdb_root / "src", ".h")
        test_files = self.collect_relative_files(flashdb_root / "tests", ".c") + self.collect_relative_files(flashdb_root / "tests", ".h")
        lines = [
            "# Source Inventory",
            "",
            f"- selected_readme: `{readme_path}`",
            f"- source_root: `{source_root}`",
            f"- resolved_flashdb_root: `{flashdb_root}`",
            "",
            "## Source Files",
            "",
        ]
        lines.extend([f"- `{item}`" for item in src_files] or ["- No C source files detected under `src/`."])
        lines.extend(["", "## Test Files", ""])
        lines.extend([f"- `{item}`" for item in test_files] or ["- No C test files detected under `tests/`."])
        lines.extend(
            [
                "",
                "## Detected Boundaries",
                "",
                "- Public APIs: inventory required during implementation stage.",
                "- Data structures: inventory required during implementation stage.",
                "- Storage and I/O boundaries: inventory required during implementation stage.",
                "",
            ]
        )
        self.source_inventory_path.write_text("\n".join(lines), encoding="utf-8")

    def write_api_mapping_placeholder(self, readme_path: Path, flashdb_root: Path) -> None:
        lines = [
            "# API Mapping",
            "",
            f"- selected_readme: `{readme_path}`",
            f"- resolved_flashdb_root: `{flashdb_root}`",
            "",
            "## Planned Mapping",
            "",
            "- C API to Rust module mapping: pending implementation.",
            "- Data model mapping: pending implementation.",
            "- Error/result strategy: use `Result` and explicit error types.",
            "- Ownership strategy: safe ownership-first translation.",
            "- Unsafe avoidance strategy: avoid `unsafe` unless a boundary cannot be expressed safely.",
            "",
        ]
        self.api_mapping_path.write_text("\n".join(lines), encoding="utf-8")

    def write_test_mapping_placeholder(self, flashdb_root: Path) -> None:
        test_files = self.collect_relative_files(flashdb_root / "tests", ".c")
        lines = [
            "# Test Mapping",
            "",
            f"- resolved_flashdb_root: `{flashdb_root}`",
            "",
            "## C Test Scenarios",
            "",
        ]
        lines.extend([f"- `{item}` -> pending Rust equivalent" for item in test_files] or ["- No C tests detected."])
        lines.append("")
        self.test_mapping_path.write_text("\n".join(lines), encoding="utf-8")

    def write_migration_summary(self, detect_payload: Dict[str, Any]) -> None:
        lines = [
            "# Migration Summary",
            "",
            f"- generated_at: `{utc_now()}`",
            f"- source_root: `{detect_payload.get('source_root', '')}`",
            f"- flashdb_root: `{detect_payload.get('flashdb_root', '')}`",
            "",
            "## Status",
            "",
            "- This branch is customized for the FlashDB C-to-Rust workflow.",
            "- Rust project generation is expected at `flashDB_rust/`.",
            "- Verification will fail closed if the generated Rust project does not exist.",
            "",
        ]
        self.migration_summary_path.write_text("\n".join(lines), encoding="utf-8")

    def detect_project(self) -> Dict[str, Any]:
        self.ensure_outputs()
        try:
            readme_path = self.validate_source_readme(self.source_root)
            flashdb_root = self.resolve_flashdb_source(self.source_root)
            self.validate_flashdb_source_layout(flashdb_root)
            self.write_source_inventory(self.source_root, flashdb_root, readme_path)
            self.write_api_mapping_placeholder(readme_path, flashdb_root)
            self.write_test_mapping_placeholder(flashdb_root)
            payload = {
                "ok": True,
                "source_root": str(self.source_root),
                "selected_readme": str(readme_path),
                "flashdb_root": str(flashdb_root),
                "checked_at": utc_now(),
            }
        except Exception as exc:
            payload = {
                "ok": False,
                "source_root": str(self.source_root),
                "reason": str(exc),
                "checked_at": utc_now(),
            }
        self.write_migration_summary(payload)
        return payload

    def validate_c2rust_output(self, repo_root: Path) -> None:
        project_root = repo_root / "flashDB_rust"
        missing: List[str] = []
        for relative in ["Cargo.toml", "src", "tests"]:
            if not (project_root / relative).exists():
                missing.append(f"flashDB_rust/{relative}")
        if missing:
            raise FileNotFoundError(f"missing generated Rust output: {', '.join(missing)}")

    def run_command(self, command: List[str], cwd: Path, timeout_seconds: int) -> CommandResult:
        try:
            completed = subprocess.run(
                command,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            return CommandResult(
                command=" ".join(command),
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        except FileNotFoundError as exc:
            return CommandResult(" ".join(command), 127, "", "", error=str(exc))
        except subprocess.TimeoutExpired as exc:
            return CommandResult(" ".join(command), 124, exc.stdout or "", exc.stderr or "", error="timeout")

    def run_cargo_verification(self, repo_root: Path, timeout_seconds: int) -> Dict[str, Any]:
        project_root = repo_root / "flashDB_rust"
        results: List[Dict[str, Any]] = []
        for command in [["cargo", "build"], ["cargo", "test"]]:
            result = self.run_command(command, project_root, timeout_seconds)
            results.append(
                {
                    "command": result.command,
                    "ok": result.returncode == 0 and result.error is None,
                    "returncode": result.returncode,
                    "error": result.error,
                    "stdout_tail": result.stdout.strip().splitlines()[-20:],
                    "stderr_tail": result.stderr.strip().splitlines()[-20:],
                }
            )
            if result.returncode != 0 or result.error is not None:
                return {"ok": False, "working_directory": str(project_root), "commands": results}
        return {"ok": True, "working_directory": str(project_root), "commands": results}

    def check_unsafe_ratio(self, repo_root: Path, max_ratio: float = 0.10) -> Dict[str, Any]:
        project_root = repo_root / "flashDB_rust"
        total_lines = 0
        unsafe_lines = 0
        files: List[Dict[str, Any]] = []
        for rust_file in iter_rust_files(project_root):
            file_total = 0
            file_unsafe = 0
            for line in rust_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("//"):
                    continue
                file_total += 1
                if "unsafe" in stripped:
                    file_unsafe += 1
            total_lines += file_total
            unsafe_lines += file_unsafe
            files.append(
                {
                    "file": str(rust_file),
                    "code_lines": file_total,
                    "unsafe_lines": file_unsafe,
                }
            )
        ratio = (unsafe_lines / total_lines) if total_lines else 0.0
        payload = {
            "project": str(project_root),
            "total_code_lines": total_lines,
            "unsafe_lines": unsafe_lines,
            "unsafe_ratio": ratio,
            "max_ratio": max_ratio,
            "passed": ratio < max_ratio,
            "files": files,
            "generated_at": utc_now(),
        }
        self.unsafe_ratio_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        return payload

    def assert_no_source_root_artifacts(self, source_root: Path) -> None:
        forbidden_paths = [source_root / ".loopforge"]
        if source_root.name == "code":
            forbidden_paths.append(source_root / ".loopforge")
        offenders = [str(path) for path in forbidden_paths if path.exists()]
        if offenders:
            raise RuntimeError(f"forbidden runtime artifacts detected under SOURCE_ROOT: {', '.join(offenders)}")

    def verify(self) -> Dict[str, Any]:
        self.ensure_outputs()
        timeout_seconds = int(self.config.get("verification", {}).get("timeout_seconds", 600) or 600)
        detect_payload = self.detect_project()
        report_lines = [
            "# Verification Report",
            "",
            f"- generated_at: `{utc_now()}`",
            f"- source_root: `{self.source_root}`",
            "",
        ]
        if not detect_payload.get("ok"):
            report_lines.extend(["## Result", "", "BLOCKED_WITH_REPORT", "", f"- reason: {detect_payload.get('reason', 'unknown')}", ""])
            self.verification_report_path.write_text("\n".join(report_lines), encoding="utf-8")
            return {"ok": False, "status": "BLOCKED_WITH_REPORT", "reason": detect_payload.get("reason", "detect failed")}

        try:
            self.validate_c2rust_output(self.workspace_root)
            cargo_payload = self.run_cargo_verification(self.workspace_root, timeout_seconds)
            if not cargo_payload.get("ok"):
                report_lines.extend(["## Cargo Verification", "", json.dumps(cargo_payload, indent=2, ensure_ascii=True), ""])
                self.verification_report_path.write_text("\n".join(report_lines), encoding="utf-8")
                return {"ok": False, "status": "BLOCKED_WITH_REPORT", "reason": "cargo verification failed", "cargo": cargo_payload}
            unsafe_payload = self.check_unsafe_ratio(self.workspace_root)
            if not unsafe_payload.get("passed"):
                report_lines.extend(["## Unsafe Ratio", "", json.dumps(unsafe_payload, indent=2, ensure_ascii=True), ""])
                self.verification_report_path.write_text("\n".join(report_lines), encoding="utf-8")
                return {"ok": False, "status": "BLOCKED_WITH_REPORT", "reason": "unsafe ratio is too high", "unsafe": unsafe_payload}
            self.assert_no_source_root_artifacts(self.source_root)
            payload = {
                "ok": True,
                "status": "READY_FOR_EVALUATION",
                "cargo": cargo_payload,
                "unsafe": unsafe_payload,
            }
            report_lines.extend(["## Result", "", "READY_FOR_EVALUATION", "", "## Cargo Verification", "", json.dumps(cargo_payload, indent=2, ensure_ascii=True), "", "## Unsafe Ratio", "", json.dumps(unsafe_payload, indent=2, ensure_ascii=True), ""])
            self.verification_report_path.write_text("\n".join(report_lines), encoding="utf-8")
            return payload
        except Exception as exc:
            report_lines.extend(["## Result", "", "BLOCKED_WITH_REPORT", "", f"- reason: {exc}", ""])
            self.verification_report_path.write_text("\n".join(report_lines), encoding="utf-8")
            return {"ok": False, "status": "BLOCKED_WITH_REPORT", "reason": str(exc)}

    def finalize(self, detect_payload: Optional[Dict[str, Any]] = None, verify_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.ensure_outputs()
        detect_payload = detect_payload or self.detect_project()
        verify_payload = verify_payload or self.verify()
        final_status = "READY_FOR_EVALUATION" if verify_payload.get("ok") else "BLOCKED_WITH_REPORT"
        lines = [
            "# LoopForge Final Report",
            "",
            f"- generated_at: `{utc_now()}`",
            f"- final_status: `{final_status}`",
            f"- source_root: `{self.source_root}`",
            f"- flashdb_rust: `{self.flashdb_rust_dir}`",
            "",
            "## Detection",
            "",
            json.dumps(detect_payload, indent=2, ensure_ascii=True),
            "",
            "## Verification",
            "",
            json.dumps(verify_payload, indent=2, ensure_ascii=True),
            "",
            "## Output Contract",
            "",
            "- trace_dir: `logs/trace/`",
            "- migration_dir: `logs/trace/c2rust/`",
            "- result_output: `result/output.md`",
            "- issue_summary: `result/issues/00-summary.md`",
            "- generated_project: `flashDB_rust/`",
            "",
            "## Boundaries",
            "",
            "- SOURCE_ROOT is read-only.",
            "- Runtime evidence must stay under `logs/trace/`.",
            "- Generated Rust output must stay under `flashDB_rust/` at repository root.",
            "",
        ]
        self.final_report_path.write_text("\n".join(lines), encoding="utf-8")
        return {"ok": True, "status": final_status, "report": str(self.final_report_path)}

    def write_entrypoint_result(self, detect_payload: Dict[str, Any], verify_payload: Dict[str, Any], finalize_payload: Dict[str, Any]) -> Dict[str, Any]:
        status = finalize_payload.get("status", "BLOCKED_WITH_REPORT")
        unsafe_ratio = "n/a"
        if isinstance(verify_payload.get("unsafe"), dict):
            unsafe_ratio = f"{verify_payload['unsafe'].get('unsafe_ratio', 0.0):.4f}"
        output_lines = [
            "# Output",
            "",
            f"- status: `{status}`",
            f"- source_root: `{self.source_root}`",
            f"- selected_readme: `{detect_payload.get('selected_readme', 'n/a')}`",
            f"- flashdb_root: `{detect_payload.get('flashdb_root', 'n/a')}`",
            f"- rust_project: `{self.flashdb_rust_dir}`",
            f"- cargo_build_test: `{'passed' if verify_payload.get('ok') else 'not passed'}`",
            f"- unsafe_ratio: `{unsafe_ratio}`",
            "",
            "## Summary",
            "",
            "- This branch is customized for FlashDB C-to-Rust migration execution.",
            "- Verification only succeeds when `flashDB_rust/` exists and passes `cargo build` plus `cargo test`.",
            "",
        ]
        if not verify_payload.get("ok"):
            output_lines.extend(["## Blocking Reason", "", f"- {verify_payload.get('reason', 'unknown')}", ""])
        self.result_output_path.write_text("\n".join(output_lines), encoding="utf-8")

        issue_lines = [
            "# Issue Summary",
            "",
        ]
        if verify_payload.get("ok"):
            issue_lines.extend(["- No blocking issues detected by the contest driver.", ""])
        else:
            issue_lines.extend(
                [
                    f"- blocking_reason: {verify_payload.get('reason', 'unknown')}",
                    "- known_missing_behavior: actual FlashDB-to-Rust implementation is not generated by this customization step.",
                    "- degraded_compatibility: verification remains blocked until a real `flashDB_rust/` project is present.",
                    "- serious_risk: running without contest-provided FlashDB source cannot validate end-to-end behavior.",
                    "",
                ]
            )
        self.issue_summary_path.write_text("\n".join(issue_lines), encoding="utf-8")

        run_summary = {
            "generated_at": utc_now(),
            "source_root": str(self.source_root),
            "detect": detect_payload,
            "verify": verify_payload,
            "finalize": finalize_payload,
            "result_output": str(self.result_output_path),
            "issue_summary": str(self.issue_summary_path),
            "final_report": str(self.final_report_path),
        }
        self.save_json(self.run_summary_path, run_summary)
        return run_summary

    def run_entrypoint(self) -> Dict[str, Any]:
        self.ensure_outputs()
        self_check_payload = self.self_check()
        detect_payload = self.detect_project()
        verify_payload = self.verify()
        finalize_payload = self.finalize(detect_payload, verify_payload)
        self.write_entrypoint_result(detect_payload, verify_payload, finalize_payload)
        return {
            "ok": self_check_payload.get("ok", False) and finalize_payload.get("status") in {"READY_FOR_EVALUATION", "BLOCKED_WITH_REPORT"},
            "self_check": self_check_payload,
            "detect": detect_payload,
            "verify": verify_payload,
            "finalize": finalize_payload,
        }


def resolve_path(base: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = (base / path).resolve()
    return path.resolve()


def resolve_default_source_root(workspace_root: Path) -> Path:
    if os.name != "nt":
        for candidate in [
            Path("/__CONTEST_PLATFORM_SOURCE_ROOT__/source"),
            Path("/__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB"),
            Path("/__CONTEST_PLATFORM_SOURCE_ROOT__"),
        ]:
            if candidate.exists():
                return candidate.resolve()
    return (workspace_root / "code").resolve()


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LoopForge C2Rust runner")
    parser.add_argument("--work-dir", default="work")
    parser.add_argument("--source-root")
    parser.add_argument("--result-dir", default="result")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--detect", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--run", action="store_true")
    return parser.parse_args(argv)


def print_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True))


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    if not any([args.init, args.self_check, args.detect, args.verify, args.finalize, args.run]):
        print("No action provided.", file=sys.stderr)
        return 2

    cwd = Path.cwd().resolve()
    work_dir = resolve_path(cwd, args.work_dir)
    workspace_root = work_dir.parent
    source_arg = (args.source_root or os.environ.get("SOURCE_ROOT", "")).strip()
    source_root = resolve_path(workspace_root, source_arg) if source_arg else resolve_default_source_root(workspace_root)
    result_dir = resolve_path(cwd, args.result_dir)
    log_dir = resolve_path(cwd, args.log_dir)
    runner = LoopForgeRunner(workspace_root, work_dir, source_root, result_dir, log_dir)

    try:
        if args.init:
            print_json({"ok": True, "status": "initialized", "source_root": str(source_root)})
        if args.self_check:
            print_json(runner.self_check())
        if args.detect:
            print_json(runner.detect_project())
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
