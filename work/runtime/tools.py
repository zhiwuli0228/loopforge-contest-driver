#!/usr/bin/env python3
"""Unified CLI entry point for C-to-Rust migration tools.

All subcommands return raw data only — no pass/fail judgment.
Output format: {"ok": bool, "command": str, "data": {...}}
Exit codes: 0 = tool executed successfully, 1 = tool error (bad args, missing deps).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict


def _read_line_context(file_path: str, line_no: int) -> str:
    try:
        lines = Path(file_path).read_text(encoding="utf-8", errors="ignore").splitlines()
        if 1 <= line_no <= len(lines):
            return lines[line_no - 1].strip()
    except (OSError, ValueError):
        pass
    return ""


def _output(result: Dict[str, Any]) -> None:
    print(json.dumps(result, indent=2, ensure_ascii=False))


def _error(command: str, message: str) -> None:
    _output({"ok": False, "command": command, "error": message})
    sys.exit(1)


def _success(command: str, data: Any) -> None:
    _output({"ok": True, "command": command, "data": data})


def cmd_parse_source(args: argparse.Namespace) -> None:
    from source_analysis import build_complete_analysis, snapshot_source_tree
    source_root = Path(args.source_root)
    if not source_root.is_dir():
        _error("parse-source", f"source-root does not exist: {source_root}")
    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    test_dirs = []
    if args.test_dirs:
        for td in args.test_dirs.split(","):
            td = td.strip()
            if not td:
                continue
            p = Path(td)
            if not p.is_absolute():
                p = source_root / p
            if p.is_dir():
                test_dirs.append(str(p))
    class _Packet:
        def __init__(self, root: Path, tdirs: list):
            self.metadata = {
                "layout_resolution": {
                    "source_dirs": [str(root)],
                    "test_dirs": tdirs,
                },
                "source_analysis": {"preprocessor_variants": []},
            }
    packet = _Packet(source_root, test_dirs)
    legacy = {"project_root": str(source_root), "public_apis": [], "functions": [], "test_files": []}
    bundle = build_complete_analysis(packet, legacy)
    artifacts = bundle.get("artifacts", {})
    functions = artifacts.get("call-graph.json", {}).get("functions", [])
    test_functions = artifacts.get("source-inventory.json", {}).get("test_functions", [])
    result = {
        "files": artifacts.get("source-inventory.json", {}).get("files", []),
        "source_tests": artifacts.get("source-inventory.json", {}).get("source_tests", []),
        "public_apis": artifacts.get("public-api-map.json", {}).get("apis", []),
        "functions": functions,
        "test_functions": test_functions,
        "types": artifacts.get("type-map.json", {}).get("types", []),
        "call_graph": artifacts.get("call-graph.json", {}).get("call_edges", []),
        "globals": artifacts.get("global-state-map.json", {}).get("globals", []),
        "preprocessor_variants": artifacts.get("preprocessor-variants.json", {}),
        "parse_failures": artifacts.get("analysis-verification.json", {}).get("parse_failures", []),
    }
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        _success("parse-source", {"written": str(out_path), "file_count": len(result["files"])})
    else:
        _success("parse-source", result)


def cmd_run_verification(args: argparse.Namespace) -> None:
    import subprocess
    commands = json.loads(args.commands)
    if not isinstance(commands, list):
        _error("run-verification", "--commands must be a JSON array of strings")
    project_dir = Path(args.project_dir)
    if not project_dir.is_dir():
        _error("run-verification", f"project-dir does not exist: {project_dir}")
    timeout = args.timeout
    results = []
    for cmd_str in commands:
        try:
            completed = subprocess.run(
                cmd_str, shell=True, cwd=project_dir,
                capture_output=True, text=True, timeout=timeout,
            )
            results.append({
                "command": cmd_str,
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "timed_out": False,
            })
        except subprocess.TimeoutExpired:
            results.append({
                "command": cmd_str,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Timed out after {timeout}s",
                "timed_out": True,
            })
    _success("run-verification", {"results": results})


def cmd_check_unsafe(args: argparse.Namespace) -> None:
    from check_unsafe_ratio import iter_rust_files
    project_dir = Path(args.project_dir)
    if not project_dir.is_dir():
        _error("check-unsafe", f"project-dir does not exist: {project_dir}")
    total_lines = 0
    unsafe_lines = 0
    files = []
    for rust_file in iter_rust_files(project_dir):
        file_total = 0
        file_unsafe = 0
        for line in rust_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue
            file_total += 1
            if "unsafe" in stripped and "unsafe_code" not in stripped:
                file_unsafe += 1
        total_lines += file_total
        unsafe_lines += file_unsafe
        files.append({"file": str(rust_file), "code_lines": file_total, "unsafe_lines": file_unsafe})
    ratio = (unsafe_lines / total_lines) if total_lines else 0.0
    result = {"total_files": len(files), "unsafe_lines": unsafe_lines, "total_code_lines": total_lines, "ratio": ratio, "per_file": files}
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        _success("check-unsafe", {"written": str(out_path), "ratio": ratio})
    else:
        _success("check-unsafe", result)


def cmd_fault_injection(args: argparse.Namespace) -> None:
    from test_migration_validation import (
        run_mutation_testing, FIXED_MUTATIONS, scan_assertions,
    )
    project_dir = Path(args.project_dir)
    if not project_dir.is_dir():
        _error("fault-injection", f"project-dir does not exist: {project_dir}")
    trace_dir = Path(args.trace_dir)
    trace_dir.mkdir(parents=True, exist_ok=True)
    mutations = json.loads(args.mutations) if args.mutations else list(FIXED_MUTATIONS)
    mutation_report = run_mutation_testing(mutations=mutations)
    assertion_scan = scan_assertions(project_dir)
    trace_data = {"mutations": mutation_report, "assertion_scan": assertion_scan}
    trace_path = trace_dir / "fault-injection-trace.json"
    trace_path.write_text(json.dumps(trace_data, indent=2, ensure_ascii=False), encoding="utf-8")
    _success("fault-injection", {
        "trace_file": str(trace_path),
        "mutations": mutation_report.get("mutations", []),
        "survivors": mutation_report.get("survivors", []),
        "mutation_count": mutation_report.get("metrics", {}).get("mutation_count", 0),
        "survivor_count": mutation_report.get("metrics", {}).get("survivor_count", 0),
        "assertion_scan": {
            "tests": assertion_scan.get("tests", []),
            "effective_assertions": assertion_scan.get("effective_assertions", []),
            "findings": assertion_scan.get("findings", []),
        },
    })


def cmd_neutrality_audit(args: argparse.Namespace) -> None:
    from test_migration_validation import scan_project_customization
    import glob as glob_mod
    paths_raw = json.loads(args.paths)
    forbidden = json.loads(args.forbidden_terms)
    expanded: list[Path] = []
    for pattern in paths_raw:
        matches = glob_mod.glob(pattern, recursive=True)
        expanded.extend(Path(m) for m in matches)
    result = scan_project_customization(expanded, forbidden)
    hits = []
    for finding in result.get("findings", []):
        file_path = finding.get("file", "")
        line_no = finding.get("line", 0)
        context = _read_line_context(file_path, line_no)
        for term in finding.get("terms", []):
            hits.append({"file": file_path, "line": line_no, "term": term, "context": context})
    for adjudication in result.get("adjudications", []):
        file_path = adjudication.get("file", "")
        line_no = adjudication.get("line", 0)
        context = _read_line_context(file_path, line_no)
        for term in adjudication.get("terms", []):
            hits.append({"file": file_path, "line": line_no, "term": term, "context": context})
    _success("neutrality-audit", {
        "files_scanned": len(expanded),
        "hits": hits,
        "finding_count": len(result.get("findings", [])),
        "adjudication_count": len(result.get("adjudications", [])),
    })


def cmd_write_report(args: argparse.Namespace) -> None:
    result_dir = Path(args.result_dir)
    result_dir.mkdir(parents=True, exist_ok=True)
    if args.data:
        data = json.loads(args.data)
    else:
        data = json.loads(sys.stdin.read())
    if args.template:
        template_path = Path(args.template)
        if not template_path.is_file():
            _error("write-report", f"template not found: {template_path}")
        template = template_path.read_text(encoding="utf-8")
    else:
        template = _default_template(data)
    for key, value in data.items():
        placeholder = "{{" + key + "}}"
        if placeholder in template:
            template = template.replace(placeholder, json.dumps(value, indent=2, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value))
    output_path = result_dir / "output.md"
    output_path.write_text(template, encoding="utf-8")
    _success("write-report", {"output_path": str(output_path)})


def _default_template(data: Dict[str, Any]) -> str:
    lines = ["# Report", ""]
    for key, value in data.items():
        lines.append(f"## {key}")
        lines.append("")
        if isinstance(value, (dict, list)):
            lines.append(f"```json\n{json.dumps(value, indent=2, ensure_ascii=False)}\n```")
        else:
            lines.append(str(value))
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="tools",
        description="Unified CLI for C-to-Rust migration tools. Returns JSON only, no pass/fail judgment.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("parse-source", help="Parse C source directory into structured inventory")
    p.add_argument("--source-root", required=True, help="Path to C/C++ source directory")
    p.add_argument("--test-dirs", default="", help="Comma-separated test directories (relative to source-root or absolute)")
    p.add_argument("--work-dir", default="work", help="Working directory (default: work)")
    p.add_argument("--output", help="Write inventory JSON to file instead of stdout")

    p = sub.add_parser("run-verification", help="Execute build/test commands and return raw results")
    p.add_argument("--project-dir", required=True, help="Project directory to run commands in")
    p.add_argument("--commands", required=True, help='JSON array of commands, e.g. \'["cargo build"]\'')
    p.add_argument("--timeout", type=int, default=300, help="Timeout per command in seconds (default: 300)")

    p = sub.add_parser("check-unsafe", help="Count unsafe code lines in Rust project")
    p.add_argument("--project-dir", required=True, help="Path to Rust project")
    p.add_argument("--output", help="Write results to file instead of stdout")

    p = sub.add_parser("fault-injection", help="Run fault injection tests and return raw results")
    p.add_argument("--project-dir", required=True, help="Path to Rust project")
    p.add_argument("--trace-dir", default="logs/trace", help="Trace output directory")
    p.add_argument("--mutations", help='JSON array of mutation types (default: all)')

    p = sub.add_parser("neutrality-audit", help="Scan files for forbidden terms")
    p.add_argument("--paths", required=True, help='JSON array of file paths/globs, e.g. \'["src/**/*.rs"]\'')
    p.add_argument("--forbidden-terms", required=True, help='JSON array of forbidden terms')

    p = sub.add_parser("write-report", help="Write structured data to formatted report file")
    p.add_argument("--result-dir", required=True, help="Directory to write report")
    p.add_argument("--data", help='JSON string of data (or pipe via stdin)')
    p.add_argument("--template", help="Path to custom markdown template")

    args = parser.parse_args()
    try:
        {
            "parse-source": cmd_parse_source,
            "run-verification": cmd_run_verification,
            "check-unsafe": cmd_check_unsafe,
            "fault-injection": cmd_fault_injection,
            "neutrality-audit": cmd_neutrality_audit,
            "write-report": cmd_write_report,
        }[args.command](args)
    except Exception as exc:
        _error(args.command, f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
