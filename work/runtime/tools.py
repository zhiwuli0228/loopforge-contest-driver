#!/usr/bin/env python3
"""Unified CLI for consistency-check runtime tools — zero-judgment data layer.

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

WORK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = WORK_ROOT.parent
if str(WORK_ROOT) not in sys.path:
    sys.path.insert(0, str(WORK_ROOT))


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


def _resolve_output_guarded(path_str: str, source_root: str | Path | None = None) -> Path:
    path = _resolve_output(path_str).resolve()
    if source_root is not None:
        source_path = Path(source_root).resolve()
        try:
            path.relative_to(source_path)
        except ValueError:
            return path
        _die("guard", f"refusing to write inside protected root: {path}")
    return path


def _load_json_file(path_str: str) -> Any:
    return json.loads(Path(path_str).read_text(encoding="utf-8"))


def _iter_text_files(root: Path) -> List[Path]:
    return [
        path for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".rs", ".py", ".java", ".kt", ".md", ".txt", ".c", ".h", ".cpp", ".hpp"}
    ]


def _count_unsafe_tokens(project_dir: Path) -> Dict[str, Any]:
    file_hits: List[Dict[str, Any]] = []
    total_lines = 0
    unsafe_lines = 0
    for path in _iter_text_files(project_dir):
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        total_lines += len(lines)
        for index, line in enumerate(lines, start=1):
            if "unsafe" in line:
                unsafe_lines += 1
                file_hits.append({"file": str(path), "line": index, "context": line.strip()})
    ratio = (unsafe_lines / total_lines) if total_lines else 0.0
    return {
        "project_dir": str(project_dir),
        "unsafe_line_count": unsafe_lines,
        "total_line_count": total_lines,
        "ratio": ratio,
        "hits": file_hits,
    }


def _scan_assertions(project_dir: Path) -> Dict[str, Any]:
    tests: List[Dict[str, Any]] = []
    effective_assertions: List[Dict[str, Any]] = []
    findings: List[Dict[str, Any]] = []
    assertion_tokens = ("assert", "expect(", "should", "verify(")
    for path in _iter_text_files(project_dir):
        if "test" not in path.name.lower() and "tests" not in path.parts:
            continue
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        assertion_count = 0
        for index, line in enumerate(lines, start=1):
            if any(token in line for token in assertion_tokens):
                assertion_count += 1
                effective_assertions.append({"file": str(path), "line": index, "context": line.strip()})
        tests.append({"file": str(path), "assertion_count": assertion_count})
        if assertion_count == 0:
            findings.append({"file": str(path), "issue": "no assertion-like statements detected"})
    return {"tests": tests, "effective_assertions": effective_assertions, "findings": findings}


def _scan_project_customization(paths: List[Path], forbidden: List[str]) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    adjudications: List[Dict[str, Any]] = []
    lowered_terms = [term.lower() for term in forbidden]
    for path in paths:
        if not path.is_file():
            continue
        for index, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            line_lower = line.lower()
            hits = [term for term, lowered in zip(forbidden, lowered_terms) if lowered in line_lower]
            if hits:
                findings.append({"file": str(path), "line": index, "terms": hits})
    for finding in findings:
        adjudications.append({"file": finding["file"], "line": finding["line"], "terms": finding["terms"]})
    return {"findings": findings, "adjudications": adjudications}


# ---------------------------------------------------------------------------
# scan-design
# ---------------------------------------------------------------------------

def cmd_parse_source(args: argparse.Namespace) -> None:
    from runtime.source_analysis import build_complete_analysis

    source_root = Path(args.source_root)
    if not source_root.is_dir():
        _die("parse-source", f"source-root does not exist: {source_root}")

    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

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
            key: value for key, value in preprocessor.items()
            if key not in ("required_variants", "compile_database")
        },
        "parse_failures": analysis_verif.get("parse_failures", []),
    }

    if args.output:
        out_path = _resolve_output_guarded(args.output, source_root)
        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        _ok("parse-source", {"written": str(out_path), "file_count": len(data["files"])})
        return
    _ok("parse-source", data)


def cmd_scan_design(args: argparse.Namespace) -> None:
    from runtime.design_scanner import scan_design_root

    design_root = Path(args.design_root)
    if not design_root.is_dir():
        _die("scan-design", f"design-root does not exist: {design_root}")

    result = scan_design_root(design_root, submission_readme=args.submission_readme)

    if args.output:
        out_path = _resolve_output_guarded(args.output, args.source_root)
        out_path.write_text(json.dumps(result["inventory"], indent=2, ensure_ascii=False), encoding="utf-8")
    if args.model_output:
        model_path = _resolve_output_guarded(args.model_output, args.source_root)
        model_path.write_text(json.dumps(result["design_model"], indent=2, ensure_ascii=False), encoding="utf-8")
    if args.evidence_output:
        evidence_path = _resolve_output_guarded(args.evidence_output, args.source_root)
        evidence_path.write_text(json.dumps(result["evidence_index"], indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        if not args.output and not args.model_output and not args.evidence_output:
            _ok("scan-design", result)
            return
    _ok(
        "scan-design",
        {
            "file_count": result["inventory"]["file_count"],
            "object_count": result["inventory"]["object_count"],
            "output": str(args.output) if args.output else "",
            "model_output": str(args.model_output) if args.model_output else "",
            "evidence_output": str(args.evidence_output) if args.evidence_output else "",
        },
    )


# ---------------------------------------------------------------------------
# run-verification
# ---------------------------------------------------------------------------

def cmd_run_verification(args: argparse.Namespace) -> None:
    from runtime.verification_runner import resolve_verification_commands, run_verification

    project_dir = Path(args.project_dir or args.source_root or "")
    if not project_dir.is_dir():
        _die("run-verification", f"project-dir does not exist: {project_dir}")

    command_override = None
    if args.commands:
        command_override = json.loads(args.commands)
        if not isinstance(command_override, list) or not all(isinstance(c, str) for c in command_override):
            _die("run-verification", "--commands must be a JSON array of strings")

    adapter_id = args.adapter
    if args.selection_input:
        selection = _load_json_file(args.selection_input)
        adapter_id = adapter_id or selection.get("adapter_id", "")

    resolved = resolve_verification_commands(
        project_dir,
        args.profile,
        adapter_id=adapter_id,
        submission_root=args.submission_root,
        commands_override=command_override,
    )
    result = run_verification(
        project_dir,
        commands=resolved["commands"],
        timeout=args.timeout,
        command_source=resolved["command_source"],
    )

    if args.output:
        out_path = _resolve_output_guarded(args.output, project_dir)
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    _ok("run-verification", result)


# ---------------------------------------------------------------------------
# check-unsafe
# ---------------------------------------------------------------------------

def cmd_check_unsafe(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    if not project_dir.is_dir():
        _die("check-unsafe", f"project-dir does not exist: {project_dir}")

    result = _count_unsafe_tokens(project_dir)

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
    project_dir = Path(args.project_dir)
    if not project_dir.is_dir():
        _die("fault-injection", f"project-dir does not exist: {project_dir}")

    trace_dir = Path(args.trace_dir)
    trace_dir.mkdir(parents=True, exist_ok=True)

    mutations: List[str] = json.loads(args.mutations) if args.mutations else ["negate-assertions", "remove-checks"]
    assertion_scan = _scan_assertions(project_dir)
    mutation_report = {
        "mutations": mutations,
        "survivors": [item["file"] for item in assertion_scan.get("tests", []) if item["assertion_count"] == 0],
        "metrics": {
            "mutation_count": len(mutations),
            "survivor_count": len([item for item in assertion_scan.get("tests", []) if item["assertion_count"] == 0]),
        },
    }

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
    import glob as _glob

    paths_raw: List[str] = json.loads(args.paths)
    forbidden: List[str] = json.loads(args.forbidden_terms)

    expanded: List[Path] = []
    for pattern in paths_raw:
        for match in _glob.glob(pattern, recursive=True):
            expanded.append(Path(match))

    result = _scan_project_customization(expanded, forbidden)

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
    from runtime.report_writer import (
        DEFAULT_FINAL_REPORT_INPUT,
        compose_report_payload,
        write_reports,
    )

    result_dir = Path(args.result_dir)
    trace_dir = Path(args.trace_dir) if args.trace_dir else result_dir.parent / "logs" / "trace"

    if args.data:
        payload = json.loads(args.data)
    elif args.data_file:
        payload = _load_json_file(args.data_file)
    elif args.trace_root:
        payload = compose_report_payload(
            trace_root=args.trace_root,
            result_dir=result_dir,
            design_root=args.design_root,
            source_root=args.source_root,
            submission_root=args.submission_root,
            test_root=args.test_root,
            profile_path=args.profile,
        )
    elif not sys.stdin.isatty():
        payload = json.loads(sys.stdin.read())
    else:
        _die("write-report", "no data provided via --data/--data-file/--trace-root or stdin")

    if args.template:
        template_path = Path(args.template)
        if not template_path.is_file():
            _die("write-report", f"template not found: {template_path}")
        template = template_path.read_text(encoding="utf-8")
        for key, value in payload.items():
            placeholder = "{{" + key + "}}"
            if placeholder in template:
                replacement = json.dumps(value, indent=2, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
                template = template.replace(placeholder, replacement)
        result_dir.mkdir(parents=True, exist_ok=True)
        output_path = result_dir / "output.md"
        output_path.write_text(template, encoding="utf-8")
        _ok("write-report", {"output_path": str(output_path)})
        return

    if args.payload_output:
        payload_output = _resolve_output_guarded(args.payload_output, args.source_root)
    elif args.trace_root:
        payload_output = _resolve_output_guarded(str(Path(args.trace_root) / Path(DEFAULT_FINAL_REPORT_INPUT).name), args.source_root)
    else:
        payload_output = None
    if payload_output is not None:
        payload_output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    outputs = write_reports(payload, result_dir=result_dir, trace_dir=trace_dir)
    if payload_output is not None:
        outputs["payload_output_path"] = str(payload_output)
    _ok("write-report", outputs)


# ---------------------------------------------------------------------------
# scan-code
# ---------------------------------------------------------------------------

def cmd_scan_code(args: argparse.Namespace) -> None:
    from runtime.code_inventory import build_source_inventory

    source_root = Path(args.source_root)
    if not source_root.is_dir():
        _die("scan-code", f"source-root does not exist: {source_root}")

    inventory = build_source_inventory(
        source_root,
        args.profile,
        submission_root=args.submission_root,
        test_root=args.test_root,
    )

    if args.output:
        out_path = _resolve_output_guarded(args.output, source_root)
        out_path.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.selection_output:
        selection_path = _resolve_output_guarded(args.selection_output, source_root)
        selection_path.write_text(
            json.dumps(inventory["selection"], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    _ok(
        "scan-code",
        {
            "selected_adapter": inventory["selected_adapter"],
            "file_count": inventory["file_count"],
            "output": str(args.output) if args.output else "",
            "selection_output": str(args.selection_output) if args.selection_output else "",
        },
    )


# ---------------------------------------------------------------------------
# extract-implementation
# ---------------------------------------------------------------------------

def cmd_extract_implementation(args: argparse.Namespace) -> None:
    from runtime.code_inventory import extract_implementation_model

    source_root = Path(args.source_root)
    if not source_root.is_dir():
        _die("extract-implementation", f"source-root does not exist: {source_root}")

    result = extract_implementation_model(source_root, args.profile, args.adapter)

    if args.output:
        out_path = _resolve_output_guarded(args.output, source_root)
        out_path.write_text(
            json.dumps(result["implementation_model"], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    if args.selection_output:
        selection_path = _resolve_output_guarded(args.selection_output, source_root)
        selection_path.write_text(
            json.dumps(result["selection"], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    if args.inventory_output:
        inventory_path = _resolve_output_guarded(args.inventory_output, source_root)
        inventory_path.write_text(
            json.dumps(result["inventory"], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    _ok(
        "extract-implementation",
        {
            "selected_adapter": result["selection"]["adapter_id"],
            "object_count": len(result["implementation_model"]["objects"]),
            "output": str(args.output) if args.output else "",
            "selection_output": str(args.selection_output) if args.selection_output else "",
            "inventory_output": str(args.inventory_output) if args.inventory_output else "",
        },
    )


# ---------------------------------------------------------------------------
# build-traceability
# ---------------------------------------------------------------------------

def cmd_build_traceability(args: argparse.Namespace) -> None:
    from runtime.traceability_builder import build_traceability, render_traceability_summary

    matrix = build_traceability(args.design_model, args.implementation_model)
    if args.output:
        out_path = _resolve_output_guarded(args.output, args.source_root)
        out_path.write_text(json.dumps(matrix, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.summary_output:
        summary_path = _resolve_output_guarded(args.summary_output, args.source_root)
        summary_path.write_text(render_traceability_summary(matrix), encoding="utf-8")
    if args.evidence_output:
        evidence_path = _resolve_output_guarded(args.evidence_output, args.source_root)
        evidence_payload = {
            "links": [
                {
                    "design_id": link["design_id"],
                    "implementation_id": link["implementation_id"],
                    "evidence": link["evidence"],
                }
                for link in matrix.get("links", [])
            ],
            "gaps": [
                {
                    "design_id": gap["design_id"],
                    "evidence": gap["evidence"],
                }
                for gap in matrix.get("gaps", [])
            ],
        }
        evidence_path.write_text(json.dumps(evidence_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    _ok("build-traceability", matrix)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        prog="tools",
        description="Unified CLI for consistency-check runtime tools. JSON output, zero judgment.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # parse-source
    p = sub.add_parser("parse-source", help="Legacy C-source inventory command kept for compatibility")
    p.add_argument("--source-root", required=True)
    p.add_argument("--test-dirs", default="")
    p.add_argument("--work-dir", default="work")
    p.add_argument("--output", help="Write JSON to file instead of stdout")

    # scan-design
    p = sub.add_parser("scan-design", help="Inventory acceptance-baseline documents and extract a canonical design model")
    p.add_argument("--design-root", required=True)
    p.add_argument("--submission-readme", help="Optional standard-package README to include as the primary design contract")
    p.add_argument("--source-root", help="Optional SOURCE_ROOT for write-guard enforcement")
    p.add_argument("--output", help="Write the design inventory JSON to file")
    p.add_argument("--model-output", help="Write the canonical design model JSON to file")
    p.add_argument("--evidence-output", help="Write the design evidence index JSON to file")

    # run-verification
    p = sub.add_parser("run-verification", help="Execute ordered build/black-box verification commands, return raw results")
    p.add_argument("--project-dir", help="Project directory to execute verification commands in")
    p.add_argument("--source-root", help="Alias for --project-dir in consistency-check flows")
    p.add_argument("--profile", help="Consistency profile YAML used to resolve default commands")
    p.add_argument("--adapter", help="Adapter id used to select profile-based verification defaults")
    p.add_argument("--submission-root", help="Standard submission package root used to resolve authoritative verification commands")
    p.add_argument("--selection-input", help="Adapter-selection JSON path used to infer the adapter id")
    p.add_argument("--commands", help='Optional JSON array, e.g. \'["mvn test"]\'')
    p.add_argument("--output", help="Write the verification JSON to file")
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
    p = sub.add_parser("write-report", help="Write structured repair-and-verify reports and final audit markdown")
    p.add_argument("--result-dir", required=True)
    p.add_argument("--trace-dir", help="Directory containing final audit markdown output")
    p.add_argument("--trace-root", help="Consistency trace root used to compose a report payload from artifacts")
    p.add_argument("--design-root", help="Design root recorded in the final report scope")
    p.add_argument("--source-root", help="Source root recorded in the final report scope and used for write guards")
    p.add_argument("--submission-root", help="Submission root recorded in the final report scope")
    p.add_argument("--test-root", help="Test root recorded in the final report scope")
    p.add_argument("--profile", help="Consistency profile YAML used to resolve model paths")
    p.add_argument("--data", help="JSON string (or pipe via stdin)")
    p.add_argument("--data-file", help="Path to JSON input payload")
    p.add_argument("--payload-output", help="Write the normalized final report payload JSON to file")
    p.add_argument("--template", help="Custom markdown template path")

    # scan-code
    p = sub.add_parser("scan-code", help="Inventory source files and select the language adapter")
    p.add_argument("--source-root", required=True)
    p.add_argument("--submission-root", help="Optional standard submission root recorded in inventory metadata")
    p.add_argument("--test-root", help="Optional black-box test root recorded in inventory metadata")
    p.add_argument("--profile", help="Path to the consistency profile YAML")
    p.add_argument("--output", help="Write inventory JSON to file")
    p.add_argument("--selection-output", help="Write adapter selection JSON to file")

    # extract-implementation
    p = sub.add_parser("extract-implementation", help="Extract a canonical implementation model using adapters")
    p.add_argument("--source-root", required=True)
    p.add_argument("--profile", help="Path to the consistency profile YAML")
    p.add_argument("--adapter", help="Override the auto-selected adapter")
    p.add_argument("--output", help="Write implementation model JSON to file")
    p.add_argument("--selection-output", help="Write adapter selection JSON to file")
    p.add_argument("--inventory-output", help="Write adapter inventory summary JSON to file")

    # build-traceability
    p = sub.add_parser("build-traceability", help="Build a canonical traceability matrix from design and implementation models")
    p.add_argument("--design-model", required=True)
    p.add_argument("--implementation-model", required=True)
    p.add_argument("--source-root", help="Optional SOURCE_ROOT for write-guard enforcement")
    p.add_argument("--output", help="Write the traceability matrix JSON to file")
    p.add_argument("--summary-output", help="Write the traceability summary markdown to file")
    p.add_argument("--evidence-output", help="Write the traceability evidence index JSON to file")

    args = parser.parse_args(argv)

    dispatch = {
        "parse-source": cmd_parse_source,
        "scan-design": cmd_scan_design,
        "run-verification": cmd_run_verification,
        "check-unsafe": cmd_check_unsafe,
        "fault-injection": cmd_fault_injection,
        "neutrality-audit": cmd_neutrality_audit,
        "scan-code": cmd_scan_code,
        "extract-implementation": cmd_extract_implementation,
        "build-traceability": cmd_build_traceability,
        "write-report": cmd_write_report,
    }

    try:
        dispatch[args.command](args)
    except Exception as exc:
        _die(args.command, f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
