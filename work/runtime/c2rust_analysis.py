from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_task_packet import AgentTaskPacket, SourceLayout


FUNCTION_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\([^;{}]*\)\s*[;{]")
STRUCT_RE = re.compile(r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)")
MACRO_RE = re.compile(r"^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _collect_files(root: Optional[Path], suffixes: List[str]) -> List[Path]:
    if root is None or not root.is_dir():
        return []
    results: List[Path] = []
    for suffix in suffixes:
        results.extend(sorted(path for path in root.rglob(f"*{suffix}") if path.is_file()))
    return results


def _unique(items: List[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def analyze_source(packet: AgentTaskPacket) -> Dict[str, Any]:
    source_root = packet.paths.source_root
    readme_path: Optional[Path] = None
    for name in packet.readme_candidates:
        candidate = source_root / name
        if candidate.is_file():
            readme_path = candidate.resolve()
            break

    flashdb_root: Optional[Path] = None
    for candidate in [source_root, source_root / "FlashDB"]:
        if (candidate / "src").is_dir() and (candidate / "tests").is_dir():
            flashdb_root = candidate.resolve()
            break

    src_dir = flashdb_root / "src" if flashdb_root else None
    tests_dir = flashdb_root / "tests" if flashdb_root else None
    packet.source_layout = SourceLayout(readme_path=readme_path, flashdb_root=flashdb_root, src_dir=src_dir, tests_dir=tests_dir)

    src_files = _collect_files(src_dir, [".c", ".h"])
    test_files = _collect_files(tests_dir, [".c", ".h"])
    readme_text = _read_text(readme_path) if readme_path else ""
    api_names: List[str] = []
    struct_names: List[str] = []
    macro_names: List[str] = []
    for path in src_files + test_files:
        text = _read_text(path)
        api_names.extend(name for name in FUNCTION_RE.findall(text) if name not in {"if", "for", "while", "switch", "return", "sizeof"})
        struct_names.extend(STRUCT_RE.findall(text))
        macro_names.extend(MACRO_RE.findall(text))

    public_apis = _unique(sorted(api_names))
    structs = _unique(sorted(struct_names))
    macros = _unique(sorted(macro_names))

    support_level = "unsupported"
    lowered = readme_text.lower()
    joined_names = " ".join(public_apis).lower()
    if "flashdb" in lowered or "flashdb" in joined_names or "flashdb" in " ".join(path.name.lower() for path in src_files):
        support_level = "flashdb-kv-template"

    io_boundaries = []
    for candidate in public_apis:
        if any(token in candidate.lower() for token in ["read", "write", "get", "set", "store", "flash"]):
            io_boundaries.append(candidate)

    analysis = {
        "ok": readme_path is not None and flashdb_root is not None and bool(src_files) and bool(test_files),
        "readme_path": str(readme_path) if readme_path else "",
        "flashdb_root": str(flashdb_root) if flashdb_root else "",
        "src_files": [str(path.relative_to(flashdb_root)).replace("\\", "/") for path in src_files] if flashdb_root else [],
        "test_files": [str(path.relative_to(flashdb_root)).replace("\\", "/") for path in test_files] if flashdb_root else [],
        "public_apis": public_apis,
        "structs": structs,
        "macros": macros,
        "io_boundaries": _unique(sorted(io_boundaries)),
        "support_level": support_level,
        "readme_excerpt": "\n".join(line.strip() for line in readme_text.splitlines()[:20] if line.strip()),
    }
    if readme_path is None:
        packet.add_issue("readme_missing", f"README candidate not found under {source_root}")
    if flashdb_root is None:
        packet.add_issue("flashdb_layout_missing", f"Expected src/tests under {source_root} or {source_root / 'FlashDB'}")
    if not src_files:
        packet.add_issue("source_files_missing", "No C source files were detected in the resolved src directory")
    if not test_files:
        packet.add_issue("test_files_missing", "No C test files were detected in the resolved tests directory")
    if support_level == "unsupported":
        packet.add_issue("semantic_template_missing", "The source tree does not match the supported FlashDB migration template")
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
    api_matches = [name for name in mapped_apis if name in rust_text]
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

    test_mapping = project_payload.get("test_mapping", [])
    mapped_source_tests = [item for item in test_mapping if item.get("source_test")]
    source_test_count = len(analysis.get("test_files", []))
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

    bootstrap_only = bool(project_payload.get("bootstrap_only", False))
    bootstrap_gate = not bootstrap_only
    checks.append(
        {
            "name": "bootstrap_only_guard",
            "passed": bootstrap_gate,
            "detail": "bootstrap skeletons cannot claim full semantic equivalence",
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
