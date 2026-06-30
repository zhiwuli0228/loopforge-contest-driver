from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agent_task_packet import AgentTaskPacket, SourceLayout
from c2rust_semantic_audit import extract_semantic_invariants, required_scenarios


INCLUDE_RE = re.compile(r'^\s*#include\s+[<"]([^>"]+)[>"]', re.MULTILINE)
MACRO_RE = re.compile(r"^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)
STRUCT_DEFINITION_RE = re.compile(r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{([^{}]*)\}\s*;", re.DOTALL)
TYPEDEF_RE = re.compile(r"\btypedef\s+.+?\s+([A-Za-z_][A-Za-z0-9_]*)\s*;", re.DOTALL)
PROTOTYPE_RE = re.compile(r"(?m)^[ \t]*(?!#)([^;\r\n{}()]+?)[ \t]*\(([^;{}]*)\)[ \t]*;")
DEFINITION_HEADER_RE = re.compile(r"(?m)^[ \t]*(?!#)([^;\r\n{}()]+?)[ \t]*\(([^;{}]*)\)\s*\{")
ASSERT_RE = re.compile(r"\b((?:assert|ASSERT|TEST_ASSERT)(?:_[A-Za-z0-9_]+)?)\s*\(([^;\n]*)\)")
TEST_NAME_RE = re.compile(r"(?m)^\s*(?:void|int)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
CONTROL_KEYWORDS = {"if", "for", "while", "switch", "return", "sizeof"}
SUPPORTED_BODY_KINDS = {
    "empty",
    "return_number",
    "return_null",
    "return_identifier",
    "return_field",
    "return_binary_expr",
    "assignment_then_return",
    "state_mutation_then_return",
    "loop_find_then_return",
    "loop_find_then_mutate_return",
    "loop_find_then_shift_delete",
}


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


def _strip_comments(text: str) -> str:
    output: List[str] = []
    index = 0
    quote: Optional[str] = None
    escaped = False
    while index < len(text):
        char = text[index]
        following = text[index + 1] if index + 1 < len(text) else ""
        if quote:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char in {'"', "'"}:
            quote = char
            output.append(char)
            index += 1
            continue
        if char == "/" and following == "/":
            output.extend("  ")
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                output.append(" ")
                index += 1
            continue
        if char == "/" and following == "*":
            output.extend("  ")
            index += 2
            while index < len(text):
                if index + 1 < len(text) and text[index:index + 2] == "*/":
                    output.extend("  ")
                    index += 2
                    break
                output.append("\n" if text[index] == "\n" else " ")
                index += 1
            continue
        output.append(char)
        index += 1
    return "".join(output)


def _parseable_c(text: str) -> str:
    """Remove constructs that make the lightweight declaration parser ambiguous."""
    code = _strip_comments(text)
    # A macro continuation can look like a declaration or function body. Preserve
    # newlines so line-anchored parsing remains deterministic.
    return re.sub(r"(?m)^[ \t]*#.*(?:\\\r?\n.*)*$", "", code)


def _normalize_path(expr: str) -> str:
    value = " ".join(expr.split())
    value = value.replace("->", ".")
    value = re.sub(r"\s*\[\s*", "[", value)
    value = re.sub(r"\s*\]\s*", "]", value)
    value = re.sub(r"\s*\.\s*", ".", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _normalize_expression(expr: str) -> str:
    return _normalize_path(expr.rstrip(";"))


def _normalize_body(body: str) -> Tuple[str, List[Dict[str, Any]]]:
    code = _strip_comments(body)
    hints: List[Dict[str, Any]] = []

    def replace_strcmp(match: re.Match[str]) -> str:
        left = _normalize_expression(match.group(1))
        right = _normalize_expression(match.group(2))
        operator = match.group(3)
        hints.append({"kind": "string_compare", "operation": "string_equals", "left": left, "right": right, "operator": operator})
        expr = f"string_equals({left}, {right})"
        return expr if operator == "==" else f"!{expr}"

    code = re.sub(
        r"strcmp\s*\(\s*(.+?)\s*,\s*(.+?)\s*\)\s*(==|!=)\s*0",
        replace_strcmp,
        code,
        flags=re.DOTALL,
    )

    def replace_copy(match: re.Match[str]) -> str:
        function_name = match.group(1)
        destination = _normalize_expression(match.group(2))
        source = _normalize_expression(match.group(3))
        size = _normalize_expression(match.group(4)) if match.group(4) else ""
        hints.append(
            {
                "kind": "copy_operation",
                "operation": "copy",
                "function": function_name,
                "destination": destination,
                "source": source,
                "size": size,
            }
        )
        suffix = f", {size}" if size else ""
        return f"copy({destination}, {source}{suffix})"

    code = re.sub(
        r"\b(strcpy|strncpy|memcpy)\s*\(\s*(.+?)\s*,\s*(.+?)(?:\s*,\s*(.+?))?\s*\)",
        replace_copy,
        code,
        flags=re.DOTALL,
    )
    return (" ".join(code.split()), hints)


def _split_signature(prefix: str) -> Optional[Tuple[str, str]]:
    if prefix.strip() in CONTROL_KEYWORDS:
        return None
    match = re.fullmatch(r"(.+?(?:\s|\*))([A-Za-z_][A-Za-z0-9_]*)", prefix.strip())
    if not match:
        return None
    return_type = match.group(1).strip()
    name = match.group(2)
    if not return_type or return_type.split()[0] in CONTROL_KEYWORDS | {"typedef"} or "=" in return_type or "#" in return_type:
        return None
    return (return_type, name)


def _iter_definitions(text: str) -> List[Tuple[str, str, str, str]]:
    definitions: List[Tuple[str, str, str, str]] = []
    for match in DEFINITION_HEADER_RE.finditer(text):
        signature = _split_signature(match.group(1))
        if not signature:
            continue
        return_type, name = signature
        params_text = match.group(2)
        opening = match.end() - 1
        depth = 0
        quote: Optional[str] = None
        escaped = False
        for index in range(opening, len(text)):
            char = text[index]
            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
                continue
            if char in {'"', "'"}:
                quote = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    definitions.append((return_type, name, params_text, text[opening + 1:index]))
                    break
    return definitions


def _parse_comparison(condition: str) -> Optional[Dict[str, Any]]:
    text = _normalize_expression(condition)
    string_match = re.fullmatch(r"!?string_equals\((.+), (.+)\)", text)
    if string_match:
        negated = text.startswith("!")
        left = string_match.group(1)
        right = string_match.group(2)
        return {
            "kind": "string_equals",
            "left": left[1:] if left.startswith("!") else left,
            "right": right,
            "negated": negated,
        }
    binary_match = re.fullmatch(r"(.+?)\s*(==|!=|<=|>=|<|>)\s*(.+)", text)
    if binary_match:
        return {
            "kind": "binary",
            "left": _normalize_expression(binary_match.group(1)),
            "operator": binary_match.group(2),
            "right": _normalize_expression(binary_match.group(3)),
            "negated": False,
        }
    return None


def _parse_assignment(statement: str) -> Optional[Dict[str, str]]:
    assignment = re.fullmatch(r"(.+?)\s*(=|\+=|-=|\*=|/=)\s*(.+)", statement.strip())
    if not assignment:
        return None
    return {
        "target": _normalize_expression(assignment.group(1)),
        "operator": assignment.group(2),
        "value": _normalize_expression(assignment.group(3)),
    }


def _parse_simple_block(block: str) -> List[Dict[str, str]]:
    statements = [item.strip() for item in block.strip().strip("{}").split(";") if item.strip()]
    parsed: List[Dict[str, str]] = []
    for statement in statements:
        assignment = _parse_assignment(statement)
        if not assignment:
            return []
        parsed.append(assignment)
    return parsed


def _find_matching(text: str, start: int, opening: str, closing: str) -> int:
    depth = 0
    quote: Optional[str] = None
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {'"', "'"}:
            quote = char
        elif char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return index
    return -1


def _analyze_loop_find_then_return(normalized: str) -> Optional[Dict[str, Any]]:
    match = re.fullmatch(
        r"for\s*\((.+?)\)\s*\{\s*if\s*\((.+?)\)\s*\{\s*return\s+(.+?)\s*;\s*\}\s*\}\s*return\s+(.+?)\s*;",
        normalized,
    )
    if not match:
        return None
    comparison = _parse_comparison(match.group(2))
    if comparison is None:
        return None
    return {
        "kind": "loop_find_then_return",
        "value": {
            "loop_header": _normalize_expression(match.group(1)),
            "match_condition": comparison,
            "return_expr": _normalize_expression(match.group(3)),
            "fallback_return": _normalize_expression(match.group(4)),
        },
    }


def _analyze_loop_find_then_mutate_return(normalized: str) -> Optional[Dict[str, Any]]:
    match = re.fullmatch(
        r"for\s*\((.+?)\)\s*\{\s*if\s*\((.+?)\)\s*\{\s*(.+?)\s*return\s+(.+?)\s*;\s*\}\s*\}\s*if\s*\((.+?)\)\s*\{\s*return\s+(.+?)\s*;\s*\}\s*(.+?)\s*return\s+(.+?)\s*;",
        normalized,
    )
    if not match:
        return None
    comparison = _parse_comparison(match.group(2))
    found_assignments = _parse_simple_block(match.group(3))
    append_assignments = _parse_simple_block(match.group(7))
    if comparison is None or not found_assignments or not append_assignments:
        return None
    guard = _parse_comparison(match.group(5))
    if guard is None:
        return None
    return {
        "kind": "loop_find_then_mutate_return",
        "value": {
            "loop_header": _normalize_expression(match.group(1)),
            "match_condition": comparison,
            "found_assignments": found_assignments,
            "found_return": _normalize_expression(match.group(4)),
            "capacity_guard": {
                "condition": guard,
                "return": _normalize_expression(match.group(6)),
            },
            "append_assignments": append_assignments,
            "tail_return": _normalize_expression(match.group(8)),
        },
    }


def _analyze_loop_find_then_shift_delete(normalized: str) -> Optional[Dict[str, Any]]:
    match = re.fullmatch(
        r"for\s*\((.+?)\)\s*\{\s*if\s*\((.+?)\)\s*\{\s*for\s*\((.+?)\)\s*\{\s*(.+?)\s*;\s*\}\s*(.+?)\s*;\s*return\s+(.+?)\s*;\s*\}\s*\}\s*return\s+(.+?)\s*;",
        normalized,
    )
    if not match:
        return None
    comparison = _parse_comparison(match.group(2))
    shift_assignment = _parse_assignment(match.group(4))
    count_update = _parse_assignment(match.group(5))
    if comparison is None or shift_assignment is None or count_update is None:
        return None
    return {
        "kind": "loop_find_then_shift_delete",
        "value": {
            "outer_loop_header": _normalize_expression(match.group(1)),
            "match_condition": comparison,
            "shift_loop_header": _normalize_expression(match.group(3)),
            "shift_assignment": shift_assignment,
            "count_update": count_update,
            "match_return": _normalize_expression(match.group(6)),
            "fallback_return": _normalize_expression(match.group(7)),
        },
    }


def _body_kind(return_type: str, body: str) -> Dict[str, Any]:
    normalized, hints = _normalize_body(body)
    payload: Dict[str, Any] = {
        "body_kind": "unsupported",
        "body_value": None,
        "translation_status": "unsupported",
        "unsupported_reason": "function body does not match a supported translation pattern",
        "raw_body": body,
        "normalized_body": normalized,
        "semantic_hints": hints,
    }

    if not normalized:
        payload.update({"body_kind": "empty", "translation_status": "translated", "unsupported_reason": None})
        return payload

    loop_payload = _analyze_loop_find_then_mutate_return(normalized)
    if loop_payload is None:
        loop_payload = _analyze_loop_find_then_shift_delete(normalized)
    if loop_payload is None:
        loop_payload = _analyze_loop_find_then_return(normalized)
    if loop_payload is not None:
        payload.update(
            {
                "body_kind": loop_payload["kind"],
                "body_value": loop_payload["value"],
                "translation_status": "translated",
                "unsupported_reason": None,
            }
        )
        return payload

    return_number = re.fullmatch(r"return\s+(-?\d+)\s*;", normalized)
    if return_number:
        payload.update({"body_kind": "return_number", "body_value": return_number.group(1), "translation_status": "translated", "unsupported_reason": None})
        return payload
    if normalized in {"return NULL;", "return null;", "return 0;"} and "*" in return_type:
        payload.update({"body_kind": "return_null", "translation_status": "translated", "unsupported_reason": None})
        return payload
    return_identifier = re.fullmatch(r"return\s+([A-Za-z_][A-Za-z0-9_]*)\s*;", normalized)
    if return_identifier:
        payload.update({"body_kind": "return_identifier", "body_value": return_identifier.group(1), "translation_status": "translated", "unsupported_reason": None})
        return payload
    return_field = re.fullmatch(
        r"return\s+([A-Za-z_][A-Za-z0-9_]*(?:\s*(?:\.|\->)\s*[A-Za-z_][A-Za-z0-9_]*|\[[^\]]+\])+)\s*;",
        normalized,
    )
    if return_field:
        payload.update({"body_kind": "return_field", "body_value": _normalize_expression(return_field.group(1)), "translation_status": "translated", "unsupported_reason": None})
        return payload
    return_binary = re.fullmatch(
        r"return\s+(.+?)\s*(==|!=|<=|>=|\+|-|\*|/|%|<|>|&&|\|\|)\s*(.+?)\s*;",
        normalized,
    )
    if return_binary:
        payload.update(
            {
                "body_kind": "return_binary_expr",
                "body_value": {
                    "left": _normalize_expression(return_binary.group(1)),
                    "operator": return_binary.group(2),
                    "right": _normalize_expression(return_binary.group(3)),
                },
                "translation_status": "translated",
                "unsupported_reason": None,
            }
        )
        return payload

    simple_body = re.fullmatch(r"(.+?;)\s*(?:return\s+(.+?)\s*;)?", normalized)
    if simple_body:
        statements = [item.strip() for item in simple_body.group(1).split(";") if item.strip()]
        assignments = []
        for statement in statements:
            assignment = _parse_assignment(statement)
            if not assignment:
                assignments = []
                break
            assignments.append(assignment)
        if assignments and len(assignments) == len(statements):
            has_state_target = any(any(token in item["target"] for token in [".", "["]) for item in assignments)
            kind = "state_mutation_then_return" if has_state_target else "assignment_then_return"
            payload.update(
                {
                    "body_kind": kind,
                    "body_value": {"assignments": assignments, "return_expr": _normalize_expression(simple_body.group(2)) if simple_body.group(2) else None},
                    "translation_status": "translated",
                    "unsupported_reason": None,
                }
            )
            return payload

    if any(token in normalized for token in ["for (", "for(", "while (", "while(", "if (", "if(", "switch ("]):
        payload["unsupported_reason"] = "control flow pattern not recognized by the source-driven translator"
    return payload


def _parse_params(params_text: str) -> List[Dict[str, str]]:
    params_text = params_text.strip()
    if not params_text or params_text == "void":
        return []
    params: List[Dict[str, str]] = []
    for index, raw in enumerate(params_text.split(",")):
        candidate = raw.strip()
        declaration = re.fullmatch(r"(.+?)(\**)([A-Za-z_][A-Za-z0-9_]*)(\s*\[[^]]+\])?", candidate)
        if declaration:
            type_text = f"{declaration.group(1).strip()} {declaration.group(2)}".strip()
            name = declaration.group(3)
        else:
            type_text, name = candidate, f"arg{index}"
        params.append({"name": name.strip() or f"arg{index}", "type": " ".join(type_text.split())})
    return params


def _parse_struct_fields(body: str) -> List[Dict[str, str]]:
    fields: List[Dict[str, str]] = []
    for declaration in body.split(";"):
        candidate = " ".join(declaration.split())
        if not candidate:
            continue
        match = re.fullmatch(r"(.+?)(\**)([A-Za-z_][A-Za-z0-9_]*)(\s*\[\s*([0-9]+)\s*\])?", candidate)
        if not match:
            continue
        fields.append(
            {
                "name": match.group(3),
                "type": f"{match.group(1).strip()} {match.group(2)}".strip(),
                "array_length": match.group(5) or "",
            }
        )
    return fields


def _parse_assertions(text: str) -> List[Dict[str, str]]:
    assertions = [{"kind": "macro", "macro": macro, "expr": expr.strip()} for macro, expr in ASSERT_RE.findall(text)]
    code = _strip_comments(text)
    failure_returns = re.finditer(
        r"\bif\s*\(([^)]*)\)\s*\{?\s*return\s+(-1|[1-9][0-9]*|false|NULL)\s*;",
        code,
        re.IGNORECASE,
    )
    assertions.extend(
        {"kind": "if_return_failure", "macro": "if-return-failure", "expr": match.group(1).strip()}
        for match in failure_returns
    )
    exit_failures = re.finditer(r"\bexit\s*\(\s*(EXIT_FAILURE|-?[1-9][0-9]*)\s*\)", code)
    assertions.extend(
        {"kind": "exit_failure", "macro": "exit-failure", "expr": match.group(1).strip()}
        for match in exit_failures
    )
    comment_text = " ".join(part for pair in re.findall(r"/\*(.*?)\*/|//([^\n]*)", text, flags=re.DOTALL) for part in pair)
    for left, operator, right in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*(==|!=|<=|>=|<|>)\s*([A-Za-z_0-9-]+)", comment_text):
        assertions.append({"kind": "scenario_condition", "macro": "scenario", "expr": f"{left} {operator} {right}"})
    return assertions


def _referenced_apis(text: str, public_apis: List[str], function_table: List[Dict[str, Any]]) -> Tuple[List[str], Dict[str, str]]:
    known_apis = _dedupe(public_apis + [item["name"] for item in function_table])
    code = _strip_comments(text)
    references = [name for name in known_apis if re.search(rf"\b{re.escape(name)}\s*\(", code)]
    evidence = {name: "function_call" for name in references}

    comment_text = " ".join(part for pair in re.findall(r"/\*(.*?)\*/|//([^\n]*)", text, flags=re.DOTALL) for part in pair).lower()
    aliases = {
        "new": ("new", "create", "creating", "initialize", "initializing"),
        "set": ("set", "setting", "store", "storing", "overwrite", "overwriting"),
        "get": ("get", "getting", "retrieve", "retrieving", "returns"),
        "delete": ("delete", "deleting", "remove", "removing"),
        "count": ("count", "counting"),
    }
    for name in known_apis:
        if name in evidence:
            continue
        suffix = name.rsplit("_", 1)[-1].lower()
        words = aliases.get(suffix, (suffix,))
        if any(re.search(rf"\b{re.escape(word)}\b", comment_text) for word in words):
            references.append(name)
            evidence[name] = "scenario_text"
    return (_dedupe(references), evidence)


def analyze_source(packet: AgentTaskPacket) -> Dict[str, Any]:
    readme_path = Path(packet.metadata.get("selected_readme_path", "")).resolve() if packet.metadata.get("selected_readme_path") else None
    fallback_readme = Path(packet.metadata.get("fallback_readme_path", "")).resolve() if packet.metadata.get("fallback_readme_path") else None

    resolution = packet.metadata.get("layout_resolution", {})
    project_root = Path(resolution["resolved_project_root"]).resolve() if resolution.get("resolved_project_root") else None
    source_dirs = [Path(path).resolve() for path in resolution.get("source_dirs", [])]
    test_dirs = [Path(path).resolve() for path in resolution.get("test_dirs", [])]
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
        parseable_text = _parseable_c(text)
        rel = _sanitize_rel(path, project_base)
        include_graph.append({"file": rel, "includes": _dedupe(INCLUDE_RE.findall(text))})
        for macro in MACRO_RE.findall(text):
            macros.append({"name": macro, "file": rel})
        for struct_name, struct_body in STRUCT_DEFINITION_RE.findall(text):
            types.append({"name": struct_name, "kind": "struct", "file": rel, "fields": _parse_struct_fields(struct_body)})
        for typedef_name in TYPEDEF_RE.findall(text):
            types.append({"name": typedef_name, "kind": "typedef", "file": rel})
        if path in src_files:
            # Only header declarations define the public surface. Parsing call-like
            # statements in .c files as prototypes polluted the API list.
            if path.suffix.lower() == ".h":
                for signature_text, params_text in PROTOTYPE_RE.findall(parseable_text):
                    signature = _split_signature(signature_text)
                    if not signature:
                        continue
                    return_type, name = signature
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
                            "raw_body": "",
                            "normalized_body": "",
                            "semantic_hints": [],
                            "translation_status": "declaration_only",
                            "unsupported_reason": None,
                            "module_hint": Path(rel).stem,
                        }
                    )
                    public_api_names.append(name)

            for return_type, name, params_text, body in _iter_definitions(parseable_text):
                if name in CONTROL_KEYWORDS:
                    continue
                params = _parse_params(params_text)
                analysis_payload = _body_kind(return_type, body)
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
                        "body_kind": analysis_payload["body_kind"],
                        "body_value": analysis_payload["body_value"],
                        "raw_body": analysis_payload["raw_body"],
                        "normalized_body": analysis_payload["normalized_body"],
                        "semantic_hints": analysis_payload["semantic_hints"],
                        "translation_status": analysis_payload["translation_status"],
                        "unsupported_reason": analysis_payload["unsupported_reason"],
                        "module_hint": Path(rel).stem,
                    }
                )
                # Header declarations, rather than private/static implementation
                # helpers, determine which definitions must satisfy the gate.

    hinted_api_names = [name for name in packet.api_name_hints if any(item["name"] == name for item in functions)]
    if hinted_api_names:
        public_apis = _dedupe(hinted_api_names + sorted(public_api_names))
    else:
        public_apis = _dedupe(sorted(public_api_names))

    tests: List[Dict[str, Any]] = []
    for path in test_files:
        text = _read_text(path)
        rel = _sanitize_rel(path, project_base)
        assertions = _parse_assertions(text)
        referenced_apis, reference_evidence = _referenced_apis(text, public_apis, functions)
        test_names = [name for name in TEST_NAME_RE.findall(text) if name not in CONTROL_KEYWORDS]
        if not test_names:
            test_names = [Path(rel).stem]
        tests.append(
            {
                "file": rel,
                "test_names": _dedupe(test_names),
                "assertions": assertions,
                "referenced_apis": _dedupe(referenced_apis),
                "reference_evidence": reference_evidence,
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
    analysis["semantic_invariants"] = extract_semantic_invariants(analysis)

    if readme_path is None:
        packet.add_issue("readme_missing", f"README candidate not found under {project_root or packet.paths.input_root}")
    if project_root is None:
        packet.add_issue("source_layout_missing", resolution.get("reason", "unable to resolve usable C project layout from input_root"))
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
    rust_test_text = "\n".join(_read_text(path) for path in test_files)
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
        file_asserts = text.count("assert!(") + text.count("assert_eq!(") + text.count("assert_ne!(") + text.count("matches!(")
        test_functions += text.count("#[test]")
        if file_asserts == 0:
            test_assertions_ok = False
        test_assert_count += file_asserts
    checks.append({"name": "assertive_tests", "passed": test_assertions_ok and test_assert_count > 0, "detail": "each Rust test file contains assertions", "assert_count": test_assert_count})

    mapped_apis = project_payload.get("mapped_apis", [])
    unsupported_apis = project_payload.get("unsupported_apis", [])
    api_matches = [name for name in mapped_apis if re.search(rf"\b{re.escape(name)}\s*\(", rust_test_text)]
    semantic_map_ok = bool(mapped_apis) and len(api_matches) == len(mapped_apis)
    checks.append(
        {
            "name": "api_mapping",
            "passed": semantic_map_ok,
            "detail": "every mapped source API is called by generated Rust tests",
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

    invariants = analysis.get("semantic_invariants", [])
    invariant_file = project_dir / "tests" / "semantic_invariants.rs"
    plan = project_payload.get("semantic_test_plan", [])
    required = {name for name, _ in required_scenarios(invariants)}
    covered = {item.get("scenario") for item in plan if item.get("covered")}
    extraction_ok = bool(invariants)
    tests_ok = invariant_file.is_file() and bool(required) and required <= covered
    checks.append({"name": "semantic_invariant_extraction", "passed": extraction_ok, "detail": "source behavior produced semantic invariants", "invariant_count": len(invariants)})
    checks.append({"name": "semantic_invariant_tests", "passed": tests_ok, "detail": "all required invariant-derived scenarios are present and executed by cargo test", "required": sorted(required), "covered": sorted(covered)})
    unresolved = verification_payload.get("unresolved_failures", [])
    checks.append({"name": "repair_loop_resolved", "passed": not unresolved, "detail": "repair loop has no unresolved failures", "unresolved_failures": unresolved})

    passed = all(check["passed"] for check in checks)
    failing = [check["name"] for check in checks if not check["passed"]]
    if not passed:
        uncovered_tests = [
            item.get("source_test", "unknown")
            for item in project_payload.get("test_mapping", [])
            if item.get("coverage_level") in {"none", "structural_only", "partial_semantic"}
        ]
        detail_parts = [f"semantic checks failed: {', '.join(failing)}"]
        if unsupported_apis:
            detail_parts.append(f"APIs without translated semantic coverage: {', '.join(unsupported_apis)}")
        if uncovered_tests:
            detail_parts.append(f"source tests without complete semantic coverage: {', '.join(uncovered_tests)}")
        packet.add_issue("semantic_gate_failed", "; ".join(detail_parts))
    return {
        "passed": passed,
        "checks": checks,
        "failing_checks": failing,
        "unresolved_failures": unresolved,
    }
