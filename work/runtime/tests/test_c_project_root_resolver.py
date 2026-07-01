from __future__ import annotations

import sys
import tempfile
import unittest
import json
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from c_project_root_resolver import resolve_c_project_root
from loopforge_runner import LoopForgeRunner
import loopforge_runner


class CProjectRootResolverTests(unittest.TestCase):
    def make_project(self, root: Path, name: str = "FlashDB", source: str = "src", tests: str = "tests") -> Path:
        project = root / name
        (project / source).mkdir(parents=True)
        (project / tests).mkdir(parents=True)
        (project / source / "flashdb.h").write_text("int flashdb_open(void);\n", encoding="utf-8")
        (project / source / "flashdb.c").write_text("int flashdb_open(void) { return 0; }\n", encoding="utf-8")
        (project / tests / "test_flashdb.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
        return project

    def test_project_root_resolves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self.make_project(Path(tmp))
            result = resolve_c_project_root(project)
            self.assertEqual(result["status"], "RESOLVED")
            self.assertEqual(Path(result["resolved_project_root"]), project.resolve())

    def test_parent_with_unique_project_resolves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "code"
            project = self.make_project(root)
            result = resolve_c_project_root(root)
            self.assertEqual(Path(result["resolved_project_root"]), project.resolve())

    def test_work_code_style_input_resolves_nested_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "work" / "code"
            root.mkdir(parents=True)
            (root / "README.md").write_text("Task statement\n", encoding="utf-8")
            project = self.make_project(root)
            result = resolve_c_project_root(root)
            self.assertEqual(result["status"], "RESOLVED")
            self.assertEqual(Path(result["resolved_project_root"]), project.resolve())

    def test_source_free_input_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "work" / "code" / "FlashDB"
            root.mkdir(parents=True)
            result = resolve_c_project_root(root)
            self.assertEqual(result["status"], "BLOCKED_WITH_REPORT")
            self.assertEqual(result["reason"], "unable to resolve usable C project layout from input_root")

    def test_multiple_projects_are_ambiguous_and_scored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "work" / "code"
            self.make_project(root, "FlashDB")
            self.make_project(root, "OtherDB")
            result = resolve_c_project_root(root)
            self.assertEqual(result["status"], "BLOCKED_WITH_REPORT")
            self.assertEqual(result["reason"], "ambiguous project roots")
            usable = [item for item in result["candidate_roots"] if item["usable"]]
            self.assertEqual(len(usable), 2)
            self.assertTrue(all(isinstance(item["score"], int) for item in usable))

    def test_filesystem_discovery_supports_nonstandard_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self.make_project(Path(tmp), source="core", tests="checks")
            result = resolve_c_project_root(project)
            self.assertEqual(result["status"], "RESOLVED")
            self.assertEqual([Path(item).name for item in result["source_dirs"]], ["core"])
            self.assertEqual([Path(item).name for item in result["test_dirs"]], ["checks"])

    def test_discovers_sources_without_conventional_directory_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "OddLayout"
            (project / "engine").mkdir(parents=True)
            (project / "qa").mkdir()
            (project / "engine" / "db.c").write_text("int db_open(void) { return 0; }\n", encoding="utf-8")
            (project / "engine" / "db.h").write_text("int db_open(void);\n", encoding="utf-8")
            (project / "qa" / "test_db.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
            result = resolve_c_project_root(project)
            self.assertEqual(result["status"], "RESOLVED")
            self.assertEqual([Path(item).name for item in result["source_dirs"]], ["engine"])

    def test_project_does_not_require_a_tests_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "Library"
            project.mkdir()
            (project / "library.c").write_text("int library_open(void) { return 0; }\n", encoding="utf-8")
            result = resolve_c_project_root(project)
            self.assertEqual(result["status"], "RESOLVED")

    def test_runner_records_input_and_resolution_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            input_root = temp / "code"
            project = self.make_project(input_root)
            workspace = Path(__file__).resolve().parents[3]
            runner = LoopForgeRunner(workspace, workspace / "work", input_root, temp / "result", temp / "logs")
            packet = runner.create_agent_task_packet()
            trace = temp / "logs" / "trace" / "c-to-rust" / "00-input-layout-resolution.json"
            payload = json.loads(trace.read_text(encoding="utf-8"))
            self.assertEqual(packet.paths.input_root, input_root.resolve())
            self.assertEqual(packet.paths.source_root, project.resolve())
            self.assertEqual(
                set(payload),
                {"input_root", "resolved_project_root", "source_dirs", "test_dirs", "candidate_roots", "resolution_strategy", "status", "reason"},
            )
            self.assertTrue(trace.with_suffix(".md").is_file())

    def test_windows_default_input_is_platform_placeholder(self) -> None:
        workspace = Path(__file__).resolve().parents[3]
        resolved = loopforge_runner.resolve_default_source_root(workspace, platform_name="nt")
        self.assertNotEqual(resolved, (workspace / "work" / "code").resolve())
        self.assertTrue(str(resolved).replace("\\", "/").endswith("/__CONTEST_PLATFORM_SOURCE_ROOT__/source"))

    def test_non_windows_default_does_not_use_work_code(self) -> None:
        workspace = Path(__file__).resolve().parents[3]
        resolved = loopforge_runner.resolve_default_source_root(workspace, platform_name="posix")
        self.assertNotEqual(resolved, (workspace / "work" / "code").resolve())
        self.assertTrue(str(resolved).replace("\\", "/").endswith("/__CONTEST_PLATFORM_SOURCE_ROOT__/source"))


if __name__ == "__main__":
    unittest.main()
