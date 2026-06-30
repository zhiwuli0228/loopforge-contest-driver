from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agent_task_packet import AgentTaskPacket, SourceLayout


INCLUDE_RE = re.compile(r'^\s*#include\s+[<"]([^>"]+)[>"]', re.MULTILINE)
MACRO_RE = re.compile(r"^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)
STRUCT_RE = re.compile(r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)")
TYPEDEF_RE = re.compile(r"\btypedef\s+.+?\s+([A-Za-z_][A-Za-z0-9_]*)\s*;", re.DOTALL)
PROTOTYPE_RE = re.compile(r"(?m)^\s*([A-Za-z_][A-Za-z0-9_\s\*]*?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^;{}]*)\)\s*;")
DEFINITION_RE = re.compile(r"(?ms)^\s*([A-Za-z_][A-Za-z0-9_\s\*]*?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^;{}]*)\)\s*\{([^{}]*)\}")
ASSERT_RE = re.compile(r"\b(assert(?:_[A-Za-z0-9_]+)?)\s*\(([^)]*)\)")
TEST_NAME_RE = re.compile(r"(?m)^\s*(?:void|int)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
CONTROL_KEYWORDS = {"if", "for", "while", "switch", "return", "sizeof"}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def _sanitize_rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def _collect_files(directories: List[Path], suffixes: Tuple[str, ...]) -> List[Path]:
    results: List[Path] = []
    for directory in directories:
        if not directory.is_dir():
            continue
        for suffix in suffixes:
            results.extend(sorted(path for path in directory.rglob(f"*{suffix}") if path.is_file()))
    return results


def _body_kind(return_type: str, body: str) -> Tuple[str, Optional[str]]:
    normalized = " ".join(body.split())
    if not normalized:
        return ("empty", None)
    return_number = re.fullmatch(r"return\s+(-?\d+)\s*;", normalized)
    if return_number:
        return ("return_number", return_number.group(1))
    if normalized in {"return NULL;", "return null;", "return 0;"} and "*" in return_type:
        return ("return_null", None)
    return_string = re.fullmatch(r'return\s+"([^"]*)"\s*;', normalized)
    if return_string:
        return ("return_string", return_string.group(1))
    return ("complex", None)


def _parse_params(params_text: str) -> List[Dict[str, str]]:
    params_text = params_text.strip()
    if not params_text or params_text == "void":
        return []
    params: List[Dict[str, str]] = []
    for index, raw in enumerate(params_text.split(",")):
        candidate = raw.strip()
        parts = candidate.rsplit(" ", 1)
        if len(parts) == 2 and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", parts[1].replace("*", "")):
            type_text, name = parts
        else:
            type_text, name = candidate, f"arg{index}"
        params.append({"name": name.replace("*", "").strip() or f"arg{index}", "type": type_text.strip()})
    return params


def _pick_project_root(packet: AgentTaskPacket) -> Tuple[Optional[Path], List[Path], List[Path]]:
    candidates = [packet.paths.source_root]
    candidates.extend(path for path in packet.paths.source_root.iterdir() if path.is_dir())
    best_root: Optional[Path] = None
    best_sources: List[Path] = []
    best_tests: List[Path] = []
    best_score = -1

    for candidate in candidates:
        source_dirs = [candidate / rel for rel in packet.source_dirs if (candidate / rel).is_dir()]
        test_dirs = [candidate / rel for rel in packet.test_dirs if (candidate / rel).is_dir()]
        score = len(source_dirs) * 10 + len(test_dirs)
        if source_dirs or test_dirs:
            if score > best_score:
                best_root = candidate.resolve()
                best_sources = source_dirs
                best_tests = test_dirs
                best_score = score
    return best_root, best_sources, best_tests


def analyze_source(packet: AgentTaskPacket) -> Dict[str, Any]:
    readme_path = Path(packet.metadata.get("selected_readme_path", "")).resolve() if packet.metadata.get("selected_readme_path") else None
    fallback_readme = Path(packet.metadata.get("fallback_readme_path", "")).resolve() if packet.metadata.get("fallback_readme_path") else None

    project_root, source_dirs, test_dirs = _pick_project_root(packet)
    packet.source_layout = SourceLayout(
        readme_path=readme_path,
        fallback_readme_path=fallback_readme,
        project_root=project_root,
        source_dirs=source_dirs,
        test_dirs=test_dirs,
    )

    src_files = _collect_files(source_dirs, (".c", ".h"))
    test_files = _collect_files(test_dirs, (".c", ".h"))

    functions: List[Dict[str, Any]] = []
    types: List[Dict[str, Any]] = []
    macros: List[Dict[str, Any]] = []
    include_graph: List[Dict[str, Any]] = []
    public_api_names: List[str] = []
    seen_function_keys = set()
    project_base = project_root or packet.paths.source_root

    for path in src_files + test_files:
        text = _read_text(path)
        rel = _sanitize_rel(path, project_base)
        include_graph.append({"file": rel, "includes": _dedupe(INCLUDE_RE.findall(text))})
        for macro in MACRO_RE.findall(text):
            macros.append({"name": macro, "file": rel})
        for struct_name in STRUCT_RE.findall(text):
            types.append({"name": struct_name, "kind": "struct", "file": rel})
        for typedef_name in TYPEDEF_RE.findall(text):
            types.append({"name": typedef_name, "kind": "typedef", "file": rel})
        if path in src_files:
            for return_type, name, params_text in PROTOTYPE_RE.findall(text):
                if name in CONTROL_KEYWORDS:
                    continue
                key = (rel, name, params_text.strip(), "prototype")
                if key in seen_function_keys:
                    continue
                seen_function_keys.add(key)
                params = _parse_params(params_text)
                functions.append(
                    {
                        "name": name,
                        "return_type": " ".join(return_type.split()),
                        "params": params,
                        "params_text": params_text.strip(),
                        "file": rel,
                        "decl_kind": "prototype",
                        "body_kind": "prototype_only",
                        "body_value": None,
                        "module_hint": Path(rel).stem,
                    }
                )
                public_api_names.append(name)

            for return_type, name, params_text, body in DEFINITION_RE.findall(text):
                if name in CONTROL_KEYWORDS:
                    continue
                params = _parse_params(params_text)
                kind, value = _body_kind(return_type, body)
                key = (rel, name, params_text.strip(), "definition")
                if key in seen_function_keys:
                    continue
                seen_function_keys.add(key)
                functions.append(
                    {
                        "name": name,
                        "return_type": " ".join(return_type.split()),
                        "params": params,
                        "params_text": params_text.strip(),
                        "file": rel,
                        "decl_kind": "definition",
                        "body_kind": kind,
                        "body_value": value,
                        "module_hint": Path(rel).stem,
                    }
                )
                public_api_names.append(name)

    hinted_api_names = [name for name in packet.api_name_hints if any(item["name"] == name for item in functions)]
    if hinted_api_names:
        public_apis = _dedupe(hinted_api_names + sorted(public_api_names))
    else:
        public_apis = _dedupe(sorted(public_api_names))

    tests: List[Dict[str, Any]] = []
    for path in test_files:
        text = _read_text(path)
        rel = _sanitize_rel(path, project_base)
        assertions = [{"macro": macro, "expr": expr.strip()} for macro, expr in ASSERT_RE.findall(text)]
        referenced_apis = [name for name in public_apis if re.search(rf"\b{re.escape(name)}\b", text)]
        test_names = [name for name in TEST_NAME_RE.findall(text) if name not in CONTROL_KEYWORDS]
        if not test_names:
            test_names = [Path(rel).stem]
        tests.append(
            {
                "file": rel,
                "test_names": _dedupe(test_names),
                "assertions": assertions,
                "referenced_apis": _dedupe(referenced_apis),
            }
        )

    test_to_api_mapping = [
        {
            "source_test": test["file"],
            "test_names": test["test_names"],
            "referenced_apis": test["referenced_apis"],
            "assertion_count": len(test["assertions"]),
        }
        for test in tests
    ]

    source_file_records = [{"path": _sanitize_rel(path, project_base), "module_hint": Path(path).stem} for path in src_files]
    test_file_records = [{"path": _sanitize_rel(path, project_base)} for path in test_files]
    function_names = [item["name"] for item in functions]
    support_level = "source-driven-c" if src_files else "unsupported"

    analysis = {
        "ok": readme_path is not None and project_root is not None and bool(src_files) and bool(test_files),
        "readme_path": str(readme_path) if readme_path else "",
        "fallback_readme_path": str(fallback_readme) if fallback_readme else "",
        "project_root": str(project_root) if project_root else "",
        "source_dirs": [str(path.relative_to(project_base)).replace("\\", "/") for path in source_dirs] if project_root else [],
        "test_dirs": [str(path.relative_to(project_base)).replace("\\", "/") for path in test_dirs] if project_root else [],
        "src_files": [item["path"] for item in source_file_records],
        "test_files": [item["path"] for item in test_file_records],
        "source_files": source_file_records,
        "functions": functions,
        "public_apis": public_apis,
        "function_table": functions,
        "types": _dedupe(sorted(item["name"] for item in types)),
        "type_table": types,
        "macros": _dedupe(sorted(item["name"] for item in macros)),
        "macro_table": macros,
        "include_graph": include_graph,
        "tests": tests,
        "test_cases": tests,
        "test_to_api_mapping": test_to_api_mapping,
        "assertion_count": sum(len(item["assertions"]) for item in tests),
        "io_boundaries": _dedupe(sorted(name for name in function_names if any(token in name.lower() for token in ["read", "write", "open", "close", "get", "set", "io"]))),
        "module_hints": _dedupe(packet.module_hints + [item["module_hint"] for item in source_file_records]),
        "support_level": support_level,
        "readme_excerpt": "\n".join(line.strip() for line in (_read_text(readme_path) if readme_path else "").splitlines()[:20] if line.strip()),
    }

    if readme_path is None:
        packet.add_issue("readme_missing", f"README candidate not found under {packet.paths.source_root}")
    if project_root is None:
        packet.add_issue("source_layout_missing", f"Expected source/test directories under {packet.paths.source_root} or an immediate child directory")
    if not src_files:
        packet.add_issue("source_files_missing", "No C source files were detected in the resolved source directories")
    if not test_files:
        packet.add_issue("test_files_missing", "No C test files were detected in the resolved test directories")
    if support_level == "unsupported":
        packet.add_issue("semantic_template_missing", "The source tree does not expose a usable C source/test layout for migration")
    return analysis


def evaluate_semantic_equivalence(
    packet: AgentTaskPacket,
    analysis: Dict[str, Any],
    project_dir: Path,
    project_payload: Dict[str, Any],
    verification_payload: Dict[str, Any],
) -> Dict[str, Any]:
    src_files = sorted(path for path in (project_dir / "src").rglob("*.rs") if path.is_file())
    test_files = sorted(path for path in (project_dir / "tests").rglob("*.rs") if path.is_file())
    rust_text = "\n".join(_read_text(path) for path in src_files + test_files)
    checks: List[Dict[str, Any]] = []

    has_cargo = (project_dir / "Cargo.toml").is_file()
    checks.append({"name": "cargo_manifest", "passed": has_cargo, "detail": "Cargo.toml exists"})

    meaningful_src = [path for path in src_files if len([line for line in _read_text(path).splitlines() if line.strip()]) >= 5]
    non_empty_crate = bool(meaningful_src) and bool(test_files)
    checks.append({"name": "non_empty_crate", "passed": non_empty_crate, "detail": "crate contains non-trivial Rust source and tests"})

    no_placeholder = "todo!(" not in rust_text and "unimplemented!(" not in rust_text
    checks.append({"name": "no_placeholders", "passed": no_placeholder, "detail": "Rust source does not contain placeholder macros"})

    test_assertions_ok = True
    test_assert_count = 0
    test_functions = 0
    for path in test_files:
        text = _read_text(path)
        file_asserts = text.count("assert!(") + text.count("assert_eq!(") + text.count("assert_ne!(")
        test_functions += text.count("#[test]")
        if file_asserts == 0:
            test_assertions_ok = False
        test_assert_count += file_asserts
    checks.append({"name": "assertive_tests", "passed": test_assertions_ok and test_assert_count > 0, "detail": "each Rust test file contains assertions", "assert_count": test_assert_count})

    mapped_apis = project_payload.get("mapped_apis", [])
    unsupported_apis = project_payload.get("unsupported_apis", [])
    api_matches = [name for name in mapped_apis if re.search(rf"\b{re.escape(name)}\b", rust_text)]
    semantic_map_ok = bool(mapped_apis) and len(api_matches) == len(mapped_apis)
    checks.append(
        {
            "name": "api_mapping",
            "passed": semantic_map_ok,
            "detail": "source APIs are represented in generated Rust modules",
            "mapped_apis": api_matches,
            "unsupported_apis": unsupported_apis,
        }
    )

    mapped_source_tests = [item for item in project_payload.get("test_mapping", []) if item.get("source_test")]
    source_test_count = len(analysis.get("tests", []))
    coverage_ok = len(test_files) >= 1 and len(mapped_source_tests) >= source_test_count and test_functions >= max(1, len(mapped_source_tests))
    checks.append(
        {
            "name": "test_mapping_gate",
            "passed": coverage_ok,
            "detail": "semantic gate is backed by explicit source-to-Rust test mappings",
            "mapped_source_tests": len(mapped_source_tests),
            "source_test_count": source_test_count,
            "rust_test_functions": test_functions,
        }
    )

    semantic_claim = project_payload.get("semantic_equivalence_claim", "not_claimed")
    claim_ok = semantic_claim not in {"not_claimed", "bootstrap_skeleton_only", "not_generated"}
    checks.append(
        {
            "name": "semantic_claim_gate",
            "passed": claim_ok,
            "detail": "semantic equivalence requires an explicit positive claim backed by generated evidence",
            "semantic_equivalence_claim": semantic_claim,
        }
    )

    cargo_gates_ok = bool(verification_payload.get("build_ok")) and bool(verification_payload.get("test_ok"))
    checks.append(
        {
            "name": "verification_dependency",
            "passed": cargo_gates_ok,
            "detail": "semantic gate requires successful cargo build and cargo test first",
        }
    )

    passed = all(check["passed"] for check in checks)
    failing = [check["name"] for check in checks if not check["passed"]]
    if not passed:
        packet.add_issue("semantic_gate_failed", f"semantic checks failed: {', '.join(failing)}")
    return {
        "passed": passed,
        "checks": checks,
        "failing_checks": failing,
    }
