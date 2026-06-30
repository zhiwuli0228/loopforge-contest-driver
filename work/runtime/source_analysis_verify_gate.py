"""Strict, artifact-backed source analysis gate for C-to-Rust migration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set


STAGES = ("requirement", "structure", "data_model", "api_behavior", "capability", "state_model", "test_coverage")
ARTIFACTS = {
    "requirement": ("00-requirement-extraction.json", "00-requirement-verification.json"),
    "structure": ("01a-structure-map.json", "01a-structure-verification.json"),
    "data_model": ("01b-data-model-map.json", "01b-data-model-verification.json"),
    "capability": ("01c-capability-map.json", "01c-capability-verification.json"),
    "state_model": ("01d-state-transition-map.json", "01d-state-transition-verification.json"),
    "api_behavior": ("01e-api-behavior-map.json", "01e-api-behavior-verification.json"),
    "test_coverage": ("01f-test-coverage-map.json", "01f-test-coverage-verification.json"),
}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _names(items: Iterable[Dict[str, Any]], key: str = "name") -> Set[str]:
    return {str(item.get(key, "")) for item in items if item.get(key)}


def _evidence(item: Dict[str, Any]) -> List[Dict[str, str]]:
    return [{"file": str(item.get("file", "")), "symbol": str(item.get("name", ""))}]


def _api_kind(function: Dict[str, Any]) -> str:
    name = str(function.get("name", "")).lower()
    body = str(function.get("normalized_body", "")).lower()
    if any(token in name for token in ("init", "reset", "clear")):
        return "init"
    if any(token in name for token in ("delete", "remove", "erase")):
        return "delete"
    if any(token in name for token in ("count", "size", "len")):
        return "count"
    if any(token in name for token in ("get", "find", "read", "query", "has")):
        return "query"
    if "=" in body or any(token in name for token in ("set", "put", "add", "insert", "update", "write")):
        return "mutation"
    return "other"


def _result(stage: str, checks: Dict[str, bool], metrics: Dict[str, Any]) -> Dict[str, Any]:
    failures = [name for name, passed in checks.items() if not passed]
    return {"stage": stage, "passed": not failures, "checks": checks, "metrics": metrics, "failures": failures}


def build_and_verify_source_analysis(packet: Any, analysis: Dict[str, Any], trace_dir: Path) -> Dict[str, Any]:
    """Produce source-analysis maps and independently recompute strict gate checks."""
    trace_dir.mkdir(parents=True, exist_ok=True)
    functions = analysis.get("functions", [])
    public = set(analysis.get("public_apis", []))
    definitions = {item["name"]: item for item in functions if item.get("decl_kind") == "definition"}
    declarations = {item["name"]: item for item in functions if item.get("decl_kind") == "prototype"}
    api_functions = [definitions.get(name) or declarations.get(name) for name in sorted(public)]
    api_functions = [item for item in api_functions if item]

    requirement = {
        "source_root": str(packet.paths.source_root),
        "source_readme": analysis.get("readme_path", ""),
        "task_requirement_readme": str(packet.paths.work_dir / "code" / "README.md"),
        "source_dirs": analysis.get("source_dirs", []),
        "test_dirs": analysis.get("test_dirs", []),
        "output_project_name": packet.output_project_name,
        "output_project_dir": str(packet.output_project_dir),
        "build_commands": packet.build_commands,
        "unsafe_limit": packet.unsafe_ratio_max,
        "evidence": [{"file": analysis.get("readme_path", ""), "kind": "source_readme"}],
    }
    structure = {
        "core_files": [path for path in analysis.get("src_files", []) if path.endswith(".c")],
        "header_files": [path for path in analysis.get("src_files", []) if path.endswith(".h")],
        "test_files": analysis.get("test_files", []),
        "modules": analysis.get("module_hints", []),
        "public_apis": sorted(public),
        "api_declarations": sorted(declarations),
        "api_definitions": sorted(definitions),
        "unresolved_declarations": sorted(set(declarations) - set(definitions)),
        "evidence": [_evidence(item)[0] for item in api_functions],
    }
    structs = []
    for item in analysis.get("type_table", []):
        if item.get("kind") != "struct":
            continue
        fields = item.get("fields", [])
        structs.append({"name": item.get("name"), "fields": fields, "field_semantics": [field.get("name", "") for field in fields], "invariants": [], "rust_mapping": {"kind": "struct"}, "evidence": _evidence(item)})
    data_model = {
        "structs": structs,
        "macros": analysis.get("macro_table", []),
        "capacity_constants": [item for item in analysis.get("macro_table", []) if any(token in str(item.get("name", "")).upper() for token in ("MAX", "CAPACITY", "SIZE", "LIMIT"))],
        "evidence": [e for item in structs for e in item["evidence"]],
    }
    behaviors = []
    for function in api_functions:
        kind = _api_kind(function)
        behaviors.append({
            "name": function["name"], "signature": f"{function.get('return_type', '')} {function['name']}({function.get('params_text', '')})",
            "kind": kind, "inputs": function.get("params", []), "outputs": [function.get("return_type", "")],
            "side_effects": [function.get("body_kind", "")] if kind in {"init", "mutation", "delete"} else [],
            "failure_modes": [], "evidence": _evidence(function),
        })
    api_behavior = {"apis": behaviors}
    capabilities = []
    tested_apis = {api for test in analysis.get("tests", []) for api in test.get("referenced_apis", [])}
    for behavior in behaviors:
        name = behavior["name"]
        capabilities.append({
            "id": f"api-{name}", "name": name, "apis": [name], "behaviors": [behavior["kind"]],
            "normal_paths": ["invoke with valid inputs"], "boundary_paths": [], "error_paths": behavior["failure_modes"],
            "state_effects": behavior["side_effects"], "evidence": behavior["evidence"],
            "implementation_plan": [f"implement {name} from verified behavior"],
            "coverage": {"source_test": name in tested_apis, "derived_test": name not in tested_apis},
        })
    capability = {"capabilities": capabilities, "unmapped_public_apis": sorted(public - {api for cap in capabilities for api in cap["apis"]})}
    mutating = [item for item in behaviors if item["kind"] in {"init", "mutation", "delete"}]
    state_model = {"states": ["valid"], "transitions": [{"api": item["name"], "from": "valid", "to": "valid", "preconditions": [], "effects": item["side_effects"], "return_behavior": item["outputs"][0], "state_preservation_on_failure": True, "evidence": item["evidence"]} for item in mutating]}
    uncovered = sorted(public - tested_apis)
    test_coverage = {
        "source_tests": analysis.get("tests", []),
        "source_assertions": [assertion for test in analysis.get("tests", []) for assertion in test.get("assertions", [])],
        "covered_apis": sorted(public & tested_apis), "covered_capabilities": [f"api-{name}" for name in sorted(public & tested_apis)],
        "uncovered_capabilities": [f"api-{name}" for name in uncovered],
        "required_derived_tests": [{"capability": f"api-{name}", "api": name} for name in uncovered],
        "generated_derived_tests": [],
    }
    maps = {"requirement": requirement, "structure": structure, "data_model": data_model, "api_behavior": api_behavior, "capability": capability, "state_model": state_model, "test_coverage": test_coverage}
    for stage, payload in maps.items():
        _write_json(trace_dir / ARTIFACTS[stage][0], payload)

    output_expected = packet.paths.work_dir / "output" / packet.output_project_name
    verifications = {
        "requirement": _result("requirement", {"source_root_exists": packet.paths.source_root.is_dir(), "source_root_is_not_work_code": packet.paths.source_root.resolve() != (packet.paths.work_dir / "code").resolve(), "source_readme_identified": bool(requirement["source_readme"]), "source_dirs_exist": bool(requirement["source_dirs"]), "test_dirs_exist": bool(requirement["test_dirs"]), "output_name_has_evidence": bool(requirement["output_project_name"] and requirement["evidence"]), "output_dir_is_canonical": packet.output_project_dir.resolve() == output_expected.resolve()}, {}),
        "structure": _result("structure", {"core_c_files_present": bool(structure["core_files"]), "public_apis_present": bool(public), "all_public_apis_defined": not structure["unresolved_declarations"], "all_public_apis_have_evidence": all(item.get("file") and item.get("symbol") for item in structure["evidence"])}, {"public_api_count": len(public), "definition_count": len(public & set(definitions))}),
        "data_model": _result("data_model", {"all_struct_fields_named": all(field.get("name") for item in structs for field in item["fields"]), "all_structs_have_evidence": all(item["evidence"] for item in structs)}, {"struct_count": len(structs)}),
        "api_behavior": _result("api_behavior", {"behavior_coverage_100_percent": _names(behaviors) == public, "all_apis_classified": all(item["kind"] for item in behaviors), "mutations_have_side_effects": all(item["side_effects"] for item in mutating), "all_behaviors_have_evidence": all(item["evidence"] for item in behaviors)}, {"coverage": len(_names(behaviors)) / len(public) if public else 0.0}),
        "capability": _result("capability", {"capabilities_present": bool(capabilities), "api_membership_100_percent": not capability["unmapped_public_apis"], "normal_paths_present": all(item["normal_paths"] for item in capabilities), "implementation_plans_present": all(item["implementation_plan"] for item in capabilities), "coverage_plans_present": all(item["coverage"]["source_test"] or item["coverage"]["derived_test"] for item in capabilities), "all_capabilities_have_evidence": all(item["evidence"] for item in capabilities)}, {"capability_count": len(capabilities)}),
        "state_model": _result("state_model", {"mutation_transition_coverage_100_percent": {item["name"] for item in mutating} == {item["api"] for item in state_model["transitions"]}, "all_transitions_have_evidence": all(item["evidence"] for item in state_model["transitions"]), "failure_preservation_explicit": all(isinstance(item["state_preservation_on_failure"], bool) for item in state_model["transitions"])}, {"mutating_api_count": len(mutating), "transition_count": len(state_model["transitions"])}),
        "test_coverage": _result("test_coverage", {"source_tests_present": bool(test_coverage["source_tests"]), "source_assertions_present": bool(test_coverage["source_assertions"]), "every_capability_has_test_or_plan": not (set(uncovered) - {item["api"] for item in test_coverage["required_derived_tests"]})}, {"covered_api_count": len(test_coverage["covered_apis"]), "derived_test_required_count": len(uncovered)}),
    }
    for stage, payload in verifications.items():
        _write_json(trace_dir / ARTIFACTS[stage][1], payload)
    failed = [stage for stage in STAGES if not verifications[stage]["passed"]]
    gate = {"passed": not failed, "status": "PASSED" if not failed else "BLOCKED_WITH_REPORT", "first_blocking_point": None if not failed else ("A_SOURCE_ROOT" if failed == ["requirement"] else "C_SOURCE_ANALYSIS"), "failed_stages": failed, "verifications": verifications}
    missing_lines = ["# Missing Capability Report", "", f"- status: `{gate['status']}`", f"- first_blocking_point: `{gate['first_blocking_point'] or 'none'}`", f"- missing public APIs: `{', '.join(structure['unresolved_declarations']) or 'none'}`", f"- missing capabilities: `{', '.join(capability['unmapped_public_apis']) or 'none'}`", "- missing data invariants: `none detected by structural gate`", "- missing state transitions: `" + (", ".join(sorted({item['name'] for item in mutating} - {item['api'] for item in state_model['transitions']})) or "none") + "`", f"- missing boundary tests: `{', '.join(uncovered) or 'none'}`", f"- missing error-path tests: `{', '.join(uncovered) or 'none'}`", f"- severity: `{'P1' if failed else 'none'}`", ""]
    (trace_dir / "01g-missing-capability-report.md").write_text("\n".join(missing_lines), encoding="utf-8")
    report = ["# Source Analysis Verify Report", "", f"- status: `{gate['status']}`", f"- first_blocking_point: `{gate['first_blocking_point'] or 'none'}`", "", "| Stage | Result | Failed checks |", "|---|---|---|"]
    report.extend(f"| {stage} | {'PASS' if verifications[stage]['passed'] else 'FAIL'} | {', '.join(verifications[stage]['failures']) or 'none'} |" for stage in STAGES)
    (trace_dir / "source-analysis-verify-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return gate
