"""Project-independent semantic obligations derived only from runtime evidence."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence


SCHEMA_VERSION = "semantic-migration-planning/v3"
ANALYSIS_SCHEMA_VERSION = "c-source-analysis/v2"
LEGACY_SCHEMA_VERSIONS = {"flashdb-semantic-planning/v1", "semantic-migration-planning/v2"}
OUTPUT_FILES = (
    "behavior-contracts.json", "state-transitions.json", "semantic-invariants.json",
    "rust-migration-plan.json", "semantic-planning-verification.json",
)
REQUIRED_ANALYSIS_FILES = (
    "source-inventory.json", "public-api-map.json", "type-map.json", "call-graph.json",
    "global-state-map.json", "preprocessor-variants.json", "analysis-verification.json",
)


class PlanningBlocked(RuntimeError):
    def __init__(self, failures: Sequence[str]):
        self.failures = sorted(set(failures))
        super().__init__(", ".join(self.failures))


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _id(kind: str, *parts: str) -> str:
    return f"{kind}-{hashlib.sha256('|'.join(parts).encode()).hexdigest()[:16]}"


def _sorted(items: Iterable[Dict[str, Any]], *keys: str) -> List[Dict[str, Any]]:
    return sorted(items, key=lambda item: tuple(str(item.get(key, "")) for key in keys))


def _api_evidence(api: Mapping[str, Any]) -> List[Dict[str, Any]]:
    result = []
    for role in ("declaration", "definition"):
        value = api.get(role)
        if isinstance(value, dict) and value.get("file"):
            result.append({"id": f"source:{api.get('id')}:{role}", "file": value["file"], "line": int(value.get("line", 0)), "symbol": value.get("symbol") or api.get("name", "")})
    return _sorted(result, "id")


def load_analysis_evidence(trace_dir: Path) -> Dict[str, Dict[str, Any]]:
    docs: Dict[str, Dict[str, Any]] = {}
    failures: List[str] = []
    for name in REQUIRED_ANALYSIS_FILES:
        path = trace_dir / name
        if not path.is_file():
            failures.append(f"missing_analysis_evidence:{name}")
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            failures.append(f"invalid_analysis_json:{name}")
            continue
        if not isinstance(value, dict) or value.get("schema_version") != ANALYSIS_SCHEMA_VERSION:
            failures.append(f"invalid_analysis_schema:{name}")
        if not value.get("run_id") or not value.get("source_digest"):
            failures.append(f"missing_analysis_metadata:{name}")
        docs[name] = value
    if len({doc.get("run_id") for doc in docs.values()}) != 1:
        failures.append("mixed_analysis_run_ids")
    if len({doc.get("source_digest") for doc in docs.values()}) != 1:
        failures.append("mixed_analysis_source_digests")
    verification = docs.get("analysis-verification.json", {})
    if verification.get("passed") is not True or verification.get("status") != "PASSED":
        failures.append("analysis_verification_not_passed")
    if not docs.get("public-api-map.json", {}).get("apis"):
        failures.append("empty_analysis_denominator:public_apis")
    if not docs.get("type-map.json", {}).get("types"):
        failures.append("empty_analysis_denominator:types")
    if failures:
        raise PlanningBlocked(failures)
    return docs


def _source_module(api: Mapping[str, Any]) -> str:
    definition = api.get("definition") or {}
    path = Path(str(definition.get("file", "source")))
    return path.stem or "source"


def _build_ir(docs: Mapping[str, Dict[str, Any]]) -> Dict[str, Any]:
    apis = _sorted(docs["public-api-map.json"].get("apis", []), "id")
    globals_ = docs["global-state-map.json"].get("globals", [])
    edges = docs["call-graph.json"].get("call_edges", [])
    resources = [{"id": _id("resource", item.get("name", "")), "source_name": item.get("name", ""), "kind": "source-global-state", "derivation_kind": "source-derived", "evidence_ids": [f"source:global:{item.get('name', '')}"], "source_evidence": [item["evidence"]] if item.get("evidence") else []} for item in globals_]
    effects, errors, contracts, transitions = [], [], [], []
    for api in apis:
        evidence = _api_evidence(api)
        evidence_ids = [item["id"] for item in evidence]
        effect_id = _id("effect", api["id"], "preserve-source-effects")
        error_id = _id("result", api["id"], api.get("return_type", ""))
        effects.append({"id": effect_id, "api_id": api["id"], "operation": "preserve-source-effects", "resource_ids": [item["id"] for item in resources], "postcondition": "all source-observable side effects are preserved", "derivation_kind": "source-derived", "evidence_ids": evidence_ids})
        errors.append({"id": error_id, "api_id": api["id"], "source_return_type": api.get("return_type", ""), "classification": "preserve-source-result-space", "derivation_kind": "source-derived", "evidence_ids": evidence_ids})
        contract_id = _id("contract", api["id"])
        contracts.append({"id": contract_id, "api_id": api["id"], "api": api["name"], "inputs": api.get("inputs", []), "return_type": api.get("return_type", ""), "preconditions": ["preserve source preconditions; no additional precondition may be introduced"], "effect_ids": [effect_id], "error_ids": [error_id], "state_mutations": [{"state": "source-observable-state", "success_postcondition": "source effects preserved", "failure_postcondition": "source failure effects preserved"}], "derivation_kind": "source-derived", "evidence_ids": evidence_ids, "source_evidence": evidence})
        transitions.append({"id": _id("transition", api["id"]), "trigger_api_id": api["id"], "contract_id": contract_id, "precondition": {"operator": "source-precondition"}, "postcondition": {"operator": "source-observable-equivalence"}, "derivation_kind": "source-derived", "evidence_ids": evidence_ids})
    defined = {item.get("name") for item in apis} | {item.get("caller") for item in edges}
    boundaries = []
    for edge in edges:
        if edge.get("callee") in defined:
            continue
        edge_id = edge.get("id") or _id("edge", edge.get("caller", ""), edge.get("callee", ""))
        boundaries.append({"id": _id("boundary", edge_id), "source_edge_id": edge_id, "caller": edge.get("caller", ""), "callee": edge.get("callee", ""), "port_id": _id("port", edge.get("callee", "external")), "operations": ["call"], "derivation_kind": "source-derived", "evidence_ids": [f"source:edge:{edge_id}"], "source_evidence": [edge["evidence"]] if edge.get("evidence") else []})
    invariants = [{"id": _id("invariant", edge.get("id") or str(index)), "kind": "call-edge-preservation", "source_edge_id": edge.get("id") or _id("edge", edge.get("caller", ""), edge.get("callee", "")), "assertion": {"operator": "preserved-call", "left": edge.get("caller", ""), "right": edge.get("callee", "")}, "derivation_kind": "source-derived", "evidence_ids": [f"source:edge:{edge.get('id') or index}"]} for index, edge in enumerate(edges)]
    return {"api_contracts": contracts, "resources": _sorted(resources, "id"), "effects": _sorted(effects, "id"), "errors": _sorted(errors, "id"), "transitions": _sorted(transitions, "id"), "invariants": _sorted(invariants, "id"), "external_boundaries": _sorted(boundaries, "id"), "unresolved_items": []}


def _build_plan(docs: Mapping[str, Dict[str, Any]], ir: Mapping[str, Any]) -> Dict[str, Any]:
    types = []
    for item in docs["type-map.json"].get("types", []):
        source_id = item.get("id") or _id("type", item.get("kind", ""), item.get("name", ""))
        types.append({"source_type_id": source_id, "source_name": item.get("name", ""), "rust_type": item.get("name") or "AnonymousType", "layout": "preserve-source-layout-when-observable", "owner": "derived-from-use-sites", "borrowing": "scoped", "lifetime": "owner-bounded", "mutability": "source-effect-constrained", "thread_safety": "source-concurrency-constrained", "members": [{"name": member.get("name", ""), "rust_mapping": member.get("type") or "source-member"} for member in item.get("members", [])], "derivation_kind": "source-derived", "evidence_ids": [f"source:type:{source_id}"], "source_evidence": [item["evidence"]] if item.get("evidence") else []})
    states = [{"source_state": item.get("name", ""), "owner": "derived-from-access-graph", "access": "preserve-source-access", "derivation_kind": "source-derived", "evidence_ids": [f"source:global:{item.get('name', '')}"], "source_evidence": [item["evidence"]] if item.get("evidence") else []} for item in docs["global-state-map.json"].get("globals", [])]
    boundary_by_edge = {item["source_edge_id"]: item for item in ir["external_boundaries"]}
    edge_mappings = []
    for edge in docs["call-graph.json"].get("call_edges", []):
        edge_id = edge.get("id") or _id("edge", edge.get("caller", ""), edge.get("callee", ""))
        boundary = boundary_by_edge.get(edge_id)
        edge_mappings.append({"source_edge_id": edge_id, "caller": edge.get("caller", ""), "callee": edge.get("callee", ""), "rust_target": boundary["port_id"] if boundary else "module-call", "equivalence_reason": "preserve source parameters, result and effects", "boundary_id": boundary["id"] if boundary else "", "derivation_kind": "source-derived", "evidence_ids": [f"source:edge:{edge_id}"]})
    ports = [{"id": item["port_id"], "boundary_id": item["id"], "operations": item["operations"], "error_semantics": "preserve-source-result", "atomicity": "preserve-source-boundary", "test_double": True, "derivation_kind": "source-derived", "evidence_ids": item["evidence_ids"]} for item in ir["external_boundaries"]]
    contracts = {item["api_id"]: item for item in ir["api_contracts"]}
    obligations = []
    for api in docs["public-api-map.json"].get("apis", []):
        contract = contracts[api["id"]]
        obligations.append({"id": _id("implementation", api["id"]), "api_id": api["id"], "contract_id": contract["id"], "target_module": _source_module(api), "effect_ids": contract["effect_ids"], "error_ids": contract["error_ids"], "boundary_dependencies": sorted({item["id"] for item in ports}), "completion_criteria": "source-observable behavior and call relations are preserved", "derivation_kind": "source-derived", "evidence_ids": contract["evidence_ids"]})
    return {"type_mappings": _sorted(types, "source_type_id"), "state_mappings": _sorted(states, "source_state"), "call_edge_mappings": _sorted(edge_mappings, "source_edge_id"), "ports": _sorted(ports, "id"), "implementation_obligations": _sorted(obligations, "api_id"), "verification_obligations": [{"id": _id("verification", item["id"]), "invariant_id": item["id"], "oracle": item["assertion"], "evidence_ids": item["evidence_ids"]} for item in ir["invariants"]], "unresolved_core_items": []}


def validate_plan(docs: Mapping[str, Dict[str, Any]], artifacts: Mapping[str, Dict[str, Any]]) -> Dict[str, Any]:
    ir = artifacts["semantic-ir"]
    plan = artifacts["rust-migration-plan.json"]
    api_ids = {item.get("id") for item in docs["public-api-map.json"].get("apis", [])}
    expected_types = {item.get("id") or _id("type", item.get("kind", ""), item.get("name", "")) for item in docs["type-map.json"].get("types", [])}
    expected_members = {(item.get("id") or _id("type", item.get("kind", ""), item.get("name", "")), member.get("name")) for item in docs["type-map.json"].get("types", []) for member in item.get("members", [])}
    expected_states = {item.get("name") for item in docs["global-state-map.json"].get("globals", [])}
    expected_edges = {item.get("id") or _id("edge", item.get("caller", ""), item.get("callee", "")) for item in docs["call-graph.json"].get("call_edges", [])}
    boundary_ids = {item["id"] for item in ir["external_boundaries"]}
    evidence_complete = all(item.get("derivation_kind") == "source-derived" and item.get("evidence_ids") for field in ("api_contracts", "effects", "errors", "transitions", "invariants", "external_boundaries") for item in ir[field])
    checks = {
        "public_api_denominator_nonempty": bool(api_ids),
        "public_api_contract_coverage_100_percent": {item.get("api_id") for item in ir["api_contracts"]} == api_ids,
        "source_evidence_complete": evidence_complete,
        "core_type_mapping_coverage_100_percent": {item.get("source_type_id") for item in plan["type_mappings"]} == expected_types,
        "core_type_member_mapping_coverage_100_percent": {(item.get("source_type_id"), member.get("name")) for item in plan["type_mappings"] for member in item.get("members", [])} == expected_members,
        "shared_state_mapping_coverage_100_percent": {item.get("source_state") for item in plan["state_mappings"]} == expected_states,
        "call_edge_mapping_coverage_100_percent": {item.get("source_edge_id") for item in plan["call_edge_mappings"]} == expected_edges,
        "implementation_obligation_coverage_100_percent": {item.get("api_id") for item in plan["implementation_obligations"]} == api_ids,
        "ports_are_source_derived": all(item.get("boundary_id") in boundary_ids and item.get("evidence_ids") for item in plan["ports"]),
        "no_unresolved_core_items": not ir["unresolved_items"] and not plan["unresolved_core_items"],
    }
    failures = [name for name, passed in checks.items() if not passed]
    return {"passed": not failures, "status": "PASSED" if not failures else "BLOCKED_WITH_REPORT", "checks": checks, "metrics": {"public_api_count": len(api_ids), "contract_count": len(ir["api_contracts"]), "type_count": len(expected_types), "shared_state_count": len(expected_states), "call_edge_count": len(expected_edges), "transition_count": len(ir["transitions"]), "semantic_invariant_count": len(ir["invariants"]), "boundary_count": len(boundary_ids)}, "failures": failures, "first_blocking_point": None if not failures else "SEMANTIC_MIGRATION_PLANNING"}


def build_semantic_plan(docs: Mapping[str, Dict[str, Any]], run_id: str | None = None) -> Dict[str, Any]:
    ir = _build_ir(docs)
    plan = _build_plan(docs, ir)
    artifacts = {"semantic-ir": ir, "behavior-contracts.json": {"contracts": ir["api_contracts"], "resources": ir["resources"], "effects": ir["effects"], "errors": ir["errors"]}, "state-transitions.json": {"transitions": ir["transitions"]}, "semantic-invariants.json": {"invariants": ir["invariants"]}, "rust-migration-plan.json": {**plan, "external_boundaries": ir["external_boundaries"]}}
    verification = validate_plan(docs, artifacts)
    artifacts["semantic-planning-verification.json"] = verification
    parent = docs["public-api-map.json"]
    metadata = {"schema_version": SCHEMA_VERSION, "run_id": run_id or uuid.uuid4().hex, "parent_analysis_run_id": parent["run_id"], "source_digest": parent["source_digest"], "semantic_ir_digest": _digest(ir), "input_digest": _digest({name: {key: value for key, value in doc.items() if key != "run_id"} for name, doc in sorted(docs.items())})}
    return {"metadata": metadata, "artifacts": artifacts, "verification": verification}


def validate_planning_documents(trace_dir: Path) -> List[str]:
    failures, docs = [], []
    for name in OUTPUT_FILES:
        path = trace_dir / name
        if not path.is_file():
            failures.append(f"missing_planning_evidence:{name}")
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            failures.append(f"invalid_planning_json:{name}")
            continue
        if doc.get("schema_version") in LEGACY_SCHEMA_VERSIONS:
            failures.append(f"legacy_planning_schema_requires_replan:{name}")
        elif doc.get("schema_version") != SCHEMA_VERSION:
            failures.append(f"invalid_planning_schema:{name}")
        docs.append(doc)
    for field in ("run_id", "parent_analysis_run_id", "source_digest", "semantic_ir_digest", "input_digest"):
        if len({doc.get(field) for doc in docs}) != 1 or any(not doc.get(field) for doc in docs):
            failures.append(f"mixed_or_missing_planning_metadata:{field}")
    return sorted(set(failures))


def write_semantic_plan(bundle: Mapping[str, Any], trace_dir: Path) -> None:
    trace_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="semantic-plan-", dir=str(trace_dir.parent)) as temp:
        stage = Path(temp)
        for name in OUTPUT_FILES:
            (stage / name).write_text(json.dumps({**bundle["metadata"], **bundle["artifacts"][name]}, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
        failures = validate_planning_documents(stage)
        if failures:
            raise PlanningBlocked(failures)
        for name in OUTPUT_FILES:
            os.replace(stage / name, trace_dir / name)


def plan_from_trace(trace_dir: Path) -> Dict[str, Any]:
    bundle = build_semantic_plan(load_analysis_evidence(trace_dir))
    if not bundle["verification"]["passed"]:
        raise PlanningBlocked(bundle["verification"]["failures"])
    write_semantic_plan(bundle, trace_dir)
    failures = validate_planning_documents(trace_dir)
    if failures:
        raise PlanningBlocked(failures)
    return bundle["verification"]
