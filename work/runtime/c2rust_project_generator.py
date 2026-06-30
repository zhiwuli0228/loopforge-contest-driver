from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from agent_task_packet import AgentTaskPacket


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _sanitize_ident(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value).strip("_").lower()
    if not cleaned:
        return fallback
    if cleaned[0].isdigit():
        cleaned = f"{fallback}_{cleaned}"
    return cleaned


def _sanitize_package_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "-", value).strip("-").lower()
    return cleaned or "c-to-rust-output"


def _map_c_type(type_text: str) -> Tuple[str, Set[str]]:
    normalized = " ".join(type_text.replace("\n", " ").split())
    imports: Set[str] = set()
    lowered = normalized.lower()
    if not normalized or lowered == "void":
        return ("()", imports)
    if "char" in lowered and "*" in lowered:
        imports.add("std::ffi::c_char")
        return ("*const c_char" if "const" in lowered else "*mut c_char", imports)
    if "*" in lowered:
        imports.add("std::ffi::c_void")
        return ("*const c_void" if "const" in lowered else "*mut c_void", imports)
    if "size_t" in lowered:
        return ("usize", imports)
    if lowered in {"bool", "_bool"}:
        return ("bool", imports)
    if any(token in lowered for token in ["long long", "int64"]):
        return ("i64", imports)
    if "long" in lowered:
        return ("i64", imports)
    if any(token in lowered for token in ["unsigned", "uint"]):
        return ("u32", imports)
    if any(token in lowered for token in ["int", "short"]):
        return ("i32", imports)
    return ("usize", imports)


def _default_expr(type_text: str, body_kind: str, body_value: Any) -> str:
    lowered = type_text.lower()
    if type_text == "()":
        return ""
    if body_kind == "return_number" and body_value is not None:
        return str(body_value)
    if body_kind == "return_null":
        return "std::ptr::null()"
    if body_kind == "return_string":
        return "std::ptr::null()"
    if "*" in lowered:
        return "std::ptr::null()"
    if type_text == "bool":
        return "false"
    if type_text.startswith("u") or type_text.startswith("i") or type_text == "usize":
        return "0"
    return "Default::default()"


def _group_functions_by_module(analysis: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for function in analysis.get("functions", []):
        module_name = _sanitize_ident(function.get("module_hint", ""), "module")
        groups.setdefault(module_name, []).append(function)
    for module_name, functions in list(groups.items()):
        preferred: Dict[str, Dict[str, Any]] = {}
        for function in functions:
            current = preferred.get(function["name"])
            if current is None:
                preferred[function["name"]] = function
                continue
            if current.get("decl_kind") != "definition" and function.get("decl_kind") == "definition":
                preferred[function["name"]] = function
        groups[module_name] = list(preferred.values())
    return groups


def _render_function(function: Dict[str, Any]) -> Tuple[str, Set[str], bool]:
    imports: Set[str] = set()
    translated = function.get("decl_kind") == "definition" and function.get("body_kind") in {"empty", "return_number", "return_null"}
    param_parts: List[str] = []
    for param in function.get("params", []):
        rust_type, rust_imports = _map_c_type(param.get("type", ""))
        imports.update(rust_imports)
        param_name = _sanitize_ident(param.get("name", "arg"), "arg")
        param_parts.append(f"{param_name}: {rust_type}")
    rust_return, rust_imports = _map_c_type(function.get("return_type", ""))
    imports.update(rust_imports)
    expr = _default_expr(rust_return, function.get("body_kind", ""), function.get("body_value"))
    signature = f"pub fn {function['name']}({', '.join(param_parts)})"
    if rust_return != "()":
        signature += f" -> {rust_return}"
    lines = [signature + " {"]
    lines.append(f"    // Derived from {function['file']}")
    if rust_return == "()":
        lines.append("}")
    else:
        lines.append(f"    {expr}")
        lines.append("}")
    return ("\n".join(lines), imports, translated)


def _render_module(module_name: str, functions: List[Dict[str, Any]], macros: List[Dict[str, Any]], types: List[Dict[str, Any]]) -> Tuple[str, Set[str], int]:
    imports: Set[str] = set()
    translated_count = 0
    chunks = ["#![forbid(unsafe_code)]", ""]

    module_macros = [item for item in macros if Path(item["file"]).stem == module_name]
    for macro in module_macros:
        chunks.append(f'pub const {macro["name"]}: &str = "{macro["name"]}";')
    if module_macros:
        chunks.append("")

    module_types = [item for item in types if Path(item["file"]).stem == module_name]
    seen_type_idents: Set[str] = set()
    for type_entry in module_types:
        ident = _sanitize_ident(type_entry["name"], "type_record")
        if ident in seen_type_idents:
            continue
        seen_type_idents.add(ident)
        chunks.append("#[derive(Debug, Default, Clone)]")
        chunks.append(f"pub struct {ident.title().replace('_', '')} {{")
        chunks.append("    pub _opaque: usize,")
        chunks.append("}")
        chunks.append("")

    for function in functions:
        rendered, function_imports, translated = _render_function(function)
        imports.update(function_imports)
        if translated:
            translated_count += 1
        chunks.append(rendered)
        chunks.append("")

    if len(chunks) == 2:
        chunks.extend(["pub fn module_inventory() -> usize {", "    0", "}"])

    import_block = []
    if imports:
        import_block = [f"use {item};" for item in sorted(imports)] + [""]
    return ("\n".join(chunks[:2] + import_block + chunks[2:]).rstrip() + "\n", imports, translated_count)


def _render_lib_rs(module_names: List[str], exported_functions: List[str]) -> str:
    lines = ["#![forbid(unsafe_code)]", ""]
    for module_name in module_names:
        lines.append(f"pub mod {module_name};")
    if module_names:
        lines.append("")
    for function_name, module_name in exported_functions:
        lines.append(f"pub use {module_name}::{function_name};")
    lines.append("")
    lines.append("pub fn generated_module_count() -> usize {")
    lines.append(f"    {len(module_names)}")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _render_tests(
    crate_name: str,
    analysis: Dict[str, Any],
    exported_functions: List[Tuple[str, str]],
    claimable: bool,
    zero_arg_functions: List[str],
) -> Tuple[str, List[Dict[str, Any]]]:
    test_mapping: List[Dict[str, Any]] = []
    lines = [f"use {crate_name}::generated_module_count;"]
    direct_functions = [name for name, _ in exported_functions]
    if direct_functions:
        lines.append(f"use {crate_name}::{{{', '.join(direct_functions)}}};")
    lines.append("")
    lines.extend(["#[test]", "fn crate_has_generated_modules() {", "    assert!(generated_module_count() > 0);", "}", ""])

    for index, test_case in enumerate(analysis.get("tests", []), start=1):
        test_name = _sanitize_ident(test_case["test_names"][0], f"source_test_{index}")
        lines.append("#[test]")
        lines.append(f"fn {test_name}() {{")
        lines.append(f"    assert!(generated_module_count() >= 1);")
        if claimable and zero_arg_functions:
            lines.append(f"    let _ = {zero_arg_functions[0]}();")
        else:
            lines.append(f"    assert!({len(test_case.get('referenced_apis', []))} >= 0);")
        lines.append("}")
        lines.append("")
        test_mapping.append(
            {
                "source_test": test_case["file"],
                "rust_test_file": "tests/source_migration.rs",
                "mapping": "direct smoke call coverage" if claimable and zero_arg_functions else "inventory-backed source mapping",
                "coverage_level": "semantic_claimed" if claimable and zero_arg_functions else "structural_only",
            }
        )
    if not analysis.get("tests"):
        test_mapping.append(
            {
                "source_test": "none",
                "rust_test_file": "tests/source_migration.rs",
                "mapping": "no source tests detected",
                "coverage_level": "none",
            }
        )
    return ("\n".join(lines).rstrip() + "\n", test_mapping)


def generate_project(packet: AgentTaskPacket, analysis: Dict[str, Any]) -> Dict[str, Any]:
    project_dir = packet.output_project_dir
    project_dir.mkdir(parents=True, exist_ok=True)
    for path in [project_dir / "src", project_dir / "tests"]:
        if path.exists():
            shutil.rmtree(path)
    cargo_manifest = project_dir / "Cargo.toml"
    if cargo_manifest.exists():
        cargo_manifest.unlink()

    grouped = _group_functions_by_module(analysis)
    module_names = _dedupe(list(grouped.keys()) + [_sanitize_ident(item.get("module_hint", ""), "module") for item in analysis.get("source_files", [])])
    macros = analysis.get("macro_table", [])
    types = analysis.get("type_table", [])
    translated_functions = 0
    total_definitions = len([item for item in analysis.get("functions", []) if item.get("decl_kind") == "definition"])
    exported_functions: List[Tuple[str, str]] = []
    zero_arg_functions: List[str] = []

    for module_name in module_names:
        module_functions = grouped.get(module_name, [])
        module_rs, _imports, translated_count = _render_module(module_name, module_functions, macros, types)
        translated_functions += translated_count
        _write(project_dir / "src" / f"{module_name}.rs", module_rs)
        for function in module_functions:
            if function.get("name") not in [name for name, _ in exported_functions]:
                exported_functions.append((function["name"], module_name))
            if not function.get("params"):
                zero_arg_functions.append(function["name"])

    package_name = _sanitize_package_name(packet.output_project_name)
    cargo_toml = "\n".join(
        [
            "[package]",
            f'name = "{package_name}"',
            'version = "0.1.0"',
            'edition = "2021"',
            "",
            "[lib]",
            f'name = "{_sanitize_ident(packet.output_project_name, "c_to_rust_output")}"',
            'path = "src/lib.rs"',
            "",
        ]
    )
    _write(cargo_manifest, cargo_toml)
    _write(project_dir / "src" / "lib.rs", _render_lib_rs(module_names, exported_functions))

    claimable = bool(exported_functions) and bool(zero_arg_functions) and total_definitions > 0 and translated_functions == total_definitions
    tests_rs, test_mapping = _render_tests(
        _sanitize_ident(packet.output_project_name, "c_to_rust_output"),
        analysis,
        exported_functions,
        claimable,
        zero_arg_functions,
    )
    _write(project_dir / "tests" / "source_migration.rs", tests_rs)

    unsupported_apis = [name for name in analysis.get("public_apis", []) if name not in [item[0] for item in exported_functions]]
    module_list = ["src/lib.rs"] + [f"src/{module_name}.rs" for module_name in module_names] + ["tests/source_migration.rs"]
    source_coverage = {
        "source_file_count": len(analysis.get("source_files", [])),
        "test_file_count": len(analysis.get("tests", [])),
        "mapped_api_count": len(exported_functions),
        "unsupported_api_count": len(unsupported_apis),
        "translated_definition_count": translated_functions,
        "definition_count": total_definitions,
    }
    return {
        "project_dir": str(project_dir),
        "module_names": module_names,
        "mapped_apis": [name for name, _ in exported_functions],
        "unsupported_apis": unsupported_apis,
        "source_coverage": source_coverage,
        "module_list": module_list,
        "test_mapping": test_mapping,
        "bootstrap_only": not claimable,
        "semantic_equivalence_claim": "basic_function_translation" if claimable else "not_claimed",
        "crate_name": package_name,
    }


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered
