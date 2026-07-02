import inspect
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generation_agent_provider import build_opencode_command, repair_generation, resolve_diagnostics
from timeout_policy import JUDGING_PLATFORM_TIMEOUT_MINUTES, JUDGING_PLATFORM_TIMEOUT_SECONDS


class GenerationAgentProviderTests(unittest.TestCase):
    def test_default_timeout_matches_judging_platform(self):
        self.assertEqual(JUDGING_PLATFORM_TIMEOUT_MINUTES, 600)
        self.assertEqual(JUDGING_PLATFORM_TIMEOUT_SECONDS, 36_000)
        default = inspect.signature(repair_generation).parameters["timeout_seconds"].default
        self.assertEqual(default, JUDGING_PLATFORM_TIMEOUT_SECONDS)

    def test_opencode_command_uses_noninteractive_project_scope(self):
        command = build_opencode_command("/usr/bin/opencode", Path("/tmp/project"), "repair this", "provider/model")
        self.assertEqual(command[:2], ["/usr/bin/opencode", "run"])
        self.assertIn("--dir", command)
        self.assertIn("--dangerously-skip-permissions", command)
        self.assertEqual(command[-3:], ["--model", "provider/model", "repair this"])

    def test_windows_powershell_wrapper_is_argv(self):
        with patch("generation_agent_provider.shutil.which", return_value="pwsh.exe"):
            command = build_opencode_command(r"C:\tools\opencode.ps1", Path(r"C:\project with spaces"), "repair")
        self.assertEqual(command[:6], ["pwsh.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", r"C:\tools\opencode.ps1"])

    def test_diagnostics_resolve_only_for_exactly_one_real_function(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            (project / "src").mkdir()
            (project / "src" / "lib.rs").write_text(
                "pub fn complete() {}\nfn duplicate() {}\nfn duplicate() {}\nconst missing: &str = \"fn missing()\";\n",
                encoding="utf-8",
            )
            diagnostics = resolve_diagnostics(project, [
                {"symbol": "complete"}, {"symbol": "duplicate"}, {"symbol": "missing"}, {"symbol": "if"},
            ])
            self.assertEqual([item["resolved"] for item in diagnostics], [True, False, False, False])


if __name__ == "__main__":
    unittest.main()
