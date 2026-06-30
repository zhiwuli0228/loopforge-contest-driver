import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from unittest.mock import patch

from c2rust_repair import _external_repair_command, _run_external_repair_provider
from codex_repair_provider import build_codex_command


class ExternalRepairProviderTests(unittest.TestCase):
    def test_unavailable_provider_is_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = SimpleNamespace(config={"execution": {"repair_provider": {"enabled": False}}}, paths=SimpleNamespace(migration_trace_dir=root))
            result = _run_external_repair_provider(packet, root, {"command": "cargo build"}, 0, 10)
            self.assertFalse(result["applied"])
            self.assertEqual(result["detail"], "repair_provider_unavailable")

    def test_provider_receives_failure_packet_and_can_modify_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "trace"
            trace.mkdir()
            fixer = root / "fixer.py"
            fixer.write_text(
                "import json, pathlib, sys\n"
                "task=json.loads(pathlib.Path(sys.argv[1]).read_text())\n"
                "pathlib.Path(task['project_dir'], 'fixed.txt').write_text(task['failed_command'])\n",
                encoding="utf-8",
            )
            packet = SimpleNamespace(
                config={"execution": {"repair_provider": {"command": [sys.executable, str(fixer), "{task_packet}"]}}},
                paths=SimpleNamespace(migration_trace_dir=trace),
            )
            failure = {"command": "cargo build", "returncode": 101, "stdout_tail": [], "stderr_tail": ["boom"]}
            result = _run_external_repair_provider(packet, root, failure, 0, 10)
            self.assertTrue(result["applied"])
            self.assertEqual((root / "fixed.txt").read_text(), "cargo build")
            task = json.loads((trace / "repair-task-01.json").read_text())
            self.assertEqual(task["stderr_tail"], ["boom"])
            self.assertTrue((trace / "repair-provider-01.json").is_file())

    def test_auto_provider_selects_adapter_when_codex_exists(self):
        packet = SimpleNamespace(config={"execution": {"repair_provider": {"enabled": "auto", "command": None}}})
        with patch("c2rust_repair.shutil.which", side_effect=lambda name: "codex" if name == "codex" else None):
            command = _external_repair_command(packet)
        self.assertEqual(command[0], sys.executable)
        self.assertTrue(command[1].endswith("codex_repair_provider.py"))

    def test_auto_provider_is_unavailable_without_codex(self):
        packet = SimpleNamespace(config={"execution": {"repair_provider": {"enabled": "auto", "command": None}}})
        with patch("c2rust_repair.shutil.which", return_value=None):
            self.assertIsNone(_external_repair_command(packet))

    def test_windows_powershell_command_is_argv_not_shell_text(self):
        with patch("codex_repair_provider.shutil.which", return_value="pwsh.exe"):
            command = build_codex_command(r"C:\\tools\\codex.ps1", Path(r"C:\\project with spaces"))
        self.assertEqual(command[:6], ["pwsh.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", r"C:\\tools\\codex.ps1"])
        self.assertIn("workspace-write", command)
        self.assertEqual(command[-1], "-")


if __name__ == "__main__":
    unittest.main()
