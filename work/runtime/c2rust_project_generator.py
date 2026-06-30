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


def _rust_type_name(value: str) -> str:
    return _sanitize_ident(value, "type_record").title().replace("_", "")


def _map_c_type(type_text: str, parameter: bool = False) -> Tuple[str, Set[str]]:
    normalized = " ".join(type_text.replace("\n", " ").split())
    imports: Set[str] = set()
    lowered = normalized.lower()
    if not normalized or lowered == "void":
        return ("()", imports)
    struct_match = re.search(r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)", normalized)
    if struct_match:
        rust_name = _rust_type_name(struct_match.group(1))
        if "*" in normalized and parameter:
            return (f"&{rust_name}" if "const" in lowered else f"&mut {rust_name}", imports)
        return (rust_name, imports)
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


def _translate_expr(value: Any) -> str:
    if value is None:
        return "()"
    expression = str(value).strip()
    expression = expression.replace("->", ".").replace("NULL", "std::ptr::null()")
    expression = expression.replace("&&", "&&").replace("||", "||")
    return expression


def _binary_expr(body_value: Dict[str, Any], rust_return: str) -> str:
    operator = body_value["operator"]
    expression = f"{_translate_expr(body_value['left'])} {operator} {_translate_expr(body_value['right'])}"
    if operator in {"==", "!=", "<=", ">=", "<", ">", "&&", "||"} and rust_return != "bool":
        return f"if {expression} {{ 1 }} else {{ 0 }}"
    return expression


def _render_body(function: Dict[str, Any], rust_return: str) -> List[str]:
    body_kind = function.get("body_kind", "")
    body_value = function.get("body_value")
    if body_kind == "empty":
        return []
    if body_kind == "return_number":
        return [str(body_value)]
    if body_kind == "return_null":
        return ["std::ptr::null()"]
    if body_kind in {"return_identifier", "return_field"}:
        return [_translate_expr(body_value)]
    if body_kind == "return_binary_expr":
        return [_binary_expr(body_value, rust_return)]
    if body_kind in {"assignment_then_return", "state_mutation_then_return"}:
        lines = []
        for assignment in body_value.get("assignments", []):
            lines.append(
                f"{_translate_expr(assignment['target'])} {assignment['operator']} {_translate_expr(assignment['value'])};"
            )
        return_expr = body_value.get("return_expr")
        if return_expr is not None and rust_return != "()":
            lines.append(_translate_expr(return_expr))
        return lines
    raise ValueError(f"unsupported body kind: {body_kind}")


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
    translated = function.get("decl_kind") == "definition" and function.get("translation_status") == "translated"
    if not translated:
        return ("", imports, False)
    body_value = function.get("body_value")
    assignments = body_value.get("assignments", []) if isinstance(body_value, dict) else []
    param_parts: List[str] = []
    for param in function.get("params", []):
        rust_type, rust_imports = _map_c_type(param.get("type", ""), parameter=True)
        imports.update(rust_imports)
        param_name = _sanitize_ident(param.get("name", "arg"), "arg")
        if any(
            assignment.get("target") == param.get("name")
            for assignment in assignments
        ):
            param_name = f"mut {param_name}"
        param_parts.append(f"{param_name}: {rust_type}")
    rust_return, rust_imports = _map_c_type(function.get("return_type", ""))
    imports.update(rust_imports)
    signature = f"pub fn {function['name']}({', '.join(param_parts)})"
    if rust_return != "()":
        signature += f" -> {rust_return}"
    lines = [signature + " {"]
    lines.append(f"    // Derived from {function['file']}")
    lines.extend(f"    {line}" for line in _render_body(function, rust_return))
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
        chunks.append(f"pub struct {_rust_type_name(ident)} {{")
        fields = type_entry.get("fields", [])
        for field in fields:
            field_type, field_imports = _map_c_type(field.get("type", ""))
            imports.update(field_imports)
            if field.get("array_length"):
                field_type = f"[{field_type}; {field['array_length']}]"
            chunks.append(f"    pub {_sanitize_ident(field['name'], 'field')}: {field_type},")
        if not fields:
            chunks.append("    pub _opaque: usize,")
        chunks.append("}")
        chunks.append("")

    for function in functions:
        rendered, function_imports, translated = _render_function(function)
        imports.update(function_imports)
        if translated:
            translated_count += 1
        if rendered:
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
    mapped_functions: List[Tuple[Dict[str, Any], str]],
) -> Tuple[str, List[Dict[str, Any]]]:
    test_mapping: List[Dict[str, Any]] = []
    direct_functions = [function["name"] for function, _ in mapped_functions]
    lines: List[str] = []
    if direct_functions:
        lines.append(f"use {crate_name}::{{{', '.join(direct_functions)}}};")
        lines.append("")

    mapped_by_name = {function["name"]: (function, module_name) for function, module_name in mapped_functions}
    exercised: Set[str] = set()

    for index, test_case in enumerate(analysis.get("tests", []), start=1):
        test_name = _sanitize_ident(test_case["test_names"][0], f"source_test_{index}")
        referenced = test_case.get("referenced_apis", [])
        selected = [mapped_by_name[name] for name in referenced if name in mapped_by_name]
        has_source_evidence = bool(referenced) and bool(test_case.get("assertions"))
        rendered, called = _render_api_exercises(crate_name, selected)
        if rendered:
            lines.append("#[test]")
            lines.append(f"fn {test_name}() {{")
            lines.extend(f"    {line}" for line in rendered)
            lines.append("}")
            lines.append("")
        exercised.update(called)
        unsupported_references = [name for name in referenced if name not in mapped_by_name]
        if not has_source_evidence:
            coverage_level = "structural_only"
        elif unsupported_references:
            coverage_level = "partial_semantic"
        else:
            coverage_level = "semantic_mapped"
        test_mapping.append(
            {
                "source_test": test_case["file"],
                "rust_test_file": "tests/source_migration.rs",
                "mapping": "source API calls with translated assertions" if rendered else "source structure only",
                "coverage_level": coverage_level,
                "mapped_apis": called,
                "unsupported_apis": unsupported_references,
                "source_assertion_count": len(test_case.get("assertions", [])),
            }
        )

    remaining = [(function, module_name) for function, module_name in mapped_functions if function["name"] not in exercised]
    if remaining:
        lines.extend(["#[test]", "fn translated_api_evidence() {"])
        rendered, called = _render_api_exercises(crate_name, remaining)
        lines.extend(f"    {line}" for line in rendered)
        lines.extend(["}", ""])
        exercised.update(called)

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


def _argument_for_param(
    crate_name: str,
    module_name: str,
    param: Dict[str, Any],
    variables: Dict[Tuple[str, str], str],
    setup: List[str],
) -> str:
    type_text = param.get("type", "")
    rust_type, _ = _map_c_type(type_text, parameter=True)
    param_name = _sanitize_ident(param.get("name", "arg"), "arg")
    if rust_type.startswith("&"):
        base_type = rust_type.replace("&mut ", "").replace("&", "")
        key = (param_name, base_type)
        variable = variables.get(key)
        if variable is None:
            variable = f"{param_name}_{len(variables)}"
            variables[key] = variable
            setup.append(f"let mut {variable} = {crate_name}::{module_name}::{base_type}::default();")
        return f"&mut {variable}" if rust_type.startswith("&mut") else f"&{variable}"
    if rust_type.startswith("*const") or rust_type.startswith("*mut"):
        return "std::ptr::null()" if rust_type.startswith("*const") else "std::ptr::null_mut()"
    if rust_type == "bool":
        return "false"
    return "1"


def _render_api_exercises(
    crate_name: str,
    functions: List[Tuple[Dict[str, Any], str]],
) -> Tuple[List[str], List[str]]:
    lines: List[str] = []
    variables: Dict[Tuple[str, str], str] = {}
    called: List[str] = []
    for function, module_name in functions:
        setup: List[str] = []
        args = [
            _argument_for_param(crate_name, module_name, param, variables, setup)
            for param in function.get("params", [])
        ]
        lines.extend(setup)
        call = f"{function['name']}({', '.join(args)})"
        kind = function.get("body_kind")
        value = function.get("body_value")
        if kind == "return_number":
            lines.append(f"assert_eq!({call}, {value});")
        elif kind == "return_null":
            lines.append(f"assert!({call}.is_null());")
        elif kind == "return_identifier":
            param_index = next((i for i, item in enumerate(function.get("params", [])) if item.get("name") == value), None)
            expected = args[param_index] if param_index is not None else _translate_expr(value)
            lines.append(f"assert_eq!({call}, {expected});")
        elif kind in {"return_field", "return_binary_expr"}:
            expected = _expected_expr(value, function, args)
            if kind == "return_binary_expr":
                rust_return, _ = _map_c_type(function.get("return_type", ""))
                expected = _binary_expr(
                    {"left": _expected_expr(value["left"], function, args), "operator": value["operator"], "right": _expected_expr(value["right"], function, args)},
                    rust_return,
                )
            lines.append(f"assert_eq!({call}, {expected});")
        elif kind in {"assignment_then_return", "state_mutation_then_return"}:
            if value.get("return_expr") is None:
                lines.append(f"assert_eq!({call}, ());")
            else:
                expected = _expected_assignment_return(value, function, args)
                lines.append(f"assert_eq!({call}, {expected});")
            for assignment in value.get("assignments", []) if kind == "state_mutation_then_return" else []:
                target = _expected_expr(assignment["target"], function, args)
                expected = _expected_expr(assignment["value"], function, args)
                lines.append(f"assert_eq!({target}, {expected});")
        else:
            lines.append(f"assert_eq!({call}, ());")
        called.append(function["name"])
    return (lines, called)


def _expected_expr(value: Any, function: Dict[str, Any], args: List[str]) -> str:
    if isinstance(value, dict):
        left = _expected_expr(value["left"], function, args)
        right = _expected_expr(value["right"], function, args)
        return f"{left} {value['operator']} {right}"
    expression = _translate_expr(value)
    for index, param in enumerate(function.get("params", [])):
        name = re.escape(param.get("name", ""))
        replacement = args[index].replace("&mut ", "").replace("&", "")
        expression = re.sub(rf"\b{name}\b", replacement, expression)
    return expression


def _expected_assignment_return(body_value: Dict[str, Any], function: Dict[str, Any], args: List[str]) -> str:
    expression = _expected_expr(body_value.get("return_expr"), function, args)
    for assignment in reversed(body_value.get("assignments", [])):
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", assignment["target"]):
            replacement = _expected_expr(assignment["value"], function, args)
            expression = re.sub(rf"\b{re.escape(assignment['target'])}\b", replacement, expression)
    return expression


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
    mapped_functions: List[Tuple[Dict[str, Any], str]] = []

    for module_name in module_names:
        module_functions = grouped.get(module_name, [])
        module_rs, _imports, translated_count = _render_module(module_name, module_functions, macros, types)
        translated_functions += translated_count
        _write(project_dir / "src" / f"{module_name}.rs", module_rs)
        for function in module_functions:
            if function.get("translation_status") != "translated" or function.get("decl_kind") != "definition":
                continue
            if function.get("name") not in [name for name, _ in exported_functions]:
                exported_functions.append((function["name"], module_name))
                mapped_functions.append((function, module_name))

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

    source_tests_have_evidence = bool(analysis.get("tests")) and all(
        test.get("referenced_apis") and test.get("assertions") for test in analysis.get("tests", [])
    )
    claimable = (
        bool(exported_functions)
        and total_definitions > 0
        and translated_functions == total_definitions
        and source_tests_have_evidence
        and all(name in [item[0] for item in exported_functions] for name in analysis.get("public_apis", []))
        and all(
            set(test.get("referenced_apis", [])).issubset({item[0] for item in exported_functions})
            for test in analysis.get("tests", [])
        )
    )
    tests_rs, test_mapping = _render_tests(
        _sanitize_ident(packet.output_project_name, "c_to_rust_output"),
        analysis,
        mapped_functions,
    )
    _write(project_dir / "tests" / "source_migration.rs", tests_rs)

    mapped_names = [item[0] for item in exported_functions]
    unsupported_apis = [name for name in analysis.get("public_apis", []) if name not in mapped_names]
    unsupported_reasons = {
        name: next(
            (
                item.get("unsupported_reason") or "no translatable function definition was found"
                for item in analysis.get("functions", [])
                if item.get("name") == name and item.get("decl_kind") == "definition"
            ),
            "no function definition was found in the analyzed source files",
        )
        for name in unsupported_apis
    }
    module_list = ["src/lib.rs"] + [f"src/{module_name}.rs" for module_name in module_names] + ["tests/source_migration.rs"]
    source_coverage = {
        "source_file_count": len(analysis.get("source_files", [])),
        "test_file_count": len(analysis.get("tests", [])),
        "mapped_api_count": len(exported_functions),
        "unsupported_api_count": len(unsupported_apis),
        "translated_definition_count": translated_functions,
        "definition_count": total_definitions,
        "unsupported_reasons": unsupported_reasons,
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
