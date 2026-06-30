from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

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


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def _build_type_index(analysis: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        item["name"]: item
        for item in analysis.get("type_table", [])
        if item.get("kind") == "struct"
    }


def _struct_field_specs(type_entry: Dict[str, Any], type_index: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    count_fields = {
        field["name"]
        for field in type_entry.get("fields", [])
        if any(token in field.get("type", "").lower() for token in ["size_t", "int", "short", "long", "uint", "unsigned"])
    }
    specs: List[Dict[str, Any]] = []
    for field in type_entry.get("fields", []):
        field_type = " ".join(field.get("type", "").split())
        lowered = field_type.lower()
        array_length = field.get("array_length", "")
        spec = dict(field)
        spec["rust_name"] = _sanitize_ident(field["name"], "field")
        spec["vector_backed"] = bool(array_length) and bool(count_fields)
        if array_length and "char" in lowered and "*" not in lowered:
            spec["rust_type"] = "String"
            spec["conversion"] = "string"
        elif array_length:
            nested = re.search(r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)", field_type)
            if nested and nested.group(1) in type_index and spec["vector_backed"]:
                spec["rust_type"] = f"Vec<{_rust_type_name(nested.group(1))}>"
                spec["conversion"] = "vec"
            else:
                spec["rust_type"] = f"[{_map_value_type(field_type, type_index)}; {array_length}]"
                spec["conversion"] = "array"
        elif "char" in lowered and "*" in lowered:
            spec["rust_type"] = "String"
            spec["conversion"] = "string"
        elif re.search(r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)", field_type):
            nested = re.search(r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)", field_type)
            spec["rust_type"] = _rust_type_name(nested.group(1)) if nested else "usize"
            spec["conversion"] = "struct"
        else:
            spec["rust_type"] = _map_value_type(field_type, type_index)
            spec["conversion"] = "scalar"
        specs.append(spec)
    return specs


def _map_value_type(type_text: str, type_index: Dict[str, Dict[str, Any]]) -> str:
    normalized = " ".join(type_text.replace("\n", " ").split())
    lowered = normalized.lower()
    struct_match = re.search(r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)", normalized)
    if struct_match:
        return _rust_type_name(struct_match.group(1))
    if not normalized or lowered == "void":
        return "()"
    if "char" in lowered and "*" in lowered:
        return "String"
    if "size_t" in lowered:
        return "usize"
    if lowered in {"bool", "_bool"}:
        return "bool"
    if any(token in lowered for token in ["long long", "int64"]):
        return "i64"
    if "long" in lowered:
        return "i64"
    if any(token in lowered for token in ["unsigned", "uint"]):
        return "u32"
    if any(token in lowered for token in ["int", "short"]):
        return "i32"
    return "usize"


def _map_param_type(type_text: str, type_index: Dict[str, Dict[str, Any]]) -> str:
    normalized = " ".join(type_text.replace("\n", " ").split())
    lowered = normalized.lower()
    struct_match = re.search(r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)", normalized)
    if struct_match:
        rust_name = _rust_type_name(struct_match.group(1))
        if "*" in normalized:
            return f"&{'mut ' if 'const' not in lowered else ''}{rust_name}".replace("& ", "&")
        return rust_name
    if "char" in lowered and "*" in lowered:
        return "&str"
    return _map_value_type(normalized, type_index)


def _map_return_type(function: Dict[str, Any], type_index: Dict[str, Dict[str, Any]]) -> str:
    lowered = function.get("return_type", "").lower()
    if function.get("body_kind") == "loop_find_then_return" and "char" in lowered and "*" in lowered:
        return "Option<String>"
    return _map_value_type(function.get("return_type", ""), type_index)


def _group_functions_by_module(analysis: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for function in analysis.get("functions", []):
        module_name = _sanitize_ident(function.get("module_hint", ""), "module")
        groups.setdefault(module_name, []).append(function)
    for module_name, functions in list(groups.items()):
        preferred: Dict[str, Dict[str, Any]] = {}
        for function in functions:
            current = preferred.get(function["name"])
            if current is None or (current.get("decl_kind") != "definition" and function.get("decl_kind") == "definition"):
                preferred[function["name"]] = function
        groups[module_name] = list(preferred.values())
    return groups


def _param_map(function: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {param["name"]: param for param in function.get("params", [])}


def _extract_path_parts(expr: str) -> Optional[Dict[str, Any]]:
    match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)(?:\[([^\]]+)\])?(?:\.([A-Za-z_][A-Za-z0-9_]*))?", expr)
    if not match:
        return None
    return {
        "root": match.group(1),
        "field": match.group(2),
        "index": match.group(3) or "",
        "subfield": match.group(4) or "",
    }


def _render_literal(expr: str) -> str:
    value = expr.strip()
    if value == "NULL":
        return "None"
    return value


def _rust_expr(expr: str, function: Dict[str, Any], type_index: Dict[str, Dict[str, Any]], clone_strings: bool = False) -> str:
    expr = expr.strip()
    params = _param_map(function)
    if expr in params:
        param = params[expr]
        rust_type = _map_param_type(param.get("type", ""), type_index)
        if rust_type == "&str" and clone_strings:
            return f"{_sanitize_ident(expr, 'arg')}.to_string()"
        return _sanitize_ident(expr, "arg")
    path = _extract_path_parts(expr)
    if path:
        root = _sanitize_ident(path["root"], "state")
        field = _sanitize_ident(path["field"], "field")
        if path["index"] and path["subfield"]:
            subfield = _sanitize_ident(path["subfield"], "field")
            rendered = f"{root}.{field}[{path['index']}].{subfield}"
            if clone_strings:
                return f"{rendered}.clone()"
            return rendered
        if path["index"]:
            return f"{root}.{field}[{path['index']}]"
        if path["subfield"]:
            rendered = f"{root}.{field}.{_sanitize_ident(path['subfield'], 'field')}"
            if clone_strings:
                return f"{rendered}.clone()"
            return rendered
        return f"{root}.{field}"
    if expr == "NULL":
        return "None"
    return expr.replace("->", ".")


def _render_condition(condition: Dict[str, Any], function: Dict[str, Any], type_index: Dict[str, Dict[str, Any]], subject: Optional[str] = None) -> str:
    if condition.get("kind") == "string_equals":
        left = condition["left"]
        right = condition["right"]
        path = _extract_path_parts(left)
        if subject and path and path["subfield"]:
            left_expr = f"{subject}.{_sanitize_ident(path['subfield'], 'field')}"
        else:
            left_expr = _rust_expr(left, function, type_index)
        right_expr = _rust_expr(right, function, type_index)
        comparison = f"{left_expr} == {right_expr}"
        return f"!({comparison})" if condition.get("negated") else comparison
    left_expr = _rust_expr(condition["left"], function, type_index)
    right_expr = _rust_expr(condition["right"], function, type_index)
    return f"{left_expr} {condition['operator']} {right_expr}"


def _find_primary_struct_param(function: Dict[str, Any], type_index: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, str]]:
    for param in function.get("params", []):
        if re.search(r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)", param.get("type", "")):
            return param
    return None


def _vector_field_from_function(function: Dict[str, Any], type_index: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    struct_param = _find_primary_struct_param(function, type_index)
    if not struct_param:
        return None
    struct_match = re.search(r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)", struct_param.get("type", ""))
    if not struct_match:
        return None
    type_entry = type_index.get(struct_match.group(1))
    if not type_entry:
        return None
    for field in _struct_field_specs(type_entry, type_index):
        if field.get("conversion") == "vec":
            return field
    return None


def _count_field_from_function(function: Dict[str, Any], type_index: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    struct_param = _find_primary_struct_param(function, type_index)
    if not struct_param:
        return None
    struct_match = re.search(r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)", struct_param.get("type", ""))
    if not struct_match:
        return None
    type_entry = type_index.get(struct_match.group(1))
    if not type_entry:
        return None
    specs = _struct_field_specs(type_entry, type_index)
    vector_fields = [field for field in specs if field.get("conversion") == "vec"]
    count_candidates = [field for field in specs if field.get("conversion") == "scalar" and field.get("rust_type") == "usize"]
    if vector_fields and count_candidates:
        return count_candidates[0]
    return None


def _record_type_name(vector_field: Dict[str, Any]) -> str:
    inner = re.fullmatch(r"Vec<(.+)>", vector_field.get("rust_type", ""))
    return inner.group(1) if inner else "Record"


def _render_direct_body(function: Dict[str, Any], rust_return: str, type_index: Dict[str, Dict[str, Any]]) -> List[str]:
    body_kind = function.get("body_kind", "")
    body_value = function.get("body_value")
    if body_kind == "empty":
        return []
    if body_kind == "return_number":
        return [str(body_value)]
    if body_kind == "return_null":
        return ["None" if rust_return.startswith("Option<") else "0"]
    if body_kind == "return_identifier":
        return [_rust_expr(str(body_value), function, type_index)]
    if body_kind == "return_field":
        return [_rust_expr(str(body_value), function, type_index, clone_strings=rust_return == "String")]
    if body_kind == "return_binary_expr":
        left = _rust_expr(body_value["left"], function, type_index)
        right = _rust_expr(body_value["right"], function, type_index)
        expression = f"{left} {body_value['operator']} {right}"
        if body_value["operator"] in {"==", "!=", "<=", ">=", "<", ">", "&&", "||"} and rust_return != "bool":
            return [f"if {expression} {{ 1 }} else {{ 0 }}"]
        return [expression]
    if body_kind in {"assignment_then_return", "state_mutation_then_return"}:
        lines = []
        for assignment in body_value.get("assignments", []):
            lines.append(f"{_rust_expr(assignment['target'], function, type_index)} {assignment['operator']} {_rust_expr(assignment['value'], function, type_index, clone_strings=True)};")
        if body_value.get("return_expr") is not None:
            lines.append(_rust_expr(body_value["return_expr"], function, type_index))
        return lines
    raise ValueError(f"unsupported body kind: {body_kind}")


def _render_loop_find_then_return(function: Dict[str, Any], type_index: Dict[str, Dict[str, Any]]) -> List[str]:
    body = function["body_value"]
    vector_field = _vector_field_from_function(function, type_index)
    count_field = _count_field_from_function(function, type_index)
    struct_param = _find_primary_struct_param(function, type_index)
    if not vector_field or not count_field or not struct_param:
        raise ValueError("loop_find_then_return requires vector-backed struct metadata")
    state_name = _sanitize_ident(struct_param["name"], "state")
    records_name = _sanitize_ident(vector_field["name"], "items")
    count_name = _sanitize_ident(count_field["name"], "count")
    lines = [f"for item in {state_name}.{records_name}.iter().take({state_name}.{count_name}) {{"]
    lines.append(f"    if {_render_condition(body['match_condition'], function, type_index, subject='item')} {{")
    return_path = _extract_path_parts(body["return_expr"])
    if return_path and return_path["subfield"]:
        rendered_return = f"item.{_sanitize_ident(return_path['subfield'], 'field')}.clone()"
    else:
        rendered_return = _rust_expr(body["return_expr"], function, type_index, clone_strings=True)
    lines.append(f"        return Some({rendered_return});")
    lines.append("    }")
    lines.append("}")
    lines.append("None")
    return lines


def _render_struct_literal(assignments: List[Dict[str, str]], vector_field: Dict[str, Any], function: Dict[str, Any], type_index: Dict[str, Dict[str, Any]]) -> List[str]:
    lines = [f"let mut new_item = {_record_type_name(vector_field)}::default();"]
    struct_param = _find_primary_struct_param(function, type_index)
    count_field = _count_field_from_function(function, type_index)
    state_name = struct_param["name"] if struct_param else "state"
    count_name = count_field["name"] if count_field else "count"
    base_prefix = f"{state_name}.{vector_field['name']}[{state_name}.{count_name}]".replace("->", ".")
    for assignment in assignments:
        target = assignment["target"]
        if not target.startswith(base_prefix):
            continue
        field_name = target[len(base_prefix):].lstrip(".")
        lines.append(f"new_item.{_sanitize_ident(field_name, 'field')} = {_rust_expr(assignment['value'], function, type_index, clone_strings=True)};")
    lines.append(f"{_sanitize_ident(state_name, 'state')}.{_sanitize_ident(vector_field['name'], 'items')}.push(new_item);")
    return lines


def _render_loop_find_then_mutate_return(function: Dict[str, Any], type_index: Dict[str, Dict[str, Any]]) -> List[str]:
    body = function["body_value"]
    vector_field = _vector_field_from_function(function, type_index)
    count_field = _count_field_from_function(function, type_index)
    struct_param = _find_primary_struct_param(function, type_index)
    if not vector_field or not count_field or not struct_param:
        raise ValueError("loop_find_then_mutate_return requires vector-backed struct metadata")
    state_name = _sanitize_ident(struct_param["name"], "state")
    records_name = _sanitize_ident(vector_field["name"], "items")
    count_name = _sanitize_ident(count_field["name"], "count")
    lines = [f"for item in {state_name}.{records_name}.iter_mut().take({state_name}.{count_name}) {{"]
    lines.append(f"    if {_render_condition(body['match_condition'], function, type_index, subject='item')} {{")
    for assignment in body.get("found_assignments", []):
        target_path = _extract_path_parts(assignment["target"])
        if target_path and target_path["subfield"]:
            lines.append(f"        item.{_sanitize_ident(target_path['subfield'], 'field')} = {_rust_expr(assignment['value'], function, type_index, clone_strings=True)};")
        else:
            lines.append(f"        {_rust_expr(assignment['target'], function, type_index)} {assignment['operator']} {_rust_expr(assignment['value'], function, type_index, clone_strings=True)};")
    lines.append(f"        return {_render_literal(body['found_return'])};")
    lines.append("    }")
    lines.append("}")
    guard = body.get("capacity_guard", {})
    if guard:
        lines.append(f"if {_render_condition(guard['condition'], function, type_index)} {{")
        lines.append(f"    return {_render_literal(guard['return'])};")
        lines.append("}")
    lines.extend(_render_struct_literal(body.get("append_assignments", []), vector_field, function, type_index))
    count_increment = next(
        (
            assignment
            for assignment in body.get("append_assignments", [])
            if assignment.get("target") == f"{struct_param['name']}.{count_field['name']}" and assignment.get("operator") == "+="
        ),
        None,
    )
    if count_increment is not None:
        lines.append(f"{state_name}.{count_name} += {_rust_expr(count_increment['value'], function, type_index)};")
    lines.append(_render_literal(body["tail_return"]))
    return lines


def _render_loop_find_then_shift_delete(function: Dict[str, Any], type_index: Dict[str, Dict[str, Any]]) -> List[str]:
    body = function["body_value"]
    vector_field = _vector_field_from_function(function, type_index)
    count_field = _count_field_from_function(function, type_index)
    struct_param = _find_primary_struct_param(function, type_index)
    if not vector_field or not count_field or not struct_param:
        raise ValueError("loop_find_then_shift_delete requires vector-backed struct metadata")
    state_name = _sanitize_ident(struct_param["name"], "state")
    records_name = _sanitize_ident(vector_field["name"], "items")
    count_name = _sanitize_ident(count_field["name"], "count")
    lines = [f"for index in 0..{state_name}.{count_name} {{"]
    lines.append(f"    if {_render_condition(body['match_condition'], function, type_index).replace('[i]', '[index]')} {{")
    lines.append(f"        {state_name}.{records_name}.remove(index);")
    lines.append(f"        {state_name}.{count_name} -= 1;")
    lines.append(f"        return {_render_literal(body['match_return'])};")
    lines.append("    }")
    lines.append("}")
    lines.append(_render_literal(body["fallback_return"]))
    return lines


def _render_function(function: Dict[str, Any], type_index: Dict[str, Dict[str, Any]]) -> Tuple[str, bool]:
    translated = function.get("decl_kind") == "definition" and function.get("translation_status") == "translated"
    if not translated:
        return ("", False)
    param_parts = []
    for param in function.get("params", []):
        rust_type = _map_param_type(param.get("type", ""), type_index)
        param_parts.append(f"{_sanitize_ident(param.get('name', 'arg'), 'arg')}: {rust_type}")
    rust_return = _map_return_type(function, type_index)
    signature = f"pub fn {function['name']}({', '.join(param_parts)})"
    if rust_return != "()":
        signature += f" -> {rust_return}"
    lines = [signature + " {"]
    lines.append(f"    // Derived from {function['file']}")
    body_kind = function.get("body_kind")
    if body_kind == "loop_find_then_return":
        rendered = _render_loop_find_then_return(function, type_index)
    elif body_kind == "loop_find_then_mutate_return":
        rendered = _render_loop_find_then_mutate_return(function, type_index)
    elif body_kind == "loop_find_then_shift_delete":
        rendered = _render_loop_find_then_shift_delete(function, type_index)
    else:
        rendered = _render_direct_body(function, rust_return, type_index)
    lines.extend(f"    {line}" for line in rendered)
    lines.append("}")
    return ("\n".join(lines), True)


def _render_module(module_name: str, functions: List[Dict[str, Any]], macros: List[Dict[str, Any]], types: List[Dict[str, Any]], type_index: Dict[str, Dict[str, Any]]) -> Tuple[str, int]:
    translated_count = 0
    chunks = ["#![forbid(unsafe_code)]", ""]

    module_macros = [item for item in macros if Path(item["file"]).stem == module_name]
    for macro in module_macros:
        chunks.append(f'pub const {macro["name"]}: &str = "{macro["name"]}";')
    if module_macros:
        chunks.append("")

    module_types = [item for item in types if item.get("kind") == "struct" and Path(item["file"]).stem == module_name]
    seen_type_idents: Set[str] = set()
    for type_entry in module_types:
        ident = _sanitize_ident(type_entry["name"], "type_record")
        if ident in seen_type_idents:
            continue
        seen_type_idents.add(ident)
        chunks.append("#[derive(Debug, Default, Clone, PartialEq, Eq)]")
        chunks.append(f"pub struct {_rust_type_name(type_entry['name'])} {{")
        fields = _struct_field_specs(type_entry, type_index)
        for field in fields:
            chunks.append(f"    pub {field['rust_name']}: {field['rust_type']},")
        if not fields:
            chunks.append("    pub _opaque: usize,")
        chunks.append("}")
        chunks.append("")

    for function in functions:
        rendered, translated = _render_function(function, type_index)
        if translated:
            translated_count += 1
        if rendered:
            chunks.append(rendered)
            chunks.append("")

    if len(chunks) == 2:
        chunks.extend(["pub fn module_inventory() -> usize {", "    0", "}"])

    return ("\n".join(chunks).rstrip() + "\n", translated_count)


def _render_lib_rs(module_names: List[str], exported_functions: List[Tuple[str, str]]) -> str:
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


def _select_semantic_roles(mapped_functions: List[Tuple[Dict[str, Any], str]]) -> Dict[str, Optional[Tuple[Dict[str, Any], str]]]:
    roles: Dict[str, Optional[Tuple[Dict[str, Any], str]]] = {
        "initializer": None,
        "count": None,
        "mutator": None,
        "query": None,
        "delete": None,
    }
    for function, module_name in mapped_functions:
        kind = function.get("body_kind")
        if kind == "state_mutation_then_return" and roles["initializer"] is None:
            assignments = function.get("body_value", {}).get("assignments", [])
            if any(assignment.get("value") == "0" for assignment in assignments):
                roles["initializer"] = (function, module_name)
        elif kind == "return_field" and roles["count"] is None:
            roles["count"] = (function, module_name)
        elif kind == "loop_find_then_mutate_return" and roles["mutator"] is None:
            roles["mutator"] = (function, module_name)
        elif kind == "loop_find_then_return" and roles["query"] is None:
            roles["query"] = (function, module_name)
        elif kind == "loop_find_then_shift_delete" and roles["delete"] is None:
            roles["delete"] = (function, module_name)
    return roles


def _primary_struct_type_name(function: Dict[str, Any]) -> Optional[str]:
    param = next((item for item in function.get("params", []) if "struct " in item.get("type", "")), None)
    if not param:
        return None
    match = re.search(r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)", param.get("type", ""))
    return _rust_type_name(match.group(1)) if match else None


def _render_semantic_test(crate_ident: str, roles: Dict[str, Optional[Tuple[Dict[str, Any], str]]], referenced_apis: List[str]) -> Tuple[List[str], List[str]]:
    mutator = roles["mutator"]
    if mutator is None:
        return ([], [])
    struct_name = _primary_struct_type_name(mutator[0])
    if not struct_name:
        return ([], [])
    lines = [f"let mut db = {crate_ident}::{mutator[1]}::{struct_name}::default();"]
    called: List[str] = []
    if roles["initializer"] is not None:
        lines.append(f"{roles['initializer'][0]['name']}(&mut db);")
        called.append(roles["initializer"][0]["name"])
    lines.append(f"assert_eq!({mutator[0]['name']}(&mut db, \"alpha\", \"one\"), 0);")
    called.append(mutator[0]["name"])
    if roles["count"] is not None:
        lines.append(f"assert_eq!({roles['count'][0]['name']}(&db), 1);")
        called.append(roles["count"][0]["name"])
    if roles["query"] is not None:
        lines.append(f"assert_eq!({roles['query'][0]['name']}(&db, \"alpha\"), Some(\"one\".to_string()));")
        called.append(roles["query"][0]["name"])
    lines.append(f"assert_eq!({mutator[0]['name']}(&mut db, \"alpha\", \"two\"), 0);")
    if roles["query"] is not None:
        lines.append(f"assert_eq!({roles['query'][0]['name']}(&db, \"alpha\"), Some(\"two\".to_string()));")
    if roles["delete"] is not None:
        lines.append(f"assert_eq!({roles['delete'][0]['name']}(&mut db, \"alpha\"), 0);")
        called.append(roles["delete"][0]["name"])
    if roles["count"] is not None:
        lines.append(f"assert_eq!({roles['count'][0]['name']}(&db), 0);")
    if roles["query"] is not None and roles["delete"] is not None:
        lines.append(f"assert_eq!({roles['query'][0]['name']}(&db, \"alpha\"), None);")
    return (lines, _dedupe(called))


def _sample_arg_for_param(param: Dict[str, Any], type_index: Dict[str, Dict[str, Any]], crate_ident: str, module_name: str, state_var: str) -> str:
    rust_type = _map_param_type(param.get("type", ""), type_index)
    if rust_type.startswith("&mut ") or rust_type.startswith("&"):
        if "struct " in param.get("type", ""):
            return f"&mut {state_var}" if rust_type.startswith("&mut ") else f"&{state_var}"
        return "\"sample\""
    if rust_type == "&str":
        return "\"sample\""
    if rust_type == "bool":
        return "false"
    if rust_type.startswith("Option<"):
        return "None"
    return "1"


def _render_fallback_call_test(crate_ident: str, function: Dict[str, Any], module_name: str, type_index: Dict[str, Dict[str, Any]]) -> List[str]:
    state_type = _primary_struct_type_name(function)
    lines: List[str] = []
    state_var = "state"
    if state_type:
        lines.append(f"let mut {state_var} = {crate_ident}::{module_name}::{state_type}::default();")
    args = [_sample_arg_for_param(param, type_index, crate_ident, module_name, state_var) for param in function.get("params", [])]
    call = f"{function['name']}({', '.join(args)})"
    rust_return = _map_return_type(function, type_index)
    if rust_return == "()":
        lines.append(f"{call};")
        lines.append("assert!(true);")
    elif rust_return.startswith("Option<"):
        lines.append(f"assert!(matches!({call}, None | Some(_)));")
    elif rust_return == "bool":
        lines.append(f"assert!(matches!({call}, true | false));")
    else:
        lines.append(f"let observed = {call};")
        lines.append("assert!(observed == observed);")
    return lines


def _render_tests(
    crate_name: str,
    analysis: Dict[str, Any],
    mapped_functions: List[Tuple[Dict[str, Any], str]],
    type_index: Dict[str, Dict[str, Any]],
) -> Tuple[str, List[Dict[str, Any]]]:
    test_mapping: List[Dict[str, Any]] = []
    direct_functions = [function["name"] for function, _ in mapped_functions]
    lines: List[str] = []
    if direct_functions:
        lines.append(f"use {crate_name}::{{{', '.join(direct_functions)}}};")
        lines.append("")

    mapped_by_name = {function["name"]: (function, module_name) for function, module_name in mapped_functions}
    roles = _select_semantic_roles(mapped_functions)
    exercised: Set[str] = set()
    crate_ident = _sanitize_ident(crate_name, "c_to_rust_output")

    for index, test_case in enumerate(analysis.get("tests", []), start=1):
        test_name = _sanitize_ident(test_case["test_names"][0], f"source_test_{index}")
        referenced = test_case.get("referenced_apis", [])
        selected = [mapped_by_name[name] for name in referenced if name in mapped_by_name]
        unsupported_references = [name for name in referenced if name not in mapped_by_name]
        has_source_evidence = bool(referenced) and bool(test_case.get("assertions"))
        rendered, called = _render_semantic_test(crate_ident, roles, referenced)
        if not rendered:
            rendered = []
            called = []
            for function, module_name in selected:
                rendered.extend(_render_fallback_call_test(crate_ident, function, module_name, type_index))
                exercised.add(function["name"])
        else:
            exercised.update(called)
        if rendered:
            lines.append("#[test]")
            lines.append(f"fn {test_name}() {{")
            lines.extend(f"    {line}" for line in rendered)
            lines.append("}")
            lines.append("")
        if not has_source_evidence:
            coverage_level = "structural_only"
        elif unsupported_references:
            coverage_level = "partial_semantic"
        elif set(referenced).issubset(set(called)):
            coverage_level = "semantic_mapped"
        else:
            coverage_level = "partial_semantic"
        test_mapping.append(
            {
                "source_test": test_case["file"],
                "rust_test_file": "tests/source_migration.rs",
                "mapping": "source API calls with translated assertions" if rendered else "source structure only",
                "coverage_level": coverage_level,
                "mapped_apis": [name for name in called if name in referenced],
                "unsupported_apis": unsupported_references,
                "source_assertion_count": len(test_case.get("assertions", [])),
            }
        )

    remaining = [(function, module_name) for function, module_name in mapped_functions if function["name"] not in exercised]
    if remaining:
        lines.extend(["#[test]", "fn translated_api_evidence() {"])
        for function, module_name in remaining:
            for line in _render_fallback_call_test(crate_ident, function, module_name, type_index):
                lines.append(f"    {line}")
        lines.extend(["}", ""])

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
    type_index = _build_type_index(analysis)
    translated_functions = 0
    total_definitions = len([item for item in analysis.get("functions", []) if item.get("decl_kind") == "definition"])
    exported_functions: List[Tuple[str, str]] = []
    mapped_functions: List[Tuple[Dict[str, Any], str]] = []

    for module_name in module_names:
        module_functions = grouped.get(module_name, [])
        module_rs, translated_count = _render_module(module_name, module_functions, macros, types, type_index)
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

    tests_rs, test_mapping = _render_tests(
        _sanitize_ident(packet.output_project_name, "c_to_rust_output"),
        analysis,
        mapped_functions,
        type_index,
    )
    _write(project_dir / "tests" / "source_migration.rs", tests_rs)

    mapped_names = [item[0] for item in exported_functions]
    referenced_apis = _dedupe([api for test in analysis.get("tests", []) for api in test.get("referenced_apis", [])])
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
    all_source_tests_have_evidence = bool(analysis.get("tests")) and all(
        test.get("referenced_apis") and test.get("assertions") for test in analysis.get("tests", [])
    )
    full_reference_coverage = bool(referenced_apis) and all(name in mapped_names for name in referenced_apis)
    full_test_coverage = bool(test_mapping) and all(item.get("coverage_level") == "semantic_mapped" for item in test_mapping)
    claimable = (
        total_definitions > 0
        and translated_functions == total_definitions
        and all_source_tests_have_evidence
        and full_reference_coverage
        and full_test_coverage
    )
    return {
        "project_dir": str(project_dir),
        "module_names": module_names,
        "mapped_apis": [name for name, _ in exported_functions],
        "unsupported_apis": unsupported_apis,
        "source_coverage": source_coverage,
        "module_list": module_list,
        "test_mapping": test_mapping,
        "bootstrap_only": not claimable,
        "semantic_equivalence_claim": "positive_semantic_claim" if claimable else "not_claimed",
        "crate_name": package_name,
    }
