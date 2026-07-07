import json
import sys
import tempfile
import unittest
from pathlib import Path


ADAPTERS_ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ADAPTERS_ROOT.parent
sys.path.insert(0, str(WORK_ROOT))

from adapters.registry import build_default_registry  # noqa: E402
from runtime.code_inventory import build_source_inventory, extract_implementation_model  # noqa: E402


class LanguageAdaptersTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = build_default_registry()
        self.profile_path = WORK_ROOT / "profiles" / "examples" / "default-java-consistency.yaml"
        self.java_fixture = ADAPTERS_ROOT / "tests" / "fixtures" / "java_order_service"
        self.generic_fixture = WORK_ROOT / "runtime" / "tests" / "fixtures" / "generic-counter"

    def test_java_selection_and_extraction_emit_canonical_objects(self):
        inventory = build_source_inventory(self.java_fixture, self.profile_path)
        self.assertEqual(inventory["selected_adapter"], "java")
        self.assertTrue(inventory["selection"]["signals"])

        extracted = extract_implementation_model(self.java_fixture, self.profile_path)
        kinds = {item["kind"] for item in extracted["implementation_model"]["objects"]}
        self.assertIn("entrypoint", kinds)
        self.assertIn("data_shape", kinds)
        self.assertIn("config_surface", kinds)
        self.assertIn("test_artifact", kinds)
        for item in extracted["implementation_model"]["objects"]:
            self.assertIn("adapter_id", item)
            self.assertIn("normalization_status", item)
            self.assertIn("confidence", item)

    def test_generic_fallback_marks_partial_objects(self):
        inventory = build_source_inventory(self.generic_fixture, self.profile_path)
        self.assertEqual(inventory["selected_adapter"], "generic")
        self.assertTrue(inventory["selection"]["fallback_used"])

        extracted = extract_implementation_model(self.generic_fixture, self.profile_path)
        objects = extracted["implementation_model"]["objects"]
        self.assertTrue(any(item["normalization_status"] == "partial" for item in objects))
        self.assertTrue(any(item["kind"] == "symbol" for item in objects))
        self.assertTrue(any(item["kind"] == "test_artifact" for item in objects))

    def test_runtime_helpers_return_json_serializable_contracts(self):
        extracted = extract_implementation_model(self.java_fixture, self.profile_path)
        payload = json.dumps(extracted)
        self.assertIn("implementation_model", payload)
        self.assertIn("selection", payload)


if __name__ == "__main__":
    unittest.main()
