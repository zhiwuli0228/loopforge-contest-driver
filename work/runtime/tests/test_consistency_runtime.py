from __future__ import annotations

import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


WORK_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORK_ROOT))

from runtime.design_scanner import scan_design_root  # noqa: E402
from runtime.loopforge_runner import LoopForgeRunner  # noqa: E402
from runtime.tools import main as tools_main  # noqa: E402
from runtime.verification_runner import resolve_verification_commands, run_verification  # noqa: E402


class ConsistencyRuntimeTests(unittest.TestCase):
    def _run_tools(self, argv: list[str]) -> dict:
        stdout = StringIO()
        with redirect_stdout(stdout):
            tools_main(argv)
        return json.loads(stdout.getvalue())

    def test_scan_design_extracts_inventory_and_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            submission_root = Path(tmp) / "submission"
            design_root = submission_root / "design-docs"
            design_root.mkdir(parents=True)
            (submission_root / "README.md").write_text(
                "# Contest Contract\n\n## Validation\nUse black-box tests.\n",
                encoding="utf-8",
            )
            (design_root / "README.md").write_text(
                "# Demo Contract\n\n## Counter API\nThe counter increments monotonically.\n",
                encoding="utf-8",
            )
            result = scan_design_root(design_root, submission_readme=submission_root / "README.md")
            self.assertEqual(result["inventory"]["file_count"], 2)
            self.assertEqual(result["inventory"]["primary_design_file"], "README.md")
            self.assertGreaterEqual(len(result["design_model"]["objects"]), 2)
            self.assertEqual(result["inventory"]["submission_readme"], "README.md")

    def test_resolve_verification_prefers_submission_metadata_and_readme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            submission_root = Path(tmp) / "submission"
            code_root = submission_root / "code"
            code_root.mkdir(parents=True)
            (submission_root / "contest.meta.yaml").write_text(
                "verification:\n  commands:\n    - mvn -f code/pom.xml test\n",
                encoding="utf-8",
            )
            resolved = resolve_verification_commands(code_root, submission_root=submission_root)
            self.assertEqual(resolved["command_source"], "submission-metadata")
            self.assertEqual(resolved["commands"], ["mvn -f code/pom.xml test"])

        with tempfile.TemporaryDirectory() as tmp:
            submission_root = Path(tmp) / "submission"
            code_root = submission_root / "code"
            code_root.mkdir(parents=True)
            (submission_root / "README.md").write_text(
                "```bash\nmvn -f code/pom.xml install -DskipTests\nmvn -f test-cases/pom.xml test\n```\n",
                encoding="utf-8",
            )
            resolved = resolve_verification_commands(code_root, submission_root=submission_root)
            self.assertEqual(resolved["command_source"], "submission-readme")
            self.assertEqual(
                resolved["commands"],
                ["mvn -f code/pom.xml install -DskipTests", "mvn -f test-cases/pom.xml test"],
            )

    def test_run_verification_records_skipped_and_unavailable_states(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            skipped = run_verification(project, commands=[])
            self.assertEqual(skipped["overall_status"], "skipped")

            unavailable = run_verification(project, commands=["definitely-missing-verifier --version"])
            self.assertEqual(unavailable["overall_status"], "unavailable")
            self.assertEqual(unavailable["results"][0]["status"], "unavailable")

    def test_tools_pipeline_writes_authoritative_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            submission_root = root / "submission"
            design_root = submission_root / "design-docs"
            source_root = submission_root / "code"
            test_root = submission_root / "test-cases"
            trace_root = root / "logs" / "trace" / "consistency"
            result_dir = root / "result"
            trace_dir = root / "logs" / "trace"

            design_root.mkdir(parents=True)
            source_root.mkdir(parents=True)
            test_root.mkdir(parents=True)
            (submission_root / "README.md").write_text(
                "```bash\nmvn -f code/pom.xml test\n```\n",
                encoding="utf-8",
            )
            (source_root / "app.py").write_text("def counter():\n    return 1\n", encoding="utf-8")
            (test_root / "PublicTest.java").write_text("// black-box\n", encoding="utf-8")
            (design_root / "README.md").write_text(
                "# Counter Contract\n\n## counter\nReturn the current counter value.\n",
                encoding="utf-8",
            )

            self._run_tools(
                [
                    "scan-design",
                    "--design-root", str(design_root),
                    "--submission-readme", str(submission_root / "README.md"),
                    "--output", str(trace_root / "01-design-inventory.json"),
                    "--model-output", str(trace_root / "03-design-model.json"),
                    "--evidence-output", str(trace_root / "03-design-model-evidence.json"),
                    "--source-root", str(source_root),
                ]
            )
            self._run_tools(
                [
                    "scan-code",
                    "--source-root", str(source_root),
                    "--submission-root", str(submission_root),
                    "--test-root", str(test_root),
                    "--output", str(trace_root / "02-source-inventory.json"),
                    "--selection-output", str(trace_root / "02-adapter-selection.json"),
                ]
            )
            self._run_tools(
                [
                    "extract-implementation",
                    "--source-root", str(source_root),
                    "--output", str(trace_root / "04-implementation-model.json"),
                    "--inventory-output", str(trace_root / "04-implementation-model-evidence.json"),
                    "--selection-output", str(trace_root / "02-adapter-selection.json"),
                ]
            )
            self._run_tools(
                [
                    "build-traceability",
                    "--design-model", str(trace_root / "03-design-model.json"),
                    "--implementation-model", str(trace_root / "04-implementation-model.json"),
                    "--output", str(trace_root / "05-traceability-matrix.json"),
                    "--summary-output", str(trace_root / "05-traceability-map.md"),
                    "--evidence-output", str(trace_root / "05-traceability-map-evidence.json"),
                    "--source-root", str(source_root),
                ]
            )
            self._run_tools(
                [
                    "run-verification",
                    "--project-dir", str(source_root),
                    "--commands", "[]",
                    "--output", str(trace_root / "09-verification-results.json"),
                ]
            )
            payload = self._run_tools(
                [
                    "write-report",
                    "--result-dir", str(result_dir),
                    "--trace-dir", str(trace_dir),
                    "--trace-root", str(trace_root),
                    "--design-root", str(design_root),
                    "--source-root", str(source_root),
                    "--submission-root", str(submission_root),
                    "--test-root", str(test_root),
                    "--payload-output", str(trace_root / "09-final-report-input.json"),
                ]
            )

            self.assertTrue((trace_root / "01-design-inventory.json").is_file())
            self.assertTrue((trace_root / "05-traceability-matrix.json").is_file())
            self.assertTrue((trace_root / "09-verification-results.json").is_file())
            self.assertTrue((trace_root / "09-final-report-input.json").is_file())
            self.assertTrue((trace_dir / "final-report.md").is_file())
            self.assertTrue((result_dir / "output.md").is_file())
            self.assertTrue((result_dir / "issues" / "00-summary.md").is_file())
            self.assertIn("output_path", payload["data"])

    def test_write_report_preserves_partial_failure_without_source_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            submission_root = root / "submission"
            design_root = submission_root / "design-docs"
            source_root = submission_root / "code"
            test_root = submission_root / "test-cases"
            trace_root = root / "logs" / "trace" / "consistency"
            result_dir = root / "result"
            trace_dir = root / "logs" / "trace"

            design_root.mkdir(parents=True)
            source_root.mkdir(parents=True)
            test_root.mkdir(parents=True)
            (submission_root / "README.md").write_text("# Contest\n", encoding="utf-8")
            (design_root / "README.md").write_text("# Design\n", encoding="utf-8")
            (source_root / "service.txt").write_text("service\n", encoding="utf-8")
            (test_root / "PublicTest.java").write_text("// black-box\n", encoding="utf-8")
            trace_root.mkdir(parents=True)
            (trace_root / "02-source-inventory.json").write_text(
                json.dumps({"source_root": str(source_root), "submission_root": str(submission_root), "test_root": str(test_root)}),
                encoding="utf-8",
            )
            (trace_root / "03-design-model.json").write_text(
                json.dumps({"objects": [{"id": "d:1", "name": "api", "kind": "capability", "summary": "demo", "evidence_refs": [{"source": "design", "path": "README.md", "locator": "line:1"}]}]}),
                encoding="utf-8",
            )
            (trace_root / "04-implementation-model.json").write_text(
                json.dumps({"objects": [{"id": "i:1", "name": "service", "kind": "module", "summary": "demo", "evidence_refs": [{"source": "implementation", "path": "service.txt", "locator": "line:1"}]}]}),
                encoding="utf-8",
            )
            (trace_root / "05-traceability-matrix.json").write_text(
                json.dumps({"coverage_summary": {"matched_links": 0, "partial_links": 0, "gaps": 1, "unmatched_implementation_count": 1, "unresolved_reference_count": 0}}),
                encoding="utf-8",
            )
            (trace_root / "09-verification-results.json").write_text(
                json.dumps({"overall_status": "unavailable", "results": [{"command": "missing", "status": "unavailable"}]}),
                encoding="utf-8",
            )
            before = {path.relative_to(source_root): path.read_bytes() for path in source_root.rglob("*") if path.is_file()}
            self._run_tools(
                [
                    "write-report",
                    "--result-dir", str(result_dir),
                    "--trace-dir", str(trace_dir),
                    "--trace-root", str(trace_root),
                    "--design-root", str(design_root),
                    "--source-root", str(source_root),
                    "--submission-root", str(submission_root),
                    "--test-root", str(test_root),
                ]
            )
            after = {path.relative_to(source_root): path.read_bytes() for path in source_root.rglob("*") if path.is_file()}
            self.assertEqual(before, after)
            output = (result_dir / "output.md").read_text(encoding="utf-8")
            self.assertIn("DEGRADED", output)
            self.assertIn("Submission Root", output)

    def test_guard_rejects_output_inside_source_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            design_root = root / "design"
            source_root = root / "source"
            design_root.mkdir()
            source_root.mkdir()
            (design_root / "README.md").write_text("# Demo\n", encoding="utf-8")
            stdout = StringIO()
            with self.assertRaises(SystemExit):
                with redirect_stdout(stdout):
                    tools_main(
                        [
                            "scan-design",
                            "--design-root", str(design_root),
                            "--output", str(source_root / "forbidden.json"),
                            "--source-root", str(source_root),
                        ]
                    )

    def test_loopforge_runner_validates_standard_submission_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace_root = WORK_ROOT.parent
            work_dir = WORK_ROOT
            submission_root = root / "submission"
            (submission_root / "design-docs").mkdir(parents=True)
            (submission_root / "code").mkdir()
            (submission_root / "README.md").write_text("# Contest\n", encoding="utf-8")
            runner = LoopForgeRunner(workspace_root, work_dir, submission_root, root / "result", root / "logs")
            payload = runner.create_self_check_payload()
            self.assertIn("test_root_missing", " ".join(payload["issues"]))

            (submission_root / "contest.meta.yaml").write_text("verification:\n  commands:\n    - mvn -f code/pom.xml test\n", encoding="utf-8")
            payload = runner.create_self_check_payload()
            self.assertTrue(payload["ok"])
            self.assertTrue((root / "logs" / "trace" / "consistency" / "00-submission-layout.json").is_file())


if __name__ == "__main__":
    unittest.main()
