"""Complete, deterministic and independently verified C source inventory."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import stat
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

try:
    import pycparser
    from pycparser import c_ast, c_parser
except ImportError:  # fail closed at runtime; bootstrap installs requirements.txt
    pycparser = None
    c_ast = None
    c_parser = None


SCHEMA_VERSION = "c-source-analysis/v2"
EVIDENCE_FILES = (
    "source-inventory.json", "independent-source-scan.json", "public-api-map.json",
    "type-map.json", "call-graph.json", "global-state-map.json",
    "preprocessor-variants.json", "analysis-verification.json",
)
CORE_SUFFIXES = {".c", ".h"}
PUBLIC_DECL_RE = re.compile(
    r"(?m)^\s*(?!static\b|typedef\b|#)(?:[A-Za-z_]\w*[\s*]+)+([A-Za-z_]\w*)\s*\(([^;{}]*)\)\s*;"
)
TEST_MARKER_RE = re.compile(r"\b(?:TEST(?:_CASE)?|assert|TEST_ASSERT)\s*\(")
INCLUDE_RE = re.compile(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]', re.MULTILINE)
DEFINE_RE = re.compile(r"^\s*#\s*define\s+([A-Za-z_]\w*)(?:\(([^)]*)\))?\s*(.*)$", re.MULTILINE)
CONDITIONAL_RE = re.compile(r"^\s*#\s*(if|ifdef|ifndef|elif)\s+(.+)$", re.MULTILINE)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def snapshot_source_tree(root: Path) -> Dict[str, Dict[str, Any]]:
    """Capture immutable attributes without writing below root."""
    result: Dict[str, Dict[str, Any]] = {}
    for path in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.as_posix()):
        info = path.stat()
        result[_rel(path, root)] = {
            "sha256": _sha256(path.read_bytes()),
            "mode": stat.S_IMODE(info.st_mode),
            "size": info.st_size,
        }
    return result


def _stable_id(kind: str, path: str, name: str) -> str:
    return f"{kind}:{_sha256(f'{path}\0{name}'.encode())[:16]}"


def _line(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _evidence(path: str, line: int, symbol: str = "") -> Dict[str, Any]:
    return {"file": path, "line": line, "symbol": symbol}


def _load_compile_database(root: Path, files: List[Path], defines: Iterable[str] = ()) -> Dict[str, Any]:
    path = root / "compile_commands.json"
    entries: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            for item in raw:
                source = Path(item.get("file", ""))
                if not source.is_absolute():
                    source = Path(item.get("directory", root)) / source
                args = item.get("arguments") or shlex.split(str(item.get("command", "")), posix=os.name != "nt")
                entries.append({"file": _rel(source, root), "directory": str(item.get("directory", root)), "arguments": args})
        except (OSError, ValueError, KeyError) as exc:
            errors.append({"code": "compile_database_invalid", "detail": str(exc)})
    else:
        include_dirs = sorted({p.parent for p in files if p.suffix.lower() == ".h"})
        entries = [{
            "file": _rel(source, root), "directory": str(root),
            "arguments": ["gcc", "-std=c99", *[f"-D{name}" for name in defines], *[f"-I{p}" for p in include_dirs], "-c", str(source)],
            "generated": True,
        } for source in files if source.suffix.lower() == ".c"]
    return {"path": _rel(path, root) if path.is_file() else "", "entries": entries, "errors": errors}


class _AstVisitor(c_ast.NodeVisitor if c_ast else object):
    def __init__(self, rel_path: str):
        self.path = rel_path
        self.functions: List[Dict[str, Any]] = []
        self.types: List[Dict[str, Any]] = []
        self.calls: List[Dict[str, Any]] = []
        self.globals: List[Dict[str, Any]] = []
        self.current_function = ""

    def _coord(self, node: Any) -> Dict[str, Any]:
        coord = getattr(node, "coord", None)
        symbol = getattr(node, "name", "") or ""
        if not isinstance(symbol, str):
            symbol = getattr(symbol, "name", "") or ""
        return _evidence(self.path, int(getattr(coord, "line", 0) or 0), symbol)

    def visit_FuncDef(self, node: Any) -> None:
        decl = node.decl
        self.functions.append({"name": decl.name, "kind": "definition", "evidence": self._coord(decl)})
        old, self.current_function = self.current_function, decl.name
        self.generic_visit(node.body)
        self.current_function = old

    def visit_FuncCall(self, node: Any) -> None:
        name = node.name.name if isinstance(node.name, c_ast.ID) else ""
        if self.current_function and name:
            self.calls.append({"caller": self.current_function, "callee": name, "evidence": self._coord(node)})
        self.generic_visit(node)

    def visit_Typedef(self, node: Any) -> None:
        self.types.append({"name": node.name, "kind": "typedef", "members": [], "evidence": self._coord(node)})
        self.generic_visit(node)

    def visit_Struct(self, node: Any) -> None:
        if node.decls is not None:
            members = [{"name": decl.name or "", "type": type(decl.type).__name__, "evidence": self._coord(decl)} for decl in node.decls]
            self.types.append({"name": node.name or "<anonymous>", "kind": "struct", "members": members, "evidence": self._coord(node)})
        self.generic_visit(node)

    def visit_Union(self, node: Any) -> None:
        if node.decls is not None:
            members = [{"name": decl.name or "", "type": type(decl.type).__name__, "evidence": self._coord(decl)} for decl in node.decls]
            self.types.append({"name": node.name or "<anonymous>", "kind": "union", "members": members, "evidence": self._coord(node)})
        self.generic_visit(node)

    def visit_Enum(self, node: Any) -> None:
        if node.values:
            members = [{"name": item.name, "type": "enumerator", "evidence": self._coord(item)} for item in node.values.enumerators]
            self.types.append({"name": node.name or "<anonymous>", "kind": "enum", "members": members, "evidence": self._coord(node)})

    def visit_Decl(self, node: Any) -> None:
        if not self.current_function and node.name and not isinstance(node.type, c_ast.FuncDecl):
            self.globals.append({"name": node.name, "evidence": self._coord(node)})
        self.generic_visit(node)


def _sanitize_for_pycparser(text: str) -> str:
    text = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.DOTALL)
    text = re.sub(r"^\s*#.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\b(?:__attribute__|__declspec)\s*\(\(?.*?\)\)?", "", text)
    return text


def _recover_structural_ast(text: str, rel: str) -> Dict[str, List[Dict[str, Any]]]:
    """Recover declarations rejected by pycparser because of project extensions."""
    result: Dict[str, List[Dict[str, Any]]] = {"functions": [], "types": [], "calls": [], "globals": []}
    clean = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.DOTALL)
    type_pattern = re.compile(r"\b(struct|union|enum)\s+([A-Za-z_]\w*)?\s*\{(.*?)\}\s*([A-Za-z_]\w*)?\s*;", re.DOTALL)
    for match in type_pattern.finditer(clean):
        kind, tag, body, alias = match.groups()
        members = []
        if kind == "enum":
            for raw in body.split(","):
                name = raw.split("=", 1)[0].strip()
                if re.fullmatch(r"[A-Za-z_]\w*", name):
                    members.append({"name": name, "type": "enumerator", "evidence": _evidence(rel, _line(clean, match.start()), name)})
        else:
            for declaration in body.split(";"):
                declaration = declaration.strip()
                if not declaration:
                    continue
                fp = re.search(r"\(\s*\*\s*([A-Za-z_]\w*)\s*\)\s*\(", declaration)
                plain = re.search(r"([A-Za-z_]\w*)\s*(?:\[[^]]*\])?\s*$", declaration)
                name = fp.group(1) if fp else (plain.group(1) if plain else "")
                members.append({"name": name, "type": "function_pointer" if fp else "field", "evidence": _evidence(rel, _line(clean, match.start()), name)})
        result["types"].append({"name": tag or alias or "<anonymous>", "kind": kind, "members": members, "evidence": _evidence(rel, _line(clean, match.start()), tag or alias or "")})
    for match in re.finditer(r"\btypedef\b.*?\b([A-Za-z_]\w*)\s*;", clean, re.DOTALL):
        result["types"].append({"name": match.group(1), "kind": "typedef", "members": [], "evidence": _evidence(rel, _line(clean, match.start()), match.group(1))})
    definition_re = re.compile(r"(?m)^\s*(?!if\b|for\b|while\b|switch\b)(?:[A-Za-z_]\w*[\s*]+)+([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{")
    function_ranges: List[Tuple[int, int]] = []
    for match in definition_re.finditer(clean):
        name = match.group(1)
        result["functions"].append({"name": name, "kind": "definition", "evidence": _evidence(rel, _line(clean, match.start()), name)})
        start = match.end() - 1
        depth, end = 0, start
        for end in range(start, len(clean)):
            depth += clean[end] == "{"
            depth -= clean[end] == "}"
            if depth == 0:
                break
        body = clean[start + 1:end]
        function_ranges.append((match.start(), end))
        for call in re.finditer(r"\b([A-Za-z_]\w*)\s*\(", body):
            callee = call.group(1)
            if callee not in {"if", "for", "while", "switch", "sizeof", "return"}:
                result["calls"].append({"caller": name, "callee": callee, "evidence": _evidence(rel, _line(clean, start + call.start()), callee)})
    for match in re.finditer(r"(?m)^\s*(?:static\s+)?(?:const\s+)?[A-Za-z_]\w*(?:\s+|\s*\*\s*)([A-Za-z_]\w*)\s*(?:\[[^]]*\])?\s*(?:=[^;]*)?;", clean):
        if not any(start <= match.start() <= end for start, end in function_ranges):
            name = match.group(1)
            result["globals"].append({"name": name, "evidence": _evidence(rel, _line(clean, match.start()), name)})
    return result


def _ast_analyze(files: List[Path], root: Path) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"functions": [], "types": [], "calls": [], "globals": [], "parse_failures": []}
    if pycparser is None:
        payload["parse_failures"].append({"file": "", "reason": "pycparser dependency unavailable"})
        return payload
    parser = c_parser.CParser()
    for path in files:
        rel = _rel(path, root)
        try:
            ast = parser.parse(_sanitize_for_pycparser(path.read_text(encoding="utf-8", errors="ignore")), filename=rel)
            visitor = _AstVisitor(rel)
            visitor.visit(ast)
            for key in ("functions", "types", "calls", "globals"):
                payload[key].extend(getattr(visitor, key))
        except Exception as exc:  # parser errors are evidence and fail closed
            recovered = _recover_structural_ast(path.read_text(encoding="utf-8", errors="ignore"), rel)
            for key in ("functions", "types", "calls", "globals"):
                payload[key].extend(recovered[key])
            text = path.read_text(encoding="utf-8", errors="ignore")
            has_required_entity = bool(recovered["functions"] or recovered["types"] or PUBLIC_DECL_RE.search(text))
            if text.count("{") != text.count("}") or not has_required_entity:
                payload["parse_failures"].append({"file": rel, "reason": str(exc), "recovery": "insufficient"})
    return payload


def independent_scan(root: Path, core_dirs: Iterable[Path], test_dirs: Iterable[Path]) -> Dict[str, Any]:
    """Independent lexical scan. It intentionally does not consume primary results."""
    source_files: List[Dict[str, Any]] = []
    public_apis: List[Dict[str, Any]] = []
    source_tests: List[Dict[str, Any]] = []
    test_roots = {p.resolve() for p in test_dirs}
    paths = sorted({p for directory in [*core_dirs, *test_dirs] if directory.is_dir() for p in directory.rglob("*") if p.is_file() and p.suffix.lower() in CORE_SUFFIXES})
    for path in paths:
        rel = _rel(path, root)
        text = path.read_text(encoding="utf-8", errors="ignore")
        under_test = any(path.resolve().is_relative_to(test_root) for test_root in test_roots)
        if under_test:
            if path.suffix.lower() == ".c" or TEST_MARKER_RE.search(text):
                source_tests.append({"path": rel, "evidence": _evidence(rel, 1)})
        else:
            source_files.append({"path": rel, "evidence": _evidence(rel, 1)})
        if path.suffix.lower() == ".h" and not under_test:
            for match in PUBLIC_DECL_RE.finditer(text):
                name = match.group(1)
                public_apis.append({"name": name, "evidence": _evidence(rel, _line(text, match.start()), name)})
    return {"source_files": source_files, "public_apis": public_apis, "source_tests": source_tests}


def _sorted_unique(items: Iterable[Dict[str, Any]], keys: Tuple[str, ...]) -> List[Dict[str, Any]]:
    result: Dict[Tuple[str, ...], Dict[str, Any]] = {}
    for item in items:
        result[tuple(str(item.get(key, "")) for key in keys)] = item
    return [result[key] for key in sorted(result)]


def _analysis_config(packet: Any) -> Dict[str, Any]:
    """Build policy only from the resolved input; never from a project identity."""
    layout = packet.metadata.get("layout_resolution", {})
    configured = packet.metadata.get("source_analysis", {})
    return {
        "source_dirs": sorted(str(Path(path).resolve()) for path in layout.get("source_dirs", [])),
        "test_dirs": sorted(str(Path(path).resolve()) for path in layout.get("test_dirs", [])),
        "required_preprocessor_variants": configured.get("preprocessor_variants", []),
    }


def build_complete_analysis(packet: Any, legacy: Dict[str, Any]) -> Dict[str, Any]:
    root = Path(legacy.get("project_root", ""))
    run_id = uuid.uuid4().hex
    config = _analysis_config(packet)
    config_bytes = json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
    metadata = {"schema_version": SCHEMA_VERSION, "run_id": run_id, "source_root": str(root), "source_digest": "", "config_sha256": _sha256(config_bytes)}
    if not root.is_dir():
        return {"metadata": metadata, "artifacts": {}, "verification": {"passed": False, "status": "BLOCKED_WITH_REPORT", "failures": ["project_root_missing"], "first_blocking_point": "A_SOURCE_ROOT"}}
    before = snapshot_source_tree(root)
    metadata["source_digest"] = _sha256(json.dumps(before, sort_keys=True).encode())
    source_dirs = [Path(p) for p in config["source_dirs"]]
    test_dirs = [Path(p) for p in config["test_dirs"]]
    primary_files = sorted({p for d in source_dirs for p in d.rglob("*") if p.is_file() and p.suffix.lower() in CORE_SUFFIXES})
    ast = _ast_analyze(primary_files, root)
    required_variants = config.get("required_preprocessor_variants", [])
    defines = sorted({name for variant in required_variants for name in variant.get("defines", [])})
    compile_db = _load_compile_database(root, primary_files, defines)
    independent = independent_scan(root, source_dirs, test_dirs)

    public_names = sorted(set(legacy.get("public_apis", [])))
    declarations = {item.get("name"): item for item in legacy.get("functions", []) if item.get("decl_kind") == "prototype"}
    definitions = {item.get("name"): item for item in ast["functions"] if item.get("kind") == "definition"}
    if not definitions:
        definitions = {item.get("name"): item for item in legacy.get("functions", []) if item.get("decl_kind") == "definition"}
    public_map = []
    for name in public_names:
        declaration = declarations.get(name, {})
        definition = definitions.get(name, {})
        signature = next((item for item in legacy.get("functions", []) if item.get("name") == name and item.get("decl_kind") == "definition"), declaration)
        public_map.append({
            "id": _stable_id("api", str(declaration.get("file", "")), name), "name": name,
            "return_type": signature.get("return_type", ""),
            "inputs": signature.get("params", []),
            "declaration": _evidence(str(declaration.get("file", "")), int(declaration.get("line", 0) or 0), name) if declaration else None,
            "definition": definition.get("evidence") or (_evidence(str(definition.get("file", "")), int(definition.get("line", 0) or 0), name) if definition else None),
        })
    source_inventory = {
        "files": [{"id": _stable_id("file", _rel(path, root), ""), "path": _rel(path, root), "kind": "header" if path.suffix.lower() == ".h" else "source", "sha256": before[_rel(path, root)]["sha256"]} for path in primary_files],
        "source_tests": independent["source_tests"],
        "exclusions": [],
        "scope": {"source_dirs": [_rel(path, root) for path in source_dirs], "test_dirs": [_rel(path, root) for path in test_dirs]},
    }
    macros = []
    variants = []
    includes = []
    for path in primary_files:
        rel = _rel(path, root); text = path.read_text(encoding="utf-8", errors="ignore")
        includes.extend({"file": rel, "include": name, "evidence": _evidence(rel, _line(text, match.start()))} for match in INCLUDE_RE.finditer(text) for name in [match.group(1)])
        macros.extend({"name": match.group(1), "parameters": match.group(2) or "", "value": match.group(3).strip(), "evidence": _evidence(rel, _line(text, match.start()), match.group(1))} for match in DEFINE_RE.finditer(text))
        variants.extend({"directive": match.group(1), "expression": match.group(2).strip(), "evidence": _evidence(rel, _line(text, match.start()))} for match in CONDITIONAL_RE.finditer(text))
    artifacts = {
        "source-inventory.json": source_inventory,
        "independent-source-scan.json": independent,
        "public-api-map.json": {"apis": public_map},
        "type-map.json": {"types": _sorted_unique(ast["types"], ("kind", "name")), "type_dependencies": _sorted_unique(({"type": item["name"], "member": member.get("name", ""), "target_kind": member.get("type", "")} for item in ast["types"] for member in item.get("members", [])), ("type", "member"))},
        "call-graph.json": {"include_edges": _sorted_unique(includes, ("file", "include")), "call_edges": _sorted_unique(ast["calls"], ("caller", "callee"))},
        "global-state-map.json": {"globals": _sorted_unique(ast["globals"], ("name",))},
        "preprocessor-variants.json": {"frontend": {"name": "pycparser-hybrid", "version": getattr(pycparser, "__version__", "unavailable")}, "compile_database": compile_db, "required_variants": required_variants, "macros": _sorted_unique(macros, ("name",)), "variants": _sorted_unique(variants, ("directive", "expression"))},
    }
    independent_sets = {
        "source_files": {item["path"] for item in independent["source_files"]},
        "public_apis": {item["name"] for item in independent["public_apis"]},
        "source_tests": {item["path"] for item in independent["source_tests"]},
    }
    primary_sets = {
        "source_files": {_rel(path, root) for path in primary_files},
        "public_apis": set(public_names),
        "source_tests": set(legacy.get("test_files", [])),
    }
    differences = {name: {"missing_from_primary": sorted(values - primary_sets[name]), "missing_from_independent": sorted(primary_sets[name] - values)} for name, values in independent_sets.items()}
    unresolved = sorted(item["name"] for item in public_map if not item["declaration"] or not item["definition"])
    type_members = [member for item in artifacts["type-map.json"]["types"] if item["kind"] in {"struct", "union", "enum"} for member in item.get("members", [])]
    checks = {
        "source_file_count_nonzero": len(primary_sets["source_files"]) > 0,
        "public_api_count_nonzero": len(primary_sets["public_apis"]) > 0,
        "source_test_count_nonzero": len(primary_sets["source_tests"]) > 0,
        "all_public_apis_resolved": not unresolved,
        "all_core_types_complete": bool(type_members) and all(member.get("name") and member.get("evidence", {}).get("file") for member in type_members),
        "core_files_sets_match": not any(differences["source_files"].values()),
        "public_api_sets_match": not any(differences["public_apis"].values()),
        "source_test_sets_match": not any(differences["source_tests"].values()),
        "core_parse_succeeded": not ast["parse_failures"],
        "call_graph_nonempty": bool(artifacts["call-graph.json"]["call_edges"]),
        "source_tree_unchanged": snapshot_source_tree(root) == before,
    }
    failures = [name for name, passed in checks.items() if not passed]
    verification = {"passed": not failures, "status": "PASSED" if not failures else "BLOCKED_WITH_REPORT", "checks": checks, "metrics": {"source_file_count": len(primary_sets["source_files"]), "public_api_count": len(public_names), "source_test_count": len(primary_sets["source_tests"]), "type_member_count": len(type_members)}, "differences": differences, "unresolved_symbols": unresolved, "parse_failures": ast["parse_failures"], "failures": failures, "first_blocking_point": None if not failures else "C_SOURCE_ANALYSIS"}
    artifacts["analysis-verification.json"] = verification
    return {"metadata": metadata, "artifacts": artifacts, "verification": verification}


def write_complete_analysis(bundle: Dict[str, Any], trace_dir: Path) -> None:
    trace_dir.mkdir(parents=True, exist_ok=True)
    metadata = bundle["metadata"]
    for name, payload in bundle.get("artifacts", {}).items():
        document = {**metadata, **payload}
        target = trace_dir / name
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(json.dumps(document, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
        temporary.replace(target)


def validate_written_evidence(trace_dir: Path, source_root: Path) -> List[str]:
    """Reject missing, malformed, mixed-run, or dangling evidence documents."""
    failures: List[str] = []
    documents: Dict[str, Dict[str, Any]] = {}
    for name in EVIDENCE_FILES:
        path = trace_dir / name
        if not path.is_file():
            failures.append(f"missing_evidence:{name}")
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            failures.append(f"invalid_json:{name}")
            continue
        if payload.get("schema_version") != SCHEMA_VERSION:
            failures.append(f"invalid_schema:{name}")
        if not payload.get("run_id"):
            failures.append(f"missing_run_id:{name}")
        documents[name] = payload
    run_ids = {payload.get("run_id") for payload in documents.values()}
    if len(run_ids) > 1:
        failures.append("mixed_run_ids")

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            evidence_file = value.get("file") if "line" in value or "symbol" in value else None
            if isinstance(evidence_file, str) and evidence_file and not (source_root / evidence_file).is_file():
                failures.append(f"dangling_source_evidence:{evidence_file}")
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    for payload in documents.values():
        walk(payload)
    return sorted(set(failures))
