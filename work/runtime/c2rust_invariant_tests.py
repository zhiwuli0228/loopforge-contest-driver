from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from c2rust_semantic_audit import required_scenarios, semantic_roles


def _ident(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", value).strip("_").lower()


def _struct_name(function: Dict[str, Any]) -> Optional[str]:
    param = next((p for p in function.get("params", []) if "struct " in p.get("type", "")), None)
    if not param:
        return None
    match = re.search(r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)", param["type"])
    return match.group(1).title().replace("_", "") if match else None


def render_invariant_tests(crate_name: str, analysis: Dict[str, Any], invariants: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
    roles = semantic_roles(analysis)
    mutator = roles["mutator"]
    if not mutator or not _struct_name(mutator):
        return "", []
    state = _struct_name(mutator)
    module = _ident(mutator.get("module_hint", "module"))
    init = roles["initializer"]["name"] if roles["initializer"] else None
    set_api = mutator["name"]
    get_api = roles["lookup"]["name"] if roles["lookup"] else None
    del_api = roles["delete"]["name"] if roles["delete"] else None
    count_api = roles["count"]["name"] if roles["count"] else None
    capacity = next((i.get("capacity") for i in invariants if i["kind"] == "capacity_limit"), None)
    capacity_expr = str(capacity) if isinstance(capacity, int) else "16"
    lines = [f"use {crate_name}::*;", f"use {crate_name}::{module}::{state};", ""]
    covered: List[Dict[str, Any]] = []

    def add(name: str, body: List[str]) -> None:
        lines.extend(["#[test]", f"fn test_{name}() {{", f"    let mut db = {state}::default();"])
        lines.extend(f"    {line}" for line in body)
        lines.extend(["}", ""])
        required = dict(required_scenarios(invariants)).get(name, [])
        covered.append({"scenario": name, "test": f"test_{name}", "covered": True, "invariants": required})

    if init and get_api:
        add("reset_after_mutation", [f'{set_api}(&mut db, "old", "value");', f"{init}(&mut db);", f'assert_eq!({set_api}(&mut db, "new", "value"), 0);', f'assert_eq!({get_api}(&db, "new"), Some("value".to_string()));', f'assert_eq!({get_api}(&db, "old"), None);'])
    if capacity and get_api:
        body = [f"for i in 0..{capacity_expr} {{", "    let key = format!(\"key-{i}\");", f'    assert_eq!({set_api}(&mut db, &key, "value"), 0);', "}", f'assert_ne!({set_api}(&mut db, "overflow", "value"), 0);']
        if count_api:
            body.append(f"assert_eq!({count_api}(&db), {capacity_expr});")
        body.append(f'assert_eq!({get_api}(&db, "key-0"), Some("value".to_string()));')
        add("capacity_boundary", body)
    if get_api:
        add("lookup_not_found", [f'assert_eq!({get_api}(&db, "missing"), None);', f'{set_api}(&mut db, "present", "value");', f'assert_eq!({get_api}(&db, "missing"), None);'])
    if del_api and get_api:
        body = [f'{set_api}(&mut db, "present", "value");', f'assert_ne!({del_api}(&mut db, "missing"), 0);', f'assert_eq!({get_api}(&db, "present"), Some("value".to_string()));']
        if count_api:
            body.append(f"assert_eq!({count_api}(&db), 1);")
        add("delete_not_found_preserves_state", body)
        body = [f'{set_api}(&mut db, "head", "1");', f'{set_api}(&mut db, "middle", "2");', f'{set_api}(&mut db, "tail", "3");', f'assert_eq!({del_api}(&mut db, "head"), 0);', f'assert_eq!({get_api}(&db, "middle"), Some("2".to_string()));', f'assert_eq!({del_api}(&mut db, "middle"), 0);', f'assert_eq!({get_api}(&db, "tail"), Some("3".to_string()));', f'assert_eq!({del_api}(&mut db, "tail"), 0);']
        if count_api:
            body.append(f"assert_eq!({count_api}(&db), 0);")
        add("delete_head_middle_tail", body)
    if get_api:
        body = [f'assert_eq!({set_api}(&mut db, "key", "one"), 0);', f'assert_eq!({set_api}(&mut db, "key", "two"), 0);', f'assert_eq!({get_api}(&db, "key"), Some("two".to_string()));']
        if count_api:
            body.append(f"assert_eq!({count_api}(&db), 1);")
        add("update_existing_does_not_increment_count", body)
    return "\n".join(lines).rstrip() + "\n", covered
