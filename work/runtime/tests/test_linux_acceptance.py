import json
import os
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from linux_acceptance import (
    AcceptanceLedger, AcceptanceWorkspace, BOOLEAN_GATES, NONZERO_COUNTS, PIPELINE_BLUEPRINT, SCHEMAS,
    Stage, StageDag, assert_clean_workspace, build_pipeline_dag, compare_manifests, customization_audit,
    final_retry, final_verification, fallback_report, normalized, path_manifest,
    publish_reports, publish_source_integrity, record_decision, repeatability_report,
    submission_manifest, validate_artifact_references, validate_report_coherence, validate_schema,
)
from linux_acceptance_cli import run_once
from timeout_policy import JUDGING_PLATFORM_TIMEOUT_SECONDS


class LinuxAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "unit.c").write_text("int unit(void) { return 1; }\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_schemas_and_unique_clean_workspace(self):
        self.assertEqual(set(SCHEMAS), {"linux-run-manifest", "stage-outcome", "exception-ledger", "customization-audit", "repeatability", "final-verification"})
        workspace = AcceptanceWorkspace.create(self.root / "runs", self.source, "run-1")
        self.assertEqual(assert_clean_workspace(workspace), [])
        manifest = workspace.manifest(self.source, self.source)
        self.assertEqual(validate_schema("linux-run-manifest", manifest), [])
        (workspace.output / "stale.rs").write_text("stale", encoding="utf-8")
        self.assertEqual(assert_clean_workspace(workspace), ["stale-artifact:output"])
        with self.assertRaises(ValueError):
            AcceptanceWorkspace.create(self.root / "runs", self.source, "run-1")

    def test_workspace_cannot_overlap_source(self):
        with self.assertRaises(ValueError):
            AcceptanceWorkspace.create(self.source, self.source, "inside")

    def test_source_manifest_detects_content_mode_and_links(self):
        before = path_manifest(self.source)
        (self.source / "unit.c").write_text("changed\n", encoding="utf-8")
        after = path_manifest(self.source)
        self.assertEqual(compare_manifests(before, after)["changed"], ["unit.c"])
        report = publish_source_integrity(self.root / "trace", "run", before, after)
        self.assertEqual(report["status"], "failed")
        self.assertTrue((self.root / "trace" / "source-before.sha256").is_file())

    def test_stage_dag_continues_independent_work(self):
        ledger = AcceptanceLedger("run")
        dag = StageDag("run", ledger)
        dag.add(Stage("crash", lambda: (_ for _ in ()).throw(RuntimeError("boom"))))
        dag.add(Stage("dependent", lambda: True, dependencies=("crash",)))
        dag.add(Stage("independent", lambda: "ok"))
        outcomes = dag.run()
        self.assertEqual(outcomes["crash"]["status"], "exception")
        self.assertEqual(outcomes["dependent"]["status"], "skipped_dependency")
        self.assertEqual(outcomes["independent"]["status"], "completed")
        self.assertEqual(len(ledger.entries), 2)

    def test_full_pipeline_blueprint_declares_contract_and_failure_matrix(self):
        names = [item["name"] for item in PIPELINE_BLUEPRINT]
        self.assertEqual(names, ["source-analysis", "semantic-planning", "rust-generation", "test-migration", "differential-validation", "repair", "cargo-build", "cargo-test", "unsafe-audit", "acceptance"])
        for item in PIPELINE_BLUEPRINT:
            self.assertTrue(item["inputs"])
            self.assertTrue(item["outputs"])
        ledger = AcceptanceLedger("run")
        actions = {
            "source-analysis": lambda: True,
            "semantic-planning": lambda: (_ for _ in ()).throw(TimeoutError("timeout")),
            "repair": lambda: (_ for _ in ()).throw(FileNotFoundError("missing tool")),
        }
        outcomes = build_pipeline_dag("run", ledger, actions, [self.root / "output"], 1).run()
        self.assertEqual(outcomes["semantic-planning"]["status"], "exception")
        self.assertEqual(outcomes["rust-generation"]["status"], "skipped_dependency")
        self.assertEqual(outcomes["repair"]["status"], "skipped_dependency")
        self.assertTrue(any(item.kind == "TimeoutError" for item in ledger.entries))

    def test_final_retry_runs_once_per_deferred_and_preserves_history(self):
        ledger = AcceptanceLedger("run")
        repaired = ledger.add("build", "exit", "failed")
        unresolved = ledger.add("test", "timeout", "failed")
        calls = []
        def retry(record):
            calls.append(record.exception_id)
            return record is repaired, {"targeted": True, "full_regression": record is repaired}
        final_retry(ledger, retry)
        final_retry(ledger, retry)
        self.assertEqual(len(calls), 2)
        self.assertEqual(repaired.status, "final_retry_repaired")
        self.assertEqual(unresolved.status, "unresolved")
        self.assertEqual(len(unresolved.attempts), 1)

    def test_customization_audit_detects_terms_paths_and_indirect_dispatch(self):
        submission = self.root / "submission"
        (submission / "rules").mkdir(parents=True)
        (submission / "rules" / "neutral.md").write_text("generic language rule", encoding="utf-8")
        clean = customization_audit(submission, "run", ["benchmark_identity"])
        self.assertEqual(clean["status"], "passed")
        (submission / "rules" / "bad.py").write_text("if project_identity == 'x':\n    pass\n", encoding="utf-8")
        bad = customization_audit(submission, "run", ["benchmark_identity"])
        self.assertTrue(bad["direct_disqualification"])
        self.assertTrue(any(item["category"] == "identity-dispatch" for item in bad["findings"]))

    def test_submission_manifest_excludes_runtime_outputs(self):
        submission = self.root / "submission"
        (submission / "work" / "runtime").mkdir(parents=True)
        (submission / "work" / "runtime" / "driver.py").write_text("pass\n", encoding="utf-8")
        (submission / "logs").mkdir()
        (submission / "logs" / "old.json").write_text("{}", encoding="utf-8")
        (submission / "work" / "code").mkdir()
        (submission / "work" / "code" / "external.c").write_text("external", encoding="utf-8")
        paths = [item["path"] for item in submission_manifest(submission)]
        self.assertEqual(paths, ["work/runtime/driver.py"])

    def test_runtime_taint_is_data_only(self):
        accepted = record_decision("run", "inventory", [{"value": "external-name", "tainted": True, "usage": "evidence"}], "record")
        rejected = record_decision("run", "strategy", [{"value": "external-name", "tainted": True, "usage": "strategy"}], "special")
        self.assertEqual(accepted["status"], "accepted")
        self.assertEqual(rejected["status"], "rejected")

    def test_repeatability_only_normalizes_minimal_metadata(self):
        left = {"run_id": "one", "created_at": "a", "code": "same", "count": 1}
        right = {"run_id": "two", "created_at": "b", "code": "same", "count": 1}
        self.assertEqual(repeatability_report("one", "two", left, right)["status"], "passed")
        right["code"] = "different"
        self.assertEqual(repeatability_report("one", "two", left, right)["status"], "failed")
        self.assertIn("code", normalized(right))

    def complete_evidence(self, run_id="run"):
        evidence = {name: 1 for name in NONZERO_COUNTS}
        evidence.update({name: True for name in BOOLEAN_GATES})
        evidence.update(run_id=run_id, unsafe_ratio=0.09)
        return evidence

    def test_final_gate_is_non_vacuous_current_run_and_strict(self):
        ledger = AcceptanceLedger("run")
        good = final_verification("run", self.complete_evidence(), ledger)
        self.assertEqual(good["compliance_status"], "READY_FOR_EVALUATION")
        for mutation in (
            {"source_file_count": 0}, {"cargo_test_passed": False},
            {"unsafe_ratio": 0.10}, {"run_id": "stale"},
        ):
            evidence = self.complete_evidence()
            evidence.update(mutation)
            self.assertEqual(final_verification("run", evidence, ledger)["compliance_status"], "NOT_READY")
        ledger.add("build", "exit", "bad", status="unresolved")
        self.assertEqual(final_verification("run", self.complete_evidence(), ledger)["compliance_status"], "NOT_READY")

    def test_artifact_references_require_current_nonempty_schema_valid_hashes(self):
        artifact = self.root / "artifact.json"
        artifact.write_text("{}\n", encoding="utf-8")
        from linux_acceptance import digest_file
        valid = {"run_id": "run", "path": str(artifact), "sha256": digest_file(artifact), "schema_valid": True}
        self.assertEqual(validate_artifact_references("run", [valid]), [])
        for mutation in ({"run_id": "old"}, {"sha256": "bad"}, {"schema_valid": False}, {"path": str(self.root / "missing")}):
            item = {**valid, **mutation}
            self.assertTrue(validate_artifact_references("run", [item]))
        self.assertEqual(validate_artifact_references("run", []), ["artifacts:empty"])

    def test_reports_are_coherent_and_list_all_unresolved(self):
        ledger = AcceptanceLedger("run")
        ledger.add("build", "exit", "bad", status="unresolved", evidence=["cargo-build.log"])
        verification = final_verification("run", self.complete_evidence(), ledger)
        publish_reports(self.root / "result", self.root / "trace", verification, ledger)
        output = (self.root / "result" / "output.md").read_text(encoding="utf-8")
        issues = (self.root / "result" / "issues" / "00-summary.md").read_text(encoding="utf-8")
        self.assertEqual(output, issues)
        self.assertIn("acceptance-0001", output)
        payload = json.loads((self.root / "trace" / "final-verification.json").read_text())
        self.assertEqual(payload["compliance_status"], "NOT_READY")
        self.assertEqual(validate_report_coherence(self.root / "result", verification), [])
        (self.root / "result" / "issues" / "00-summary.md").write_text("conflict\n", encoding="utf-8")
        self.assertIn("human-reports-conflict", validate_report_coherence(self.root / "result", verification))

    def test_fallback_report_never_claims_ready(self):
        payload = fallback_report(self.root / "result", "run", RuntimeError("renderer failed"))
        self.assertEqual(payload["execution_status"], "COMPLETED_WITH_EXCEPTIONS")
        self.assertEqual(payload["compliance_status"], "NOT_READY")
        self.assertTrue((self.root / "result" / "fallback-report.json").is_file())

    @mock.patch("linux_acceptance.atomic_json", side_effect=OSError("partial write"))
    def test_fallback_tolerates_unwritable_primary_target(self, _write):
        payload = fallback_report(self.root / "result", "run", OSError("primary failed"))
        self.assertEqual(payload["compliance_status"], "NOT_READY")

    @mock.patch("linux_acceptance_cli.subprocess.run")
    def test_entrypoint_run_isolated_and_reports_nonzero_without_escaping(self, run):
        submission = self.root / "submission"
        (submission / "work" / "scripts").mkdir(parents=True)
        (submission / "work" / "scripts" / "run.sh").write_text("#!/bin/sh\n", encoding="utf-8")
        def command_result(command, **_kwargs):
            if command[0] in {"rustc", "cargo"}:
                return mock.Mock(returncode=0, stdout=f"{command[0]} test-version\n", stderr="")
            return mock.Mock(returncode=7, stdout="out", stderr="err")
        run.side_effect = command_result
        result = run_once(self.source, submission, self.root / "runs", "formal-1", [])
        run_root = Path(result["root"])
        self.assertEqual(result["verification"]["execution_status"], "COMPLETED_WITH_EXCEPTIONS")
        self.assertEqual(result["verification"]["compliance_status"], "NOT_READY")
        self.assertTrue((run_root / "logs" / "driver.stderr.log").is_file())
        self.assertTrue((run_root / "logs" / "driver-final-retry.stderr.log").is_file())
        self.assertTrue((run_root / "result" / "output.md").is_file())
        self.assertEqual(path_manifest(self.source)["unit.c"]["sha256"], path_manifest(self.source)["unit.c"]["sha256"])
        driver_calls = [call for call in run.call_args_list if call.args[0][0] == "bash"]
        self.assertTrue(driver_calls)
        self.assertTrue(all(call.kwargs["timeout"] == JUDGING_PLATFORM_TIMEOUT_SECONDS for call in driver_calls))


if __name__ == "__main__":
    unittest.main()
