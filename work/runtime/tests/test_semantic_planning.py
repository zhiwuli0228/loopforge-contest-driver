import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

RUNTIME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME))

from source_analysis import build_complete_analysis, write_complete_analysis  # noqa: E402
from semantic_planning import (  # noqa: E402
    OUTPUT_FILES, SCHEMA_VERSION, PlanningBlocked, build_semantic_plan,
    load_analysis_evidence, plan_from_trace, validate_plan,
    validate_planning_documents, write_semantic_plan,
)

FIXTURE = Path(__file__).parent / "fixtures" / "generic-counter"


def _packet(root):
    return SimpleNamespace(metadata={"layout_resolution": {"source_dirs": [str(root / "src"), str(root / "inc")], "test_dirs": [str(root / "tests")]}})


def _analysis_docs(trace):
    legacy = {"project_root": str(FIXTURE), "public_apis": ["counter_increment"], "test_files": ["tests/test_counter.c"], "functions": [
        {"name": "counter_increment", "decl_kind": "prototype", "file": "inc/counter.h", "line": 4, "return_type": "int", "params": []},
        {"name": "counter_increment", "decl_kind": "definition", "file": "src/counter.c", "line": 4, "return_type": "int", "params": []},
    ]}
    bundle = build_complete_analysis(_packet(FIXTURE), legacy)
    if not bundle["verification"]["passed"]:
        raise AssertionError(bundle["verification"])
    write_complete_analysis(bundle, Path(trace))
    return load_analysis_evidence(Path(trace))


class SemanticPlanningTests(unittest.TestCase):
    def test_plan_is_source_derived_and_has_no_profile_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            plan = build_semantic_plan(_analysis_docs(temp), run_id="run")
        self.assertTrue(plan["verification"]["passed"], plan["verification"])
        self.assertEqual(plan["metadata"]["schema_version"], SCHEMA_VERSION)
        self.assertNotIn("profile_id", plan["metadata"])
        self.assertNotIn("profile_digest", plan["metadata"])
        self.assertTrue(all(item["derivation_kind"] == "source-derived" for item in plan["artifacts"]["semantic-ir"]["api_contracts"]))

    def test_no_bundled_project_profile_or_domain_classifier_exists(self):
        self.assertFalse((RUNTIME / "profiles" / "flashdb-acceptance.json").exists())
        source = (RUNTIME / "semantic_planning.py").read_text(encoding="utf-8")
        for token in ("FDB_OK", "FDB_ERROR", "def _capability_api", "flashdb-acceptance", "if \"kv\" in", "if \"ts\" in"):
            self.assertNotIn(token, source)

    def test_non_database_fixture_gets_no_database_or_device_concepts(self):
        with tempfile.TemporaryDirectory() as temp:
            plan = build_semantic_plan(_analysis_docs(temp))
        encoded = json.dumps(plan["artifacts"]).lower()
        for token in ("kvdb", "tsdb", "sector", "reopen", "flash-port"):
            self.assertNotIn(token, encoded)

    def test_modules_come_from_source_location_not_api_name(self):
        with tempfile.TemporaryDirectory() as temp:
            plan = build_semantic_plan(_analysis_docs(temp))
        obligation = plan["artifacts"]["rust-migration-plan.json"]["implementation_obligations"][0]
        self.assertEqual(obligation["target_module"], "counter")

    def test_independent_denominators_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            docs = _analysis_docs(temp)
            original = build_semantic_plan(docs)["artifacts"]
        changes = [
            ("semantic-ir", "api_contracts", "public_api_contract_coverage_100_percent"),
            ("rust-migration-plan.json", "type_mappings", "core_type_mapping_coverage_100_percent"),
            ("rust-migration-plan.json", "state_mappings", "shared_state_mapping_coverage_100_percent"),
            ("rust-migration-plan.json", "call_edge_mappings", "call_edge_mapping_coverage_100_percent"),
            ("rust-migration-plan.json", "implementation_obligations", "implementation_obligation_coverage_100_percent"),
        ]
        for document, field, check in changes:
            artifacts = copy.deepcopy(original)
            artifacts[document][field] = []
            self.assertFalse(validate_plan(docs, artifacts)["checks"][check], check)

    def test_source_evidence_removal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            docs = _analysis_docs(temp)
            artifacts = build_semantic_plan(docs)["artifacts"]
        artifacts["semantic-ir"]["api_contracts"][0]["evidence_ids"] = []
        self.assertFalse(validate_plan(docs, artifacts)["checks"]["source_evidence_complete"])

    def test_planning_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp:
            docs = _analysis_docs(temp)
            first = build_semantic_plan(docs, run_id="one")
            second = build_semantic_plan(docs, run_id="two")
        self.assertEqual(first["artifacts"], second["artifacts"])
        self.assertEqual(first["metadata"]["semantic_ir_digest"], second["metadata"]["semantic_ir_digest"])

    def test_legacy_and_profile_based_schema_are_rejected(self):
        for schema in ("flashdb-semantic-planning/v1", "semantic-migration-planning/v2"):
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                for name in OUTPUT_FILES:
                    (root / name).write_text(json.dumps({"schema_version": schema}))
                self.assertTrue(any(item.startswith("legacy_planning_schema_requires_replan") for item in validate_planning_documents(root)))

    def test_atomic_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bundle = build_semantic_plan(_analysis_docs(temp), run_id="run")
            write_semantic_plan(bundle, root)
            self.assertEqual(validate_planning_documents(root), [])
            before = {name: (root / name).read_bytes() for name in OUTPUT_FILES}
            broken = copy.deepcopy(bundle)
            del broken["artifacts"]["semantic-invariants.json"]
            with self.assertRaises(KeyError):
                write_semantic_plan(broken, root)
            self.assertEqual({name: (root / name).read_bytes() for name in OUTPUT_FILES}, before)

    def test_end_to_end_from_trace(self):
        with tempfile.TemporaryDirectory() as temp:
            _analysis_docs(temp)
            self.assertTrue(plan_from_trace(Path(temp))["passed"])

    def test_loader_rejects_mixed_analysis(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _analysis_docs(temp)
            public = json.loads((root / "public-api-map.json").read_text())
            public["run_id"] = "stale"
            (root / "public-api-map.json").write_text(json.dumps(public))
            with self.assertRaises(PlanningBlocked) as caught:
                load_analysis_evidence(root)
            self.assertIn("mixed_analysis_run_ids", caught.exception.failures)


if __name__ == "__main__":
    unittest.main()
