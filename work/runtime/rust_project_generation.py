from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, Sequence

from semantic_planning import OUTPUT_FILES as PLANNING_FILES
from semantic_planning import PlanningBlocked, load_analysis_evidence, validate_planning_documents


SCHEMA_VERSION = "c-to-rust-project-generation/v1"
RUST_EDITION = "2021"
MINIMUM_RUST_VERSION = "1.70"
UNSAFE_RATIO_LIMIT = 0.10
EVIDENCE_FILES = (
    "implementation-map.json",
    "unsupported-functions.json",
    "module-edge-map.json",
    "unsafe-audit.json",
    "generation-verification.json",
)
PLACEHOLDER_PATTERNS = {
    "todo_macro": re.compile(r"\btodo!\s*\("),
    "unimplemented_macro": re.compile(r"\bunimplemented!\s*\("),
    "placeholder_panic": re.compile(r"\bpanic!\s*\(\s*\"(?:TODO|todo|unimplemented|placeholder)"),
    "constant_success": re.compile(r"(?s)pub\s+(?:unsafe\s+)?fn\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*(?:->\s*[^\{]+)?\{\s*(?:let\s+_\s*=\s*[^;]+;\s*)?(?:0|true|Ok\s*\(\s*\(\s*\)\s*\))\s*\}"),
    "empty_function": re.compile(r"(?s)pub\s+(?:unsafe\s+)?fn\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*(?:->\s*\(\s*\))?\s*\{\s*\}"),
}


def summarize_final_repair(diagnostics: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    final_repair = [dict(item) for item in diagnostics if item.get("stage") == "final_repair_pass"]
    resolved = [item for item in final_repair if item.get("resolved")]
    unresolved = [item for item in final_repair if not item.get("resolved")]
    return {
        "attempted_count": len(final_repair),
        "resolved_count": len(resolved),
        "unresolved_count": len(unresolved),
        "attempted_symbols": [item.get("symbol", "unknown") for item in final_repair],
        "resolved_symbols": [item.get("symbol", "unknown") for item in resolved],
        "unresolved_symbols": [item.get("symbol", "unknown") for item in unresolved],
    }


class GenerationBlocked(RuntimeError):
    def __init__(self, failures: Sequence[str], report: Mapping[str, Any] | None = None):
        self.failures = list(dict.fromkeys(failures))
        self.report = dict(report or {})
        super().__init__("; ".join(self.failures))


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _stable_id(kind: str, *parts: str) -> str:
    return f"{kind}-{hashlib.sha256('|'.join(parts).encode()).hexdigest()[:16]}"


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_tree(root: Path, *, include_target: bool = False) -> Dict[str, str]:
    ignored = {"target", ".git"} if not include_target else {".git"}
    if not root.is_dir():
        return {}
    result: Dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root)
        if any(part in ignored for part in relative.parts):
            continue
        result[relative.as_posix()] = _file_digest(path)
    return result


def project_digest(root: Path) -> str:
    return _digest(snapshot_tree(root))


def _metadata(doc: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        doc.get("schema_version"), doc.get("run_id"),
        doc.get("parent_analysis_run_id"), doc.get("source_digest"),
        doc.get("semantic_ir_digest"),
    )


def load_generation_inputs(trace_dir: Path) -> Dict[str, Any]:
    trace_dir = trace_dir.resolve()
    failures: list[str] = []
    try:
        analysis = load_analysis_evidence(trace_dir)
    except PlanningBlocked as exc:
        raise GenerationBlocked([f"analysis:{item}" for item in exc.failures]) from exc
    planning_failures = validate_planning_documents(trace_dir)
    failures.extend(f"planning:{item}" for item in planning_failures)
    planning: Dict[str, Dict[str, Any]] = {}
    for name in PLANNING_FILES:
        path = trace_dir / name
        if not path.is_file():
            failures.append(f"missing_planning_evidence:{name}")
            continue
        try:
            planning[name] = _read_json(path)
        except (OSError, json.JSONDecodeError):
            failures.append(f"invalid_planning_evidence:{name}")
    if planning:
        identities = {_metadata(doc) for doc in planning.values()}
        if len(identities) != 1:
            failures.append("mixed_planning_identity")
        verification = planning.get("semantic-planning-verification.json", {})
        if not verification.get("passed") or verification.get("status") != "PASSED":
            failures.append("semantic_planning_not_passed")
        public = analysis["public-api-map.json"]
        for doc in planning.values():
            if doc.get("parent_analysis_run_id") != public.get("run_id"):
                failures.append("stale_parent_analysis_run")
            if doc.get("source_digest") != public.get("source_digest"):
                failures.append("source_digest_mismatch")
    if failures:
        raise GenerationBlocked(failures)
    identity = next(iter({_metadata(doc) for doc in planning.values()}))
    return {
        "analysis": analysis,
        "planning": planning,
        "analysis_run_id": analysis["public-api-map.json"]["run_id"],
        "planning_run_id": identity[1],
        "source_digest": identity[3],
        "semantic_ir_digest": identity[4],
        "input_digest": _digest({"analysis": analysis, "planning": planning}),
    }


def _rust_files(project_dir: Path) -> list[Path]:
    return sorted(path for path in (project_dir / "src").rglob("*.rs") if path.is_file()) if (project_dir / "src").is_dir() else []


def _line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _function_symbols(project_dir: Path) -> Dict[str, list[Dict[str, Any]]]:
    symbols: Dict[str, list[Dict[str, Any]]] = {}
    pattern = re.compile(r"\b(?:pub(?:\([^)]*\))?\s+)?(?:unsafe\s+)?fn\s+([A-Za-z_]\w*)\s*(?:<[^\n{;]+?>)?\s*\(")
    for path in _rust_files(project_dir):
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            symbols.setdefault(match.group(1), []).append({
                "file": path.relative_to(project_dir).as_posix(),
                "line": _line_for_offset(text, match.start()),
                "symbol": match.group(1),
            })
    return symbols


def scan_placeholders(
    project_dir: Path,
    state_changing_apis: Iterable[str] = (),
    adjudications: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[Dict[str, Any]]:
    findings: list[Dict[str, Any]] = []
    mutable = set(state_changing_apis)
    adjudications = dict(adjudications or {})
    for path in _rust_files(project_dir):
        text = path.read_text(encoding="utf-8")
        for kind, pattern in PLACEHOLDER_PATTERNS.items():
            for match in pattern.finditer(text):
                symbol = match.group(1) if match.lastindex else ""
                if kind == "constant_success" and symbol not in mutable:
                    continue
                relative = path.relative_to(project_dir).as_posix()
                line = _line_for_offset(text, match.start())
                finding_id = _stable_id("placeholder", kind, symbol, relative, str(line))
                decision = dict(adjudications.get(finding_id, {}))
                resolved = (
                    kind in {"constant_success", "empty_function"}
                    and decision.get("verdict") == "source_semantics_preserved"
                    and bool(decision.get("contract_id"))
                    and bool(decision.get("source_evidence"))
                    and bool(decision.get("reason"))
                )
                findings.append({
                    "id": finding_id, "kind": kind, "symbol": symbol,
                    "file": relative, "line": line,
                    "adjudication": "resolved" if resolved else "unresolved",
                    "decision": decision,
                })
    return findings


def audit_unsafe(project_dir: Path, justifications: Mapping[str, Mapping[str, str]] | None = None) -> Dict[str, Any]:
    justifications = dict(justifications or {})
    occurrences: list[Dict[str, Any]] = []
    node_count = 0
    node_pattern = re.compile(r"\b(?:fn|struct|enum|impl|trait|const|static|type|mod)\b")
    unsafe_pattern = re.compile(r"\bunsafe\s*(?:\{|fn\b|impl\b|trait\b)")
    for path in _rust_files(project_dir):
        text = path.read_text(encoding="utf-8")
        node_count += len(node_pattern.findall(text))
        relative = path.relative_to(project_dir).as_posix()
        for match in unsafe_pattern.finditer(text):
            key = f"{relative}:{_line_for_offset(text, match.start())}"
            detail = dict(justifications.get(key, {}))
            occurrences.append({"id": key, "file": relative, "line": _line_for_offset(text, match.start()), **detail})
    unsafe_count = len(occurrences)
    ratio = unsafe_count / node_count if node_count else 1.0
    justified = all(all(item.get(field) for field in ("necessity", "safety_invariant", "boundary")) for item in occurrences)
    return {
        "metric": "unsafe_syntax_nodes / rust_item_nodes",
        "unsafe_count": unsafe_count,
        "item_count": node_count,
        "ratio": ratio,
        "limit": UNSAFE_RATIO_LIMIT,
        "occurrences": occurrences,
        "passed": node_count > 0 and ratio < UNSAFE_RATIO_LIMIT and justified,
    }


def run_locked_build(project_dir: Path, timeout_seconds: int = 300) -> Dict[str, Any]:
    command = ["cargo", "build", "--locked"]
    try:
        toolchain = subprocess.run(["rustc", "--version"], capture_output=True, text=True, timeout=30)
        completed = subprocess.run(command, cwd=project_dir, capture_output=True, text=True, timeout=timeout_seconds)
        return {
            "command": "cargo build --locked", "working_directory": str(project_dir),
            "toolchain": toolchain.stdout.strip() or toolchain.stderr.strip(), "returncode": completed.returncode,
            "stdout": completed.stdout, "stderr": completed.stderr, "passed": completed.returncode == 0,
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"command": "cargo build --locked", "working_directory": str(project_dir), "toolchain": "unavailable", "returncode": -1, "stdout": "", "stderr": str(exc), "passed": False}


def validate_candidate(project_dir: Path, inputs: Mapping[str, Any], *, build: bool = True, unsafe_justifications: Mapping[str, Mapping[str, str]] | None = None, placeholder_adjudications: Mapping[str, Mapping[str, Any]] | None = None, generation_diagnostics: Iterable[Mapping[str, Any]] | None = None) -> Dict[str, Any]:
    planning = inputs["planning"]
    analysis = inputs["analysis"]
    contracts = planning["behavior-contracts.json"].get("contracts", [])
    plan = planning["rust-migration-plan.json"]
    api_records = analysis["public-api-map.json"].get("apis", [])
    expected_apis = sorted({item.get("name") or item.get("api") for item in api_records if item.get("name") or item.get("api")})
    source_edges = analysis["call-graph.json"].get("call_edges", [])
    # The complete-analysis contract exports every public definition plus all
    # callers in the call graph. Callees may be platform callbacks and are
    # therefore covered by the planned port mapping rather than a Rust fn.
    expected_functions = sorted(set(expected_apis) | {item.get("caller") for item in source_edges if item.get("caller")})
    symbols = _function_symbols(project_dir)
    contract_by_api = {item.get("api"): item for item in contracts}
    effects = {item.get("id"): item for item in planning["behavior-contracts.json"].get("effects", [])}
    mutable = {
        item.get("api") for item in contracts
        if any(effects.get(effect_id, {}).get("operation") not in {None, "none", "read"} for effect_id in item.get("effect_ids", []))
        or item.get("state_mutations")
    }
    implementation = []
    unsupported = []
    for name in sorted(set(expected_functions) | set(expected_apis)):
        matches = symbols.get(name, [])
        if len(matches) != 1:
            unsupported.append({"source_symbol": name, "reason": "missing Rust symbol" if not matches else "duplicate Rust symbols", "matches": matches})
            continue
        contract = contract_by_api.get(name, {})
        implementation.append({
            "implementation_id": f"impl-{hashlib.sha256(name.encode()).hexdigest()[:16]}", "source_symbol": name,
            "api_id": contract.get("api_id", ""), "contract_id": contract.get("id", ""),
            "rust": matches[0], "state_effects": contract.get("state_mutations", []), "source_evidence": contract.get("source_evidence", []),
        })
    planned_edges = {item.get("source_edge_id"): item for item in plan.get("call_edge_mappings", [])}
    edge_map = []
    missing_edges = []
    for edge in source_edges:
        edge_id = edge.get("id") or _stable_id("edge", edge.get("caller", ""), edge.get("callee", ""))
        mapping = planned_edges.get(edge_id)
        record = {"source_edge_id": edge_id, "caller": edge.get("caller", ""), "callee": edge.get("callee", ""), "mapping": mapping or {}, "covered": bool(mapping)}
        edge_map.append(record)
        if not mapping:
            missing_edges.append(edge_id)
    placeholders = scan_placeholders(project_dir, mutable, placeholder_adjudications)
    unresolved_placeholders = [item for item in placeholders if item["adjudication"] != "resolved"]
    generation_diagnostics_list = [dict(item) for item in (generation_diagnostics or [])]
    unresolved_generation_diagnostics = [item for item in generation_diagnostics_list if not item.get("resolved")]
    final_repair_summary = summarize_final_repair(generation_diagnostics_list)
    unsafe = audit_unsafe(project_dir, unsafe_justifications)
    cargo = run_locked_build(project_dir) if build else {"passed": True, "skipped": True}
    checks = {
        "cargo_manifest_and_lock_exist": (project_dir / "Cargo.toml").is_file() and (project_dir / "Cargo.lock").is_file(),
        "public_api_denominator_nonzero": bool(expected_apis),
        "core_function_denominator_nonzero": bool(expected_functions),
        "public_api_coverage_100_percent": all(name in symbols and len(symbols[name]) == 1 for name in expected_apis),
        "core_function_coverage_100_percent": all(name in symbols and len(symbols[name]) == 1 for name in expected_functions),
        "unsupported_functions_empty": not unsupported,
        "generation_diagnostics_clear": not unresolved_generation_diagnostics,
        "module_edges_complete": not missing_edges,
        "placeholder_scan_clear": not unresolved_placeholders,
        "unsafe_gate_passed": unsafe["passed"],
        "cargo_build_locked_passed": cargo["passed"],
    }
    failures = [name for name, passed in checks.items() if not passed]
    return {
        "schema_version": SCHEMA_VERSION, "status": "PASSED" if not failures else "BLOCKED_WITH_REPORT", "passed": not failures,
        "checks": checks, "failures": failures, "first_blocking_point": failures[0] if failures else None,
        "metrics": {"public_api_count": len(expected_apis), "core_function_count": len(expected_functions), "implementation_count": len(implementation), "call_edge_count": len(source_edges)},
        "implementation_map": implementation, "unsupported_functions": unsupported, "module_edge_map": edge_map,
        "generation_diagnostics": generation_diagnostics_list,
        "unresolved_generation_diagnostics": unresolved_generation_diagnostics,
        "final_repair_summary": final_repair_summary,
        "placeholder_findings": placeholders, "unsafe_audit": unsafe, "cargo_build": cargo,
    }


def _decorate(document: Mapping[str, Any], metadata: Mapping[str, Any]) -> Dict[str, Any]:
    return {**metadata, **document}


def build_evidence(project_dir: Path, inputs: Mapping[str, Any], *, run_id: str | None = None, build: bool = True, unsafe_justifications: Mapping[str, Mapping[str, str]] | None = None, placeholder_adjudications: Mapping[str, Mapping[str, Any]] | None = None, generation_diagnostics: Iterable[Mapping[str, Any]] | None = None) -> Dict[str, Any]:
    verification = validate_candidate(project_dir, inputs, build=build, unsafe_justifications=unsafe_justifications, placeholder_adjudications=placeholder_adjudications, generation_diagnostics=generation_diagnostics)
    metadata = {
        "schema_version": SCHEMA_VERSION, "run_id": run_id or uuid.uuid4().hex,
        "analysis_run_id": inputs["analysis_run_id"], "planning_run_id": inputs["planning_run_id"],
        "source_digest": inputs["source_digest"], "input_digest": inputs["input_digest"],
        "project_digest": project_digest(project_dir), "rust_edition": RUST_EDITION,
        "minimum_rust_version": MINIMUM_RUST_VERSION, "lock_policy": "cargo build --locked",
    }
    artifacts = {
        "implementation-map.json": _decorate({"implementations": verification.pop("implementation_map")}, metadata),
        "unsupported-functions.json": _decorate({
            "unsupported_functions": verification.pop("unsupported_functions"),
            "generation_diagnostics": verification.get("generation_diagnostics", []),
            "unresolved_generation_diagnostics": verification.get("unresolved_generation_diagnostics", []),
            "final_repair_summary": verification.get("final_repair_summary", {}),
        }, metadata),
        "module-edge-map.json": _decorate({"edges": verification.pop("module_edge_map")}, metadata),
        "unsafe-audit.json": _decorate(verification.pop("unsafe_audit"), metadata),
        "generation-verification.json": _decorate(verification, metadata),
    }
    return {"metadata": metadata, "artifacts": artifacts, "verification": artifacts["generation-verification.json"]}


def write_evidence(bundle: Mapping[str, Any], trace_dir: Path) -> None:
    artifacts = bundle["artifacts"]
    missing = [name for name in EVIDENCE_FILES if name not in artifacts]
    if missing:
        raise KeyError(f"missing generation artifacts: {missing}")
    trace_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=trace_dir.parent) as temp:
        stage = Path(temp)
        for name in EVIDENCE_FILES:
            (stage / name).write_text(json.dumps(artifacts[name], indent=2, sort_keys=True) + "\n", encoding="utf-8")
        for name in EVIDENCE_FILES:
            os.replace(stage / name, trace_dir / name)
    cargo = artifacts["generation-verification.json"].get("cargo_build", {})
    (trace_dir / "cargo-build.log").write_text((cargo.get("stdout", "") + cargo.get("stderr", "")), encoding="utf-8")


def verify_and_publish(project_dir: Path, trace_dir: Path, inputs: Mapping[str, Any], **kwargs: Any) -> Dict[str, Any]:
    bundle = build_evidence(project_dir, inputs, **kwargs)
    write_evidence(bundle, trace_dir)
    if not bundle["verification"]["passed"]:
        raise GenerationBlocked(bundle["verification"]["failures"], bundle["verification"])
    return bundle["verification"]


def _copy_project(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("target", ".git"))


def compute_incremental_dependencies(inputs: Mapping[str, Any]) -> Dict[str, list[Dict[str, str]]]:
    """Derive direct module dependencies exclusively from verified planning IR."""
    def module_name(value: Any) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9_]", "_", str(value)).strip("_").lower()
        if not cleaned:
            return "module"
        return f"module_{cleaned}" if cleaned[0].isdigit() else cleaned

    plan = inputs["planning"]["rust-migration-plan.json"]
    apis = inputs["analysis"]["public-api-map.json"].get("apis", [])
    api_name_by_id = {item.get("id"): item.get("name") for item in apis}
    module_by_symbol: Dict[str, str] = {}
    obligations = plan.get("implementation_obligations", [])
    result: Dict[str, list[Dict[str, str]]] = {}
    for obligation in obligations:
        module = module_name(obligation.get("target_module")) if obligation.get("target_module") else ""
        symbol = api_name_by_id.get(obligation.get("api_id"))
        if module and symbol:
            module_by_symbol[str(symbol)] = module
        if module and obligation.get("boundary_dependencies"):
            result.setdefault(module, []).append({
                "module": "ports",
                "evidence": ",".join(sorted(map(str, obligation["boundary_dependencies"]))),
            })
    for edge in plan.get("call_edge_mappings", []):
        caller_module = module_by_symbol.get(str(edge.get("caller", "")))
        callee_module = module_by_symbol.get(str(edge.get("callee", "")))
        if caller_module and callee_module and caller_module != callee_module:
            result.setdefault(caller_module, []).append({
                "module": callee_module,
                "evidence": str(edge.get("source_edge_id") or ""),
            })
    return {
        module: sorted(
            {item["module"]: item for item in records}.values(),
            key=lambda item: item["module"],
        )
        for module, records in sorted(result.items())
    }


def incremental_regenerate(
    project_dir: Path,
    trace_dir: Path,
    inputs: Mapping[str, Any],
    target_module: str,
    regenerate: Callable[[Path, Sequence[str]], None],
    *,
    build: bool = True,
) -> Dict[str, Any]:
    project_dir = project_dir.resolve()
    before = snapshot_tree(project_dir)
    parent_digest = _digest(before)
    modules = {path.stem: path.relative_to(project_dir).as_posix() for path in _rust_files(project_dir)}
    if target_module not in modules:
        raise GenerationBlocked([f"unknown_incremental_target:{target_module}"])
    dependency_graph = compute_incremental_dependencies(inputs)
    dependency_records = dependency_graph.get(target_module, [])
    dependencies = [item["module"] for item in dependency_records]
    unknown = [name for name in dependencies if name not in modules]
    if unknown:
        raise GenerationBlocked([f"unknown_incremental_dependency:{name}" for name in unknown])
    closure = sorted(set([target_module, *dependencies]))
    allowed = {modules[name] for name in closure}
    with tempfile.TemporaryDirectory(dir=project_dir.parent) as temp:
        candidate = Path(temp) / project_dir.name
        _copy_project(project_dir, candidate)
        regenerate(candidate, closure)
        after = snapshot_tree(candidate)
        changed = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
        out_of_bounds = sorted(set(changed) - allowed)
        if out_of_bounds:
            raise GenerationBlocked([f"incremental_boundary_violation:{path}" for path in out_of_bounds])
        bundle = build_evidence(candidate, inputs, build=build)
        if not bundle["verification"]["passed"]:
            raise GenerationBlocked(bundle["verification"]["failures"], bundle["verification"])
        for relative in changed:
            destination = project_dir / relative
            if relative in after:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(candidate / relative, destination)
            elif destination.exists():
                destination.unlink()
        write_evidence(bundle, trace_dir)
    report = {
        "schema_version": SCHEMA_VERSION, "parent_generation_digest": parent_digest,
        "target_module": target_module, "direct_dependencies": dependencies, "allowed_closure": closure,
        "closure_edge_evidence": dependency_records,
        "allowed_files": sorted(allowed), "before": before, "after": snapshot_tree(project_dir),
        "changed_files": changed, "unchanged_files": sorted(set(before) & set(after) - set(changed)),
        "out_of_bounds": [], "passed": True,
    }
    (trace_dir / "incremental-regeneration-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
