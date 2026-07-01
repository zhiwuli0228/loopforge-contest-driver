import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


RUNTIME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME))

from source_analysis import (  # noqa: E402
    EVIDENCE_FILES,
    build_complete_analysis,
    independent_scan,
    snapshot_source_tree,
    validate_written_evidence,
    write_complete_analysis,
)


FIXTURE = Path(__file__).parent / "fixtures" / "flashdb-real-layout"


def packet(root):
    return SimpleNamespace(metadata={"layout_resolution": {
        "source_dirs": [str(root / "src"), str(root / "inc")],
        "test_dirs": [str(root / "tests")],
    }})


def legacy(root):
    return {
        "project_root": str(root),
        "public_apis": ["fdb_kv_set"],
        "test_files": ["tests/test_flashdb.c"],
        "functions": [
            {"name": "fdb_kv_set", "decl_kind": "prototype", "file": "inc/flashdb.h", "line": 16},
            {"name": "fdb_kv_set", "decl_kind": "definition", "file": "src/flashdb.c", "line": 10},
        ],
    }


class SourceAnalysisTests(unittest.TestCase):
    def test_complex_types_preprocessor_calls_and_state_are_modeled(self):
        bundle = build_complete_analysis(packet(FIXTURE), legacy(FIXTURE))
        artifacts = bundle["artifacts"]
        types = artifacts["type-map.json"]["types"]
        self.assertTrue(any(item["kind"] == "struct" and {m["name"] for m in item["members"]} == {"capacity", "write"} for item in types))
        self.assertTrue(any(item["kind"] == "enum" and {m["name"] for m in item["members"]} == {"FDB_OK", "FDB_ERROR"} for item in types))
        self.assertTrue(any(item["name"] == "write_count" for item in artifacts["global-state-map.json"]["globals"]))
        self.assertTrue(artifacts["preprocessor-variants.json"]["variants"])

    def test_independent_scanner_returns_nonempty_sets(self):
        result = independent_scan(FIXTURE, [FIXTURE / "src", FIXTURE / "inc"], [FIXTURE / "tests"])
        self.assertEqual({item["name"] for item in result["public_apis"]}, {"fdb_kv_set"})
        self.assertEqual({item["path"] for item in result["source_tests"]}, {"tests/test_flashdb.c"})

    def test_missing_api_is_fail_closed(self):
        incomplete = legacy(FIXTURE)
        incomplete["public_apis"] = []
        bundle = build_complete_analysis(packet(FIXTURE), incomplete)
        self.assertFalse(bundle["verification"]["passed"])
        self.assertIn("public_api_count_nonzero", bundle["verification"]["failures"])
        self.assertIn("public_api_sets_match", bundle["verification"]["failures"])

    def test_unresolved_declaration_is_fail_closed(self):
        incomplete = legacy(FIXTURE)
        incomplete["functions"] = incomplete["functions"][:1]
        source = (FIXTURE / "src" / "flashdb.c").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for directory in ("src", "inc", "tests"):
                (root / directory).mkdir()
            (root / "inc" / "flashdb.h").write_text((FIXTURE / "inc" / "flashdb.h").read_text(), encoding="utf-8")
            (root / "src" / "flashdb.c").write_text(source.replace("fdb_kv_set", "private_set"), encoding="utf-8")
            (root / "tests" / "test_flashdb.c").write_text((FIXTURE / "tests" / "test_flashdb.c").read_text(), encoding="utf-8")
            incomplete["project_root"] = str(root)
            bundle = build_complete_analysis(packet(root), incomplete)
        self.assertIn("all_public_apis_resolved", bundle["verification"]["failures"])

    def test_source_tree_is_unchanged_and_output_is_coherent(self):
        before = snapshot_source_tree(FIXTURE)
        bundle = build_complete_analysis(packet(FIXTURE), legacy(FIXTURE))
        with tempfile.TemporaryDirectory() as temp:
            write_complete_analysis(bundle, Path(temp))
            documents = [json.loads((Path(temp) / name).read_text()) for name in EVIDENCE_FILES]
        self.assertEqual(snapshot_source_tree(FIXTURE), before)
        self.assertEqual(len({item["run_id"] for item in documents}), 1)
        self.assertEqual(len({item["schema_version"] for item in documents}), 1)

    def test_normalized_content_is_deterministic(self):
        first = build_complete_analysis(packet(FIXTURE), legacy(FIXTURE))
        second = build_complete_analysis(packet(FIXTURE), legacy(FIXTURE))
        self.assertEqual(first["artifacts"], second["artifacts"])

    def test_mixed_run_and_dangling_evidence_are_rejected(self):
        bundle = build_complete_analysis(packet(FIXTURE), legacy(FIXTURE))
        with tempfile.TemporaryDirectory() as temp:
            trace = Path(temp)
            write_complete_analysis(bundle, trace)
            public_map = json.loads((trace / "public-api-map.json").read_text())
            public_map["run_id"] = "stale-run"
            public_map["apis"][0]["declaration"]["file"] = "inc/missing.h"
            (trace / "public-api-map.json").write_text(json.dumps(public_map), encoding="utf-8")
            failures = validate_written_evidence(trace, FIXTURE)
        self.assertIn("mixed_run_ids", failures)
        self.assertIn("dangling_source_evidence:inc/missing.h", failures)

    def test_missing_structure_field_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for directory in ("src", "inc", "tests"):
                (root / directory).mkdir()
            header = (FIXTURE / "inc" / "flashdb.h").read_text().replace("int capacity;", "int;")
            source = (FIXTURE / "src" / "flashdb.c").read_text().replace("int capacity;", "int;")
            (root / "inc" / "flashdb.h").write_text(header, encoding="utf-8")
            (root / "src" / "flashdb.c").write_text(source, encoding="utf-8")
            (root / "tests" / "test_flashdb.c").write_text((FIXTURE / "tests" / "test_flashdb.c").read_text(), encoding="utf-8")
            model = legacy(root)
            bundle = build_complete_analysis(packet(root), model)
        self.assertIn("all_core_types_complete", bundle["verification"]["failures"])

    def test_unbalanced_core_file_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for directory in ("src", "inc", "tests"):
                (root / directory).mkdir()
            (root / "inc" / "flashdb.h").write_text((FIXTURE / "inc" / "flashdb.h").read_text(), encoding="utf-8")
            source = (FIXTURE / "src" / "flashdb.c").read_text() + "\nvoid broken(void) {\n"
            (root / "src" / "flashdb.c").write_text(source, encoding="utf-8")
            (root / "tests" / "test_flashdb.c").write_text((FIXTURE / "tests" / "test_flashdb.c").read_text(), encoding="utf-8")
            bundle = build_complete_analysis(packet(root), legacy(root))
        self.assertIn("core_parse_succeeded", bundle["verification"]["failures"])

    def test_analysis_policy_is_derived_from_the_resolved_input(self):
        current = packet(FIXTURE)
        current.metadata["source_analysis"] = {
            "preprocessor_variants": [{"name": "feature-a", "defines": ["ENABLE_FEATURE_A"]}]
        }
        bundle = build_complete_analysis(current, legacy(FIXTURE))
        variants = bundle["artifacts"]["preprocessor-variants.json"]
        inventory = bundle["artifacts"]["source-inventory.json"]
        self.assertEqual(variants["required_variants"], current.metadata["source_analysis"]["preprocessor_variants"])
        self.assertEqual(inventory["scope"], {"source_dirs": ["inc", "src"], "test_dirs": ["tests"]})
        self.assertNotIn("acceptance_commit", json.dumps(bundle))


if __name__ == "__main__":
    unittest.main()
