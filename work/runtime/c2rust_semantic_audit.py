from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _definitions(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [item for item in analysis.get("functions", []) if item.get("decl_kind") == "definition"]


def _role(functions: List[Dict[str, Any]], kind: str) -> Optional[Dict[str, Any]]:
    return next((item for item in functions if item.get("body_kind") == kind), None)


def extract_semantic_invariants(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Derive testable, API-name-independent invariants from normalized C behavior."""
    functions = _definitions(analysis)
    initializer = next(
        (
            item for item in functions
            if item.get("body_kind") == "state_mutation_then_return"
            and any(a.get("value") == "0" for a in (item.get("body_value") or {}).get("assignments", []))
        ),
        None,
    )
    mutator = _role(functions, "loop_find_then_mutate_return")
    lookup = _role(functions, "loop_find_then_return")
    delete = _role(functions, "loop_find_then_shift_delete")
    count = _role(functions, "return_field")
    invariants: List[Dict[str, Any]] = []

    if initializer:
        reset_fields = [a["target"].rsplit(".", 1)[-1] for a in initializer["body_value"].get("assignments", []) if a.get("value") == "0"]
        invariants.append({"id": "state_reset", "kind": "state_reset", "api": initializer["name"], "reset_fields": reset_fields, "requires_logical_storage_reset": True})
    if mutator:
        body = mutator.get("body_value") or {}
        guard = body.get("capacity_guard") or {}
        condition = guard.get("condition") or {}
        capacity = condition.get("right", "")
        macro_names = {item.get("name") for item in analysis.get("macro_table", [])}
        if capacity in macro_names or capacity.isdigit():
            invariants.append({"id": "capacity_limit", "kind": "capacity_limit", "api": mutator["name"], "capacity": int(capacity) if capacity.isdigit() else capacity, "overflow_return": guard.get("return"), "state_preserved_on_overflow": True})
        invariants.append({"id": "insert_or_update", "kind": "insert_or_update", "api": mutator["name"], "update_existing": True, "append_new": True, "duplicate_increments_count": False})
        invariants.append({"id": "state_preserved_on_error", "kind": "state_preserved_on_error", "api": mutator["name"]})
    if lookup:
        invariants.append({"id": "lookup_not_found", "kind": "lookup_not_found", "api": lookup["name"], "return_value": lookup.get("body_value", {}).get("fallback_return", "NULL")})
    if delete:
        body = delete.get("body_value") or {}
        invariants.append({"id": "delete_shift", "kind": "delete_shift", "api": delete["name"], "delete_existing_return": body.get("match_return"), "remaining_items_queryable": True})
        invariants.append({"id": "delete_missing", "kind": "delete_missing", "api": delete["name"], "delete_missing_return": body.get("fallback_return"), "state_preserved": True})
    if count:
        for item in invariants:
            item.setdefault("count_api", count["name"])
    return invariants


def semantic_roles(analysis: Dict[str, Any]) -> Dict[str, Optional[Dict[str, Any]]]:
    functions = _definitions(analysis)
    return {
        "initializer": next((i for i in functions if i.get("body_kind") == "state_mutation_then_return" and any(a.get("value") == "0" for a in (i.get("body_value") or {}).get("assignments", []))), None),
        "mutator": _role(functions, "loop_find_then_mutate_return"),
        "lookup": _role(functions, "loop_find_then_return"),
        "delete": _role(functions, "loop_find_then_shift_delete"),
        "count": _role(functions, "return_field"),
    }


def required_scenarios(invariants: List[Dict[str, Any]]) -> List[Tuple[str, List[str]]]:
    kinds = {item["kind"] for item in invariants}
    scenarios: List[Tuple[str, List[str]]] = []
    if {"state_reset", "insert_or_update", "lookup_not_found"} <= kinds:
        scenarios.append(("reset_after_mutation", ["state_reset", "insert_or_update", "lookup_not_found"]))
    if "capacity_limit" in kinds:
        scenarios.append(("capacity_boundary", ["capacity_limit", "state_preserved_on_error"]))
    if "lookup_not_found" in kinds:
        scenarios.append(("lookup_not_found", ["lookup_not_found"]))
    if "delete_missing" in kinds:
        scenarios.append(("delete_not_found_preserves_state", ["delete_missing", "state_preserved_on_error"]))
    if "delete_shift" in kinds:
        scenarios.append(("delete_head_middle_tail", ["delete_shift"]))
    if "insert_or_update" in kinds:
        scenarios.append(("update_existing_does_not_increment_count", ["insert_or_update"]))
    return scenarios
