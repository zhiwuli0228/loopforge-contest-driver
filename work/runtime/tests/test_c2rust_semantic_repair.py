import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from c2rust_semantic_repair import run_semantic_repair_loop


def semantic(passed=False):
    return {"passed": passed, "failing_checks": [] if passed else ["api_mapping"],
            "checks": [{"name": "api_mapping", "unsupported_apis": [] if passed else ["missing_api"]}]}


class SemanticRepairLoopTests(unittest.TestCase):
    def packet(self, root, rounds=2):
        project = root / "project"
        (project / "tests").mkdir(parents=True)
        return SimpleNamespace(
            config={"execution": {"max_semantic_repair_rounds": rounds}}, issues=[],
            output_project_dir=project, output_project_name="demo",
            paths=SimpleNamespace(migration_trace_dir=root / "trace"),
        )

    def test_successful_semantic_repair_reaudits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / "trace").mkdir(); packet = self.packet(root)
            with patch("c2rust_semantic_repair.invoke_external_repair_provider", return_value={"applied": True}), \
                 patch("c2rust_semantic_repair.render_invariant_tests", return_value=("#[test]\nfn invariant() {}\n", [])), \
                 patch("c2rust_semantic_repair.run_repair_loop", return_value={"build_ok": True, "test_ok": True}), \
                 patch("c2rust_semantic_repair.evaluate_semantic_equivalence", return_value=semantic(True)):
                result = run_semantic_repair_loop(packet, {}, {"test_mapping": []}, semantic(), ["cargo build"], 10)
            self.assertTrue(result["passed"])
            self.assertEqual(result["rounds_executed"], 1)
            self.assertTrue((packet.output_project_dir / "tests" / "semantic_invariants.rs").is_file())

    def test_provider_unavailable_stops_without_claiming_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / "trace").mkdir(); packet = self.packet(root)
            with patch("c2rust_semantic_repair.invoke_external_repair_provider", return_value={"applied": False, "detail": "repair_provider_unavailable"}):
                result = run_semantic_repair_loop(packet, {}, {"test_mapping": []}, semantic(), [], 10)
            self.assertFalse(result["passed"])
            self.assertEqual(result["rounds_executed"], 1)

    def test_exhausts_configured_rounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / "trace").mkdir(); packet = self.packet(root, 2)
            with patch("c2rust_semantic_repair.invoke_external_repair_provider", return_value={"applied": True}), \
                 patch("c2rust_semantic_repair.render_invariant_tests", return_value=("", [])), \
                 patch("c2rust_semantic_repair.run_repair_loop", return_value={"build_ok": True, "test_ok": True}), \
                 patch("c2rust_semantic_repair.evaluate_semantic_equivalence", return_value=semantic(False)):
                result = run_semantic_repair_loop(packet, {}, {"test_mapping": []}, semantic(), [], 10)
            self.assertFalse(result["passed"])
            self.assertEqual(result["rounds_executed"], 2)


if __name__ == "__main__":
    unittest.main()
