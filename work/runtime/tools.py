#!/usr/bin/env python3
"""Unified CLI for C-to-Rust migration tools — zero-judgment data layer.

All subcommands return only raw data. No pass/fail, no gate, no threshold.
Output: {"ok": bool, "command": str, "data": {...}}
Exit: 0 = tool succeeded, 1 = tool error (bad args, missing deps, import failure).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------

def _out(result: Dict[str, Any]) -> None:
    print(json.dumps(result, indent=2, ensure_ascii=False))


def _die(command: str, message: str) -> None:
    _out({"ok": False, "command": command, "error": message})
    sys.exit(1)


def _ok(command: str, data: Any) -> None:
    _out({"ok": True, "command": command, "data": data})


def _read_line(file_path: str, line_no: int) -> str:
    try:
        lines = Path(file_path).read_text(encoding="utf-8", errors="ignore").splitlines()
        return lines[line_no - 1].strip() if 1 <= line_no <= len(lines) else ""
    except (OSError, ValueError):
        return ""


def _resolve_output(path_str: str) -> Path:
    p = Path(path_str)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------------------
# parse-source
# ---------------------------------------------------------------------------

def cmd_parse_source(args: argparse.Namespace) -> None:
    from source_analysis import build_complete_analysis

    source_root = Path(args.source_root)
    if not source_root.is_dir():
        _die("parse-source", f"source-root does not exist: {source_root}")

    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    # resolve test directories
    test_dirs: List[str] = []
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

    # minimal packet stub — supplies layout metadata expected by source_analysis
    class _Packet:
        metadata: Dict[str, Any]
        def __init__(self, root: Path, tdirs: List[str]) -> None:
            self.metadata = {
                "layout_resolution": {
                    "source_dirs": [str(root)],
                    "test_dirs": tdirs,
                },
                "source_analysis": {"preprocessor_variants": []},
            }

    packet = _Packet(source_root, test_dirs)
    legacy = {
        "project_root": str(source_root),
        "public_apis": [],
        "functions": [],
        "test_files": [],
    }

    bundle = build_complete_analysis(packet, legacy)
    artifacts: Dict[str, Any] = bundle.get("artifacts", {})

    # extract raw data — no verification pass/fail
    inventory = artifacts.get("source-inventory.json", {})
    call_graph = artifacts.get("call-graph.json", {})
    public_api = artifacts.get("public-api-map.json", {})
    type_map = artifacts.get("type-map.json", {})
    globals_map = artifacts.get("global-state-map.json", {})
    preprocessor = artifacts.get("preprocessor-variants.json", {})
    analysis_verif = artifacts.get("analysis-verification.json", {})

    data = {
        "files": inventory.get("files", []),
        "source_tests": inventory.get("source_tests", []),
        "public_apis": public_api.get("apis", []),
        "functions": call_graph.get("functions", []),
        "test_functions": inventory.get("test_functions", []),
        "types": type_map.get("types", []),
        "call_graph": call_graph.get("call_edges", []),
        "globals": globals_map.get("globals", []),
        "preprocessor_variants": {
            k: v for k, v in preprocessor.items()
            if k not in ("required_variants", "compile_database")
        },
        "parse_failures": analysis_verif.get("parse_failures", []),
    }

    if args.output:
        out_path = _resolve_output(args.output)
        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        _ok("parse-source", {"written": str(out_path), "file_count": len(data["files"])})
    else:
        _ok("parse-source", data)


# ---------------------------------------------------------------------------
# run-verification
# ---------------------------------------------------------------------------

def cmd_run_verification(args: argparse.Namespace) -> None:
    commands = json.loads(args.commands)
    if not isinstance(commands, list) or not all(isinstance(c, str) for c in commands):
        _die("run-verification", "--commands must be a JSON array of strings")

    project_dir = Path(args.project_dir)
    if not project_dir.is_dir():
        _die("run-verification", f"project-dir does not exist: {project_dir}")

    timeout: int = args.timeout
    results: List[Dict[str, Any]] = []

    for cmd_str in commands:
        try:
            completed = subprocess.run(
                cmd_str, shell=True, cwd=str(project_dir),
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

    _ok("run-verification", {"results": results})


# ---------------------------------------------------------------------------
# check-unsafe
# ---------------------------------------------------------------------------

def cmd_check_unsafe(args: argparse.Namespace) -> None:
    from check_unsafe_ratio import count_unsafe

    project_dir = Path(args.project_dir)
    if not project_dir.is_dir():
        _die("check-unsafe", f"project-dir does not exist: {project_dir}")

    result = count_unsafe(project_dir)

    if args.output:
        out_path = _resolve_output(args.output)
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        _ok("check-unsafe", {"written": str(out_path), "ratio": result["ratio"]})
    else:
        _ok("check-unsafe", result)


# ---------------------------------------------------------------------------
# fault-injection
# ---------------------------------------------------------------------------

def cmd_fault_injection(args: argparse.Namespace) -> None:
    from test_migration_validation import (
        run_mutation_testing, FIXED_MUTATIONS, scan_assertions,
    )

    project_dir = Path(args.project_dir)
    if not project_dir.is_dir():
        _die("fault-injection", f"project-dir does not exist: {project_dir}")

    trace_dir = Path(args.trace_dir)
    trace_dir.mkdir(parents=True, exist_ok=True)

    mutations: List[str] = json.loads(args.mutations) if args.mutations else list(FIXED_MUTATIONS)

    mutation_report = run_mutation_testing(mutations=mutations)
    assertion_scan = scan_assertions(project_dir)

    trace_data = {"mutations": mutation_report, "assertion_scan": assertion_scan}
    trace_path = trace_dir / "fault-injection-trace.json"
    trace_path.write_text(json.dumps(trace_data, indent=2, ensure_ascii=False), encoding="utf-8")

    _ok("fault-injection", {
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


# ---------------------------------------------------------------------------
# neutrality-audit
# ---------------------------------------------------------------------------

def cmd_neutrality_audit(args: argparse.Namespace) -> None:
    from test_migration_validation import scan_project_customization
    import glob as _glob

    paths_raw: List[str] = json.loads(args.paths)
    forbidden: List[str] = json.loads(args.forbidden_terms)

    expanded: List[Path] = []
    for pattern in paths_raw:
        for match in _glob.glob(pattern, recursive=True):
            expanded.append(Path(match))

    result = scan_project_customization(expanded, forbidden)

    hits: List[Dict[str, Any]] = []
    for category in ("findings", "adjudications"):
        for item in result.get(category, []):
            file_path = item.get("file", "")
            line_no = item.get("line", 0)
            context = _read_line(file_path, line_no)
            for term in item.get("terms", []):
                hits.append({
                    "file": file_path,
                    "line": line_no,
                    "term": term,
                    "context": context,
                })

    _ok("neutrality-audit", {
        "files_scanned": len(expanded),
        "hits": hits,
        "finding_count": len(result.get("findings", [])),
        "adjudication_count": len(result.get("adjudications", [])),
    })


# ---------------------------------------------------------------------------
# write-report
# ---------------------------------------------------------------------------

def _default_template(data: Dict[str, Any]) -> str:
    lines: List[str] = ["# Report", ""]
    for key, value in data.items():
        lines.append(f"## {key}")
        lines.append("")
        if isinstance(value, (dict, list)):
            lines.append(f"```json\n{json.dumps(value, indent=2, ensure_ascii=False)}\n```")
        else:
            lines.append(str(value))
        lines.append("")
    return "\n".join(lines)


def cmd_write_report(args: argparse.Namespace) -> None:
    result_dir = Path(args.result_dir)
    result_dir.mkdir(parents=True, exist_ok=True)

    if args.data:
        data = json.loads(args.data)
    elif not sys.stdin.isatty():
        data = json.loads(sys.stdin.read())
    else:
        _die("write-report", "no data provided via --data or stdin")

    if args.template:
        template_path = Path(args.template)
        if not template_path.is_file():
            _die("write-report", f"template not found: {template_path}")
        template = template_path.read_text(encoding="utf-8")
    else:
        template = _default_template(data)

    # placeholder substitution: {{key}} -> value
    for key, value in data.items():
        placeholder = "{{" + key + "}}"
        if placeholder in template:
            replacement = (
                json.dumps(value, indent=2, ensure_ascii=False)
                if isinstance(value, (dict, list))
                else str(value)
            )
            template = template.replace(placeholder, replacement)

    output_path = result_dir / "output.md"
    output_path.write_text(template, encoding="utf-8")
    _ok("write-report", {"output_path": str(output_path)})


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        prog="tools",
        description="Unified CLI for C-to-Rust migration tools. JSON output, zero judgment.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # parse-source
    p = sub.add_parser("parse-source", help="Parse C source into structured inventory")
    p.add_argument("--source-root", required=True)
    p.add_argument("--test-dirs", default="")
    p.add_argument("--work-dir", default="work")
    p.add_argument("--output", help="Write JSON to file instead of stdout")

    # run-verification
    p = sub.add_parser("run-verification", help="Execute build/test commands, return raw results")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--commands", required=True, help='JSON array, e.g. \'["cargo build"]\'')
    p.add_argument("--timeout", type=int, default=300)

    # check-unsafe
    p = sub.add_parser("check-unsafe", help="Count unsafe code lines, return ratio only")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--output", help="Write JSON to file instead of stdout")

    # fault-injection
    p = sub.add_parser("fault-injection", help="Run fault injection, return raw results")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--trace-dir", default="logs/trace")
    p.add_argument("--mutations", help="JSON array of mutation types")

    # neutrality-audit
    p = sub.add_parser("neutrality-audit", help="Scan files for forbidden terms")
    p.add_argument("--paths", required=True, help='JSON array of globs, e.g. \'["src/**/*.rs"]\'')
    p.add_argument("--forbidden-terms", required=True, help='JSON array of terms')

    # write-report
    p = sub.add_parser("write-report", help="Write structured data to markdown report")
    p.add_argument("--result-dir", required=True)
    p.add_argument("--data", help="JSON string (or pipe via stdin)")
    p.add_argument("--template", help="Custom markdown template path")

    args = parser.parse_args(argv)

    dispatch = {
        "parse-source": cmd_parse_source,
        "run-verification": cmd_run_verification,
        "check-unsafe": cmd_check_unsafe,
        "fault-injection": cmd_fault_injection,
        "neutrality-audit": cmd_neutrality_audit,
        "write-report": cmd_write_report,
    }

    try:
        dispatch[args.command](args)
    except Exception as exc:
        _die(args.command, f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
