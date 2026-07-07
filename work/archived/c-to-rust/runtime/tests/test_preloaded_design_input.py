from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_task_packet import resolve_runtime_contract
from c_project_root_resolver import resolve_c_project_root
from loopforge_runner import LoopForgeRunner


class PreloadedDesignInputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = {"migration_defaults": {"output_project_name": "fallback_rust"}}

    def test_valid_design_is_authoritative_and_hashed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            design = Path(tmp) / "README.md"
            content = b"# Project Name: Demo\noutput `demo_rust`\ncargo build\ncargo test\n"
            design.write_bytes(content)
            contract = resolve_runtime_contract(design, self.profile)
            self.assertEqual(contract["design_readme_error"], "")
            self.assertEqual(contract["design_readme_sha256"], hashlib.sha256(content).hexdigest())
            self.assertEqual(contract["output_project_name"], "demo_rust")

    def test_missing_design_is_rejected_without_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            contract = resolve_runtime_contract(Path(tmp) / "missing.md", self.profile)
            self.assertEqual(contract["design_readme_error"], "design_readme_missing")
            self.assertEqual(contract["design_readme_sha256"], "")

    def test_empty_design_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            design = Path(tmp) / "README.md"
            design.write_text("  \n", encoding="utf-8")
            self.assertEqual(resolve_runtime_contract(design, self.profile)["design_readme_error"], "design_readme_empty")

    def test_non_regular_design_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            design = Path(tmp) / "README.md"
            design.mkdir()
            self.assertEqual(resolve_runtime_contract(design, self.profile)["design_readme_error"], "design_readme_not_regular_file")

    def test_unreadable_design_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            design = Path(tmp) / "README.md"
            design.write_text("requirements", encoding="utf-8")
            with patch.object(Path, "read_bytes", side_effect=PermissionError("denied")):
                self.assertEqual(resolve_runtime_contract(design, self.profile)["design_readme_error"], "design_readme_unreadable")

    def test_source_readme_does_not_affect_discovery_or_mutate_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            (source / "src").mkdir(parents=True)
            (source / "tests").mkdir()
            (source / "README.md").write_text("misleading requirements", encoding="utf-8")
            (source / "src" / "demo.c").write_text("int demo(void) { return 1; }\n", encoding="utf-8")
            (source / "tests" / "test_demo.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
            before = {path.relative_to(source): path.read_bytes() for path in source.rglob("*") if path.is_file()}
            result = resolve_c_project_root(source)
            after = {path.relative_to(source): path.read_bytes() for path in source.rglob("*") if path.is_file()}
            self.assertEqual(result["status"], "RESOLVED")
            self.assertEqual(before, after)

    def test_successful_and_failed_detection_preserve_source_tree(self) -> None:
        workspace = Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            for name, valid in (("valid", True), ("invalid", False)):
                source = temp / name
                source.mkdir()
                if valid:
                    (source / "src").mkdir()
                    (source / "tests").mkdir()
                    (source / "src" / "demo.h").write_text("int demo(void);\n", encoding="utf-8")
                    (source / "src" / "demo.c").write_text("int demo(void) { return 1; }\n", encoding="utf-8")
                    (source / "tests" / "test_demo.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
                before = {path.relative_to(source): path.read_bytes() for path in source.rglob("*") if path.is_file()}
                runner = LoopForgeRunner(workspace, workspace / "work", source, temp / f"{name}-result", temp / f"{name}-logs")
                runner.detect_project()
                after = {path.relative_to(source): path.read_bytes() for path in source.rglob("*") if path.is_file()}
                self.assertEqual(before, after)

    def test_writable_destination_inside_source_is_rejected(self) -> None:
        workspace = Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            with self.assertRaisesRegex(ValueError, "outside SOURCE_ROOT"):
                LoopForgeRunner(workspace, workspace / "work", source, source / "result", Path(tmp) / "logs")


if __name__ == "__main__":
    unittest.main()
