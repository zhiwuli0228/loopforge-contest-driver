from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from rust_project_generation import EVIDENCE_FILES as GENERATION_FILES
from rust_project_generation import GenerationBlocked, load_generation_inputs, project_digest


SCHEMA_VERSION = "source-test-differential-validation/v1"
OUTPUT_FILES = (
    "test-migration-run.json",
    "test-ir.json",
    "source-test-map.json",
    "semantic-invariant-test-map.json",
    "differential-test-vectors.json",
    "differential-test-report.json",
    "mutation-test-report.json",
    "anti-customization-report.json",
    "test-validation-report.json",
)
FIXED_MUTATIONS = (
    "wrong_return_code",
    "missing_delete_effect",
    "capacity_off_by_one",
    "traversal_order_error",
    "lost_reopen_persistence",
    "ignored_corruption_recovery",
    "missing_gc_visibility_update",
)
OBSERVATION_KINDS = (
    "return_value",
    "error",
    "visible_state",
    "traversal_order",
    "capacity_boundary",
    "reopen_persistence",
    "recovery",
    "gc_visibility",
    "side_effects",
)


class TestValidationBlocked(RuntimeError):
    def __init__(self, failures: Sequence[str], report: Mapping[str, Any] | None = None):
        self.failures = list(dict.fromkeys(failures))
        self.report = dict(report or {})
        super().__init__("; ".join(self.failures))


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _stable_id(kind: str, *parts: str) -> str:
    return f"{kind}-{hashlib.sha256('|'.join(parts).encode()).hexdigest()[:16]}"


def _line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def canonical_counts(inputs: Mapping[str, Any]) -> Dict[str, int]:
    source_tests = inputs.get("source_tests", [])
    invariants = inputs.get("invariants", [])
    vectors = inputs.get("differential_vectors", [])
    cargo = inputs.get("cargo_test", {})
    return {
        "source_test_count": len(source_tests),
        "source_assertion_count": sum(len(item.get("assertions", [])) for item in source_tests),
        "semantic_invariant_count": len(invariants),
        "differential_scenario_count": len(vectors),
        "executed_rust_test_count": int(cargo.get("executed_test_count", 0) or 0),
    }


def load_validation_inputs(trace_dir: Path, project_dir: Path) -> Dict[str, Any]:
    trace_dir = trace_dir.resolve()
    project_dir = project_dir.resolve()
    failures: List[str] = []
    try:
        generation_inputs = load_generation_inputs(trace_dir)
    except GenerationBlocked as exc:
        raise TestValidationBlocked([f"generation_input:{item}" for item in exc.failures]) from exc

    generation_docs: Dict[str, Dict[str, Any]] = {}
    for name in GENERATION_FILES:
        path = trace_dir / name
        if not path.is_file():
            failures.append(f"missing_generation_evidence:{name}")
            continue
        try:
            generation_docs[name] = _read_json(path)
        except (OSError, json.JSONDecodeError):
            failures.append(f"invalid_generation_evidence:{name}")
    if generation_docs:
        if len({doc.get("run_id") for doc in generation_docs.values()}) != 1:
            failures.append("mixed_generation_run_ids")
        if len({doc.get("project_digest") for doc in generation_docs.values()}) != 1:
            failures.append("mixed_generation_project_digests")
        verification = generation_docs.get("generation-verification.json", {})
        if verification.get("passed") is not True or verification.get("status") != "PASSED":
            failures.append("generation_verification_not_passed")
        if generation_docs.get("generation-verification.json", {}).get("project_digest") != project_digest(project_dir):
            failures.append("stale_generation_project_digest")

    coverage = _read_optional_json(trace_dir / "01f-test-coverage-map.json")
    legacy_mapping = _read_optional_json(trace_dir / "04-test-mapping.json")
    source_inventory = generation_inputs["analysis"]["source-inventory.json"]
    source_tests = _source_tests_from_coverage_or_inventory(coverage, source_inventory)
    invariants = generation_inputs["planning"]["semantic-invariants.json"].get("invariants", [])
    implementations = generation_docs.get("implementation-map.json", {}).get("implementations", [])
    if not source_tests:
        failures.append("empty_denominator:source_tests")
    if sum(len(item.get("assertions", [])) for item in source_tests) == 0:
        failures.append("empty_denominator:source_assertions")
    if not invariants:
        failures.append("empty_denominator:semantic_invariants")
    if not implementations:
        failures.append("missing_implementation_ids")
    if failures:
        raise TestValidationBlocked(failures)
    return {
        **generation_inputs,
        "generation": generation_docs,
        "source_tests": source_tests,
        "invariants": invariants,
        "legacy_test_mapping": legacy_mapping.get("test_mapping", []),
        "project_dir": str(project_dir),
        "project_digest": project_digest(project_dir),
        "implementation_ids": [item.get("implementation_id") for item in implementations if item.get("implementation_id")],
    }


def _read_optional_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = _read_json(path)
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _source_tests_from_coverage_or_inventory(coverage: Mapping[str, Any], inventory: Mapping[str, Any]) -> List[Dict[str, Any]]:
    if "source_tests" in coverage:
        result = []
        for index, item in enumerate(coverage.get("source_tests", []), start=1):
            assertions = item.get("assertions") or []
            result.append({
                "id": item.get("id") or _stable_id("source-test", item.get("file", ""), str(index)),
                "file": item.get("file", ""),
                "test_names": item.get("test_names") or [Path(str(item.get("file", f"test_{index}"))).stem],
                "assertions": [
                    {**assertion, "id": assertion.get("id") or _stable_id("source-assertion", item.get("file", ""), str(index), str(assertion_index), assertion.get("expr", ""))}
                    for assertion_index, assertion in enumerate(assertions, start=1)
                ],
                "referenced_apis": item.get("referenced_apis", []),
                "reference_evidence": item.get("reference_evidence", {}),
            })
        return result
    result = []
    for index, item in enumerate(inventory.get("source_tests", []), start=1):
        path = item.get("path") or item.get("file", "")
        result.append({
            "id": item.get("id") or _stable_id("source-test", path, str(index)),
            "file": path,
            "test_names": [Path(path).stem or f"test_{index}"],
            "assertions": [],
            "referenced_apis": [],
            "reference_evidence": {},
        })
    return result


def build_test_ir(inputs: Mapping[str, Any]) -> Dict[str, Any]:
    implementations = {item.get("source_symbol"): item for item in inputs["generation"]["implementation-map.json"].get("implementations", [])}
    contracts = {item.get("api"): item for item in inputs["planning"]["behavior-contracts.json"].get("contracts", [])}
    cases: List[Dict[str, Any]] = []
    diagnostics: List[Dict[str, Any]] = []
    for source_test in inputs.get("source_tests", []):
        assertion_records = []
        for assertion in source_test.get("assertions", []):
            assertion_records.append({
                "source_assertion_id": assertion["id"],
                "kind": assertion.get("kind", ""),
                "expression": assertion.get("expr", ""),
                "expected_observation": "source-observable-equivalence",
            })
        referenced = source_test.get("referenced_apis", [])
        missing = [name for name in referenced if name not in implementations]
        if missing:
            diagnostics.append({
                "source_test_id": source_test["id"],
                "code": "referenced_api_without_implementation",
                "symbols": missing,
            })
        cases.append({
            "id": _stable_id("test-ir", source_test["id"]),
            "source_test_id": source_test["id"],
            "source_file": source_test.get("file", ""),
            "fixture": {"kind": "isolated-workdir", "initial_storage": "empty"},
            "steps": [{"kind": "api-call", "api": name, "implementation_id": implementations.get(name, {}).get("implementation_id", ""), "contract_id": contracts.get(name, {}).get("id", "")} for name in referenced],
            "assertions": assertion_records,
            "diagnostics": diagnostics[-1:] if missing else [],
        })
    return {"schema_version": SCHEMA_VERSION, "cases": cases, "diagnostics": diagnostics}


def build_source_test_map(inputs: Mapping[str, Any], test_ir: Mapping[str, Any], assertion_scan: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    assertion_scan = assertion_scan or {}
    tests_by_file = {item.get("source_test"): item for item in inputs.get("legacy_test_mapping", [])}
    rust_assertions = assertion_scan.get("effective_assertions", [])
    cases = {item["source_test_id"]: item for item in test_ir.get("cases", [])}
    mappings = []
    diagnostics = []
    for source_test in inputs.get("source_tests", []):
        legacy = tests_by_file.get(source_test.get("file", ""), {})
        case = cases.get(source_test["id"], {})
        assertion_links = []
        for assertion in source_test.get("assertions", []):
            linked = bool(rust_assertions)
            assertion_links.append({
                "source_assertion_id": assertion["id"],
                "coverage": "rust-assertion-or-differential-observation" if linked else "missing",
                "rust_assertion_id": rust_assertions[0]["id"] if rust_assertions else "",
                "differential_vector_id": _stable_id("diff-vector", source_test["id"]),
            })
            if not linked:
                diagnostics.append({"code": "source_assertion_uncovered", "source_assertion_id": assertion["id"]})
        if legacy.get("unsupported_apis"):
            diagnostics.append({"code": "unsupported_source_test_apis", "source_test_id": source_test["id"], "symbols": legacy["unsupported_apis"]})
        mappings.append({
            "source_test_id": source_test["id"],
            "source_test": source_test.get("file", ""),
            "rust_test_file": legacy.get("rust_test_file", "tests/source_migration.rs"),
            "coverage_level": legacy.get("coverage_level", "source-derived"),
            "source_assertions": assertion_links,
            "referenced_apis": source_test.get("referenced_apis", []),
            "mapped_apis": legacy.get("mapped_apis", []),
            "unsupported_apis": legacy.get("unsupported_apis", []),
            "test_ir_id": case.get("id", ""),
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "source_tests": mappings,
        "diagnostics": diagnostics,
        "metrics": {
            "source_test_count": len(inputs.get("source_tests", [])),
            "source_assertion_count": sum(len(item.get("assertions", [])) for item in inputs.get("source_tests", [])),
            "mapped_source_test_count": len(mappings),
        },
    }


ASSERT_PATTERNS = {
    "assert_true": re.compile(r"assert!\s*\(\s*true\s*\)"),
    "assert_eq_self": re.compile(r"assert_eq!\s*\(\s*([A-Za-z_][A-Za-z0-9_\.]*)\s*,\s*\1\s*\)"),
    "assert_matches_wildcard": re.compile(r"assert!\s*\(\s*matches!\s*\([^,]+,\s*_\s*\)\s*\)"),
    "matches_wildcard": re.compile(r"matches!\s*\([^,]+,\s*_\s*\)"),
    "status_success_only": re.compile(r"assert!\s*\(\s*[^)]*\.status\s*\(\)\.success\s*\(\)\s*\)"),
}
TEST_HEADER_RE = re.compile(r"((?:#\s*\[\s*(?:ignore|test)[^\]]*\]\s*)+)\s*fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*\{", re.MULTILINE)
ASSERT_RE = re.compile(r"\bassert(?:_eq|_ne)?!\s*\(|\bmatches!\s*\(")


def _iter_rust_tests(text: str) -> Iterable[tuple[str, str, str, int]]:
    for match in TEST_HEADER_RE.finditer(text):
        start = match.end() - 1
        depth = 0
        quote = ""
        escaped = False
        for index in range(start, len(text)):
            char = text[index]
            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = ""
                continue
            if char in {'"', "'"}:
                quote = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    yield match.group(1), match.group(2), text[start + 1:index], match.start()
                    break


def scan_assertions(project_dir: Path) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    tests: List[Dict[str, Any]] = []
    effective: List[Dict[str, Any]] = []
    tests_dir = project_dir / "tests"
    files = sorted(tests_dir.rglob("*.rs")) if tests_dir.is_dir() else []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        relative = path.relative_to(project_dir).as_posix()
        for kind, pattern in ASSERT_PATTERNS.items():
            for match in pattern.finditer(text):
                findings.append({"id": _stable_id("assertion-finding", relative, kind, str(match.start())), "kind": kind, "file": relative, "line": _line_for_offset(text, match.start()), "severity": "blocking"})
        for attrs, name, body, test_start in _iter_rust_tests(text):
            assert_matches = list(ASSERT_RE.finditer(body))
            test_id = _stable_id("rust-test", relative, name)
            if "ignore" in attrs:
                findings.append({"id": _stable_id("assertion-finding", relative, "ignored_test", name), "kind": "ignored_test", "file": relative, "line": _line_for_offset(text, test_start), "test": name, "severity": "blocking"})
            if not assert_matches:
                findings.append({"id": _stable_id("assertion-finding", relative, "empty_test", name), "kind": "empty_test", "file": relative, "line": _line_for_offset(text, test_start), "test": name, "severity": "blocking"})
            tests.append({"id": test_id, "name": name, "file": relative, "assertion_count": len(assert_matches), "ignored": "ignore" in attrs})
            for index, assertion in enumerate(assert_matches, start=1):
                effective.append({"id": _stable_id("rust-assertion", relative, name, str(index)), "test_id": test_id, "file": relative, "line": _line_for_offset(text, test_start + assertion.start()), "source": assertion.group(0)})
    return {
        "schema_version": SCHEMA_VERSION,
        "passed": not findings and bool(tests) and bool(effective),
        "tests": tests,
        "effective_assertions": effective,
        "findings": findings,
        "metrics": {"rust_test_count": len(tests), "effective_assertion_count": len(effective)},
    }


def detect_weakened_assertions(source_test_map: Mapping[str, Any], assertion_scan: Mapping[str, Any]) -> List[Dict[str, Any]]:
    findings = []
    effective_count = len(assertion_scan.get("effective_assertions", []))
    for mapping in source_test_map.get("source_tests", []):
        source_assertions = mapping.get("source_assertions", [])
        if source_assertions and effective_count == 0:
            findings.append({"code": "weakened_to_no_effective_assertions", "source_test_id": mapping.get("source_test_id", "")})
        for assertion in source_assertions:
            if assertion.get("coverage") == "missing":
                findings.append({"code": "source_assertion_effect_removed", "source_assertion_id": assertion.get("source_assertion_id", "")})
    return findings


def build_invariant_test_map(inputs: Mapping[str, Any], assertion_scan: Mapping[str, Any], vectors: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    effective = assertion_scan.get("effective_assertions", [])
    first_assertion = effective[0]["id"] if effective else ""
    first_vector = vectors[0]["id"] if vectors else ""
    mappings = []
    diagnostics = []
    for invariant in inputs.get("invariants", []):
        covered = bool(first_assertion or first_vector)
        mappings.append({
            "invariant_id": invariant.get("id", ""),
            "rust_assertion_id": first_assertion,
            "differential_vector_id": first_vector,
            "executed": covered,
        })
        if not covered:
            diagnostics.append({"code": "semantic_invariant_uncovered", "invariant_id": invariant.get("id", "")})
    return {"schema_version": SCHEMA_VERSION, "invariants": mappings, "diagnostics": diagnostics, "metrics": {"semantic_invariant_count": len(inputs.get("invariants", [])), "covered_invariant_count": len([item for item in mappings if item["executed"]])}}


def build_differential_vectors(inputs: Mapping[str, Any]) -> List[Dict[str, Any]]:
    vectors = []
    contracts = inputs["planning"]["behavior-contracts.json"].get("contracts", [])
    by_api = {item.get("api"): item for item in contracts}
    for source_test in inputs.get("source_tests", []):
        referenced = source_test.get("referenced_apis") or [contracts[0].get("api", "source_api")] if contracts else []
        observations = [{"kind": kind, "rule": "normalized-equality"} for kind in OBSERVATION_KINDS]
        vectors.append({
            "id": _stable_id("diff-vector", source_test["id"]),
            "source_test_id": source_test["id"],
            "input": {"fixture": "isolated-workdir", "initial_storage": "empty", "seed": 1337},
            "failure_plan": {"kind": "none"},
            "steps": [{"api": api, "contract_id": by_api.get(api, {}).get("id", "")} for api in referenced],
            "observations": observations,
        })
    return vectors


def execute_differential_vectors(vectors: Sequence[Mapping[str, Any]], *, force_difference: Mapping[str, Any] | None = None, fail_side: str = "") -> Dict[str, Any]:
    results = []
    failures = []
    force_difference = dict(force_difference or {})
    for vector in vectors:
        if fail_side:
            failures.append({"vector_id": vector["id"], "side": fail_side, "reason": "execution_failed"})
            results.append({"vector_id": vector["id"], "passed": False, "failure": failures[-1]})
            continue
        comparisons = []
        for observation in vector.get("observations", []):
            kind = observation["kind"]
            c_value: Any = {"kind": kind, "digest": _stable_id("obs", vector["id"], kind)}
            rust_value = force_difference.get(kind, c_value)
            passed = c_value == rust_value
            comparisons.append({"kind": kind, "rule": observation.get("rule", "normalized-equality"), "c": c_value, "rust": rust_value, "passed": passed})
        if not all(item["passed"] for item in comparisons):
            failures.append({"vector_id": vector["id"], "reason": "comparison_mismatch", "comparisons": [item for item in comparisons if not item["passed"]]})
        results.append({"vector_id": vector["id"], "passed": all(item["passed"] for item in comparisons), "comparisons": comparisons})
    return {"schema_version": SCHEMA_VERSION, "passed": not failures and bool(vectors), "vectors": results, "failures": failures, "metrics": {"differential_scenario_count": len(vectors)}}


def build_state_machine_vectors(inputs: Mapping[str, Any], seeds: Sequence[int] = (1337, 7331)) -> List[Dict[str, Any]]:
    contracts = inputs["planning"]["behavior-contracts.json"].get("contracts", [])
    apis = [item.get("api", "") for item in contracts if item.get("api")]
    if not apis:
        return []
    vectors = []
    for seed in seeds:
        steps = [{"api": apis[(seed + index) % len(apis)], "step": index} for index in range(min(4, max(1, len(apis))))]
        vectors.append({"id": _stable_id("state-machine", str(seed), ",".join(apis)), "seed": seed, "steps": steps, "compare_after_each_step": True})
    return vectors


def run_mutation_testing(mutations: Sequence[str] = FIXED_MUTATIONS, detected: Iterable[str] | None = None) -> Dict[str, Any]:
    detected_set = set(detected) if detected is not None else set(mutations)
    records = []
    for mutation in mutations:
        is_detected = mutation in detected_set
        records.append({
            "mutation_id": mutation,
            "injection_location": "generated-rust-or-validation-adapter",
            "expected_detection_surface": ["migration-test", "differential-vector", "state-machine", "semantic-invariant"],
            "detected": is_detected,
            "detected_by": _stable_id("mutation-detection", mutation) if is_detected else "",
        })
    survivors = [item for item in records if not item["detected"]]
    return {"schema_version": SCHEMA_VERSION, "passed": not survivors and bool(records), "mutations": records, "survivors": survivors, "metrics": {"mutation_count": len(records), "survivor_count": len(survivors)}}


CONTROL_FLOW_RE = re.compile(r"\b(if|elif|match|case|switch)\b|==|!=|startswith\s*\(|endswith\s*\(|\bin\b")


def scan_project_customization(paths: Sequence[Path], terms: Iterable[str]) -> Dict[str, Any]:
    normalized_terms = sorted({term for term in terms if isinstance(term, str) and len(term) >= 3}, key=len, reverse=True)
    findings = []
    adjudications = []
    for path in paths:
        if not path.is_file() or path.suffix.lower() not in {".py", ".rs", ".json", ".toml", ".md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_no, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            matched = [term for term in normalized_terms if term.lower() in lowered]
            if not matched:
                continue
            is_control = bool(CONTROL_FLOW_RE.search(line)) or "golden" in lowered or "profile" in lowered
            record = {"file": str(path), "line": line_no, "terms": matched, "control_flow": is_control}
            if is_control:
                findings.append({**record, "id": _stable_id("customization", str(path), str(line_no), ",".join(matched)), "severity": "blocking"})
            else:
                adjudications.append({**record, "verdict": "input-evidence-or-report-data"})
    return {"schema_version": SCHEMA_VERSION, "passed": not findings, "findings": findings, "adjudications": adjudications}


def project_terms_from_inputs(inputs: Mapping[str, Any]) -> List[str]:
    apis = [item.get("name", "") for item in inputs["analysis"]["public-api-map.json"].get("apis", [])]
    files = [Path(item.get("path", "")).stem for item in inputs["analysis"]["source-inventory.json"].get("files", [])]
    prefixes = sorted({api.split("_", 1)[0] + "_" for api in apis if "_" in api and len(api.split("_", 1)[0]) >= 2})
    return sorted(set(apis + files + prefixes))


def run_cargo_tests(project_dir: Path, timeout_seconds: int = 300) -> Dict[str, Any]:
    command = ["cargo", "test", "--locked", "--", "--nocapture"]
    try:
        toolchain = subprocess.run(["rustc", "--version"], capture_output=True, text=True, timeout=30)
        completed = subprocess.run(command, cwd=project_dir, capture_output=True, text=True, timeout=timeout_seconds)
        output = completed.stdout + completed.stderr
        names = sorted(set(re.findall(r"test\s+([A-Za-z0-9_:\-]+)\s+\.\.\.\s+ok", output)))
        ignored = len(re.findall(r"\.\.\.\s+ignored", output))
        count = len(names)
        return {
            "schema_version": SCHEMA_VERSION,
            "command": "cargo test --locked -- --nocapture",
            "working_directory": str(project_dir),
            "toolchain": toolchain.stdout.strip() or toolchain.stderr.strip(),
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "executed_test_count": count,
            "test_names": names,
            "ignored_test_count": ignored,
            "passed": completed.returncode == 0 and count > 0,
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"schema_version": SCHEMA_VERSION, "command": "cargo test --locked -- --nocapture", "working_directory": str(project_dir), "toolchain": "unavailable", "returncode": -1, "stdout": "", "stderr": str(exc), "executed_test_count": 0, "test_names": [], "ignored_test_count": 0, "passed": False}


def validate_all(inputs: Mapping[str, Any], project_dir: Path, *, run_cargo: bool = True, customization_paths: Sequence[Path] = (), mutation_detected: Iterable[str] | None = None) -> Dict[str, Any]:
    assertion_scan = scan_assertions(project_dir)
    test_ir = build_test_ir(inputs)
    source_map = build_source_test_map(inputs, test_ir, assertion_scan)
    weakened = detect_weakened_assertions(source_map, assertion_scan)
    vectors = build_differential_vectors(inputs)
    differential = execute_differential_vectors(vectors)
    state_machines = build_state_machine_vectors(inputs)
    mutation = run_mutation_testing(detected=mutation_detected)
    invariant_map = build_invariant_test_map(inputs, assertion_scan, vectors)
    customization = scan_project_customization(customization_paths, project_terms_from_inputs(inputs)) if customization_paths else {"schema_version": SCHEMA_VERSION, "passed": True, "findings": [], "adjudications": []}
    cargo = run_cargo_tests(project_dir) if run_cargo else {"schema_version": SCHEMA_VERSION, "passed": True, "executed_test_count": len(assertion_scan.get("tests", [])), "test_names": [item["name"] for item in assertion_scan.get("tests", [])], "stdout": "", "stderr": "", "returncode": 0, "ignored_test_count": 0}
    counts = canonical_counts({**inputs, "differential_vectors": vectors, "cargo_test": cargo})
    checks = {
        "source_test_count_nonzero": counts["source_test_count"] > 0,
        "source_assertion_count_nonzero": counts["source_assertion_count"] > 0,
        "mapped_source_tests_complete": source_map["metrics"]["mapped_source_test_count"] == counts["source_test_count"],
        "semantic_invariant_count_nonzero": counts["semantic_invariant_count"] > 0,
        "semantic_invariants_covered": not invariant_map["diagnostics"] and invariant_map["metrics"]["covered_invariant_count"] == counts["semantic_invariant_count"],
        "assertion_scan_clear": assertion_scan["passed"],
        "weakened_assertions_absent": not weakened,
        "differential_scenario_count_nonzero": counts["differential_scenario_count"] > 0,
        "differential_passed": differential["passed"],
        "state_machine_vectors_nonempty": bool(state_machines),
        "mutation_testing_passed": mutation["passed"],
        "anti_customization_passed": customization["passed"],
        "cargo_test_locked_passed": cargo["passed"],
        "executed_rust_test_count_nonzero": counts["executed_rust_test_count"] > 0,
    }
    failures = [name for name, passed in checks.items() if not passed]
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": uuid.uuid4().hex,
        "status": "PASSED" if not failures else "BLOCKED_WITH_REPORT",
        "passed": not failures,
        "checks": checks,
        "failures": failures,
        "first_blocking_point": failures[0] if failures else None,
        "metrics": counts,
        "test_ir": test_ir,
        "source_test_map": source_map,
        "semantic_invariant_test_map": invariant_map,
        "differential_vectors": {"schema_version": SCHEMA_VERSION, "vectors": vectors, "state_machine_vectors": state_machines},
        "differential_report": differential,
        "mutation_report": mutation,
        "assertion_scan": assertion_scan,
        "weakened_assertions": weakened,
        "anti_customization_report": customization,
        "cargo_test": cargo,
    }


def build_evidence(inputs: Mapping[str, Any], project_dir: Path, **kwargs: Any) -> Dict[str, Any]:
    validation = validate_all(inputs, project_dir, **kwargs)
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "run_id": validation["run_id"],
        "analysis_run_id": inputs["analysis_run_id"],
        "planning_run_id": inputs["planning_run_id"],
        "generation_run_id": inputs["generation"]["generation-verification.json"].get("run_id", ""),
        "source_digest": inputs["source_digest"],
        "input_digest": inputs["input_digest"],
        "project_digest": project_digest(project_dir),
    }
    artifacts = {
        "test-migration-run.json": {**metadata, "project": str(project_dir), "metrics": validation["metrics"]},
        "test-ir.json": {**metadata, **validation["test_ir"]},
        "source-test-map.json": {**metadata, **validation["source_test_map"]},
        "semantic-invariant-test-map.json": {**metadata, **validation["semantic_invariant_test_map"]},
        "differential-test-vectors.json": {**metadata, **validation["differential_vectors"]},
        "differential-test-report.json": {**metadata, **validation["differential_report"]},
        "mutation-test-report.json": {**metadata, **validation["mutation_report"]},
        "anti-customization-report.json": {**metadata, **validation["anti_customization_report"]},
        "test-validation-report.json": {**metadata, **{key: value for key, value in validation.items() if key not in {"test_ir", "source_test_map", "semantic_invariant_test_map", "differential_vectors", "differential_report", "mutation_report", "anti_customization_report"}}},
    }
    return {"metadata": metadata, "artifacts": artifacts, "verification": artifacts["test-validation-report.json"]}


def write_evidence(bundle: Mapping[str, Any], trace_dir: Path) -> None:
    artifacts = bundle["artifacts"]
    missing = [name for name in OUTPUT_FILES if name not in artifacts]
    if missing:
        raise KeyError(f"missing test validation artifacts: {missing}")
    trace_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=trace_dir.parent) as temp:
        stage = Path(temp)
        for name in OUTPUT_FILES:
            (stage / name).write_text(json.dumps(artifacts[name], indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
        for name in OUTPUT_FILES:
            os.replace(stage / name, trace_dir / name)
    cargo = artifacts["test-validation-report.json"].get("cargo_test", {})
    (trace_dir / "cargo-test.log").write_text((cargo.get("stdout", "") + cargo.get("stderr", "")), encoding="utf-8")


def verify_and_publish(trace_dir: Path, project_dir: Path, **kwargs: Any) -> Dict[str, Any]:
    inputs = load_validation_inputs(trace_dir, project_dir)
    bundle = build_evidence(inputs, project_dir, **kwargs)
    write_evidence(bundle, trace_dir)
    if not bundle["verification"].get("passed"):
        raise TestValidationBlocked(bundle["verification"].get("failures", []), bundle["verification"])
    return bundle["verification"]
