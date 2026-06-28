# LoopForge Runner Source (Python)

The following code block is the source of truth for the generated runtime file `.loopforge/runtime/loopforge_runner.py`.

```python
#!/usr/bin/env python3
"""LoopForge contest runner.

This runner intentionally stays deterministic and stdlib-only. In the current
milestone it supports:

- --init
- --self-check
- --detect
- --snapshot <name>
- --prepare <task-file>
- --start-apply
- --complete-apply
- --integrate-review
- --verify
- --repair
- --finalize
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


VERSION = "0.8.0"
DEFAULT_MODE = "spec-implementation"
DEFAULT_RESULT = "RUNNING"
LOOP_ID = "loopforge-default"
ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
MAX_REPAIR_ROUNDS = 2
WORKSPACE_DIRS = [
    "runtime",
    "task",
    "spec",
    "brainstorm",
    "plan",
    "leases",
    "snapshots",
    "subagents",
    "gates",
    "state",
    "reports",
]


@dataclass
class CommandResult:
    command: List[str]
    returncode: int
    stdout: str
    stderr: str
    error: Optional[str] = None


class LoopForgeRunner:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.loopforge_dir = self.project_root / ".loopforge"
        self.state_path = self.loopforge_dir / "state" / "loop-state.json"
        self.gate_events_path = self.loopforge_dir / "gates" / "gate-events.md"
        self.verification_path = self.loopforge_dir / "state" / "verification-summary.json"
        self.review_path = self.loopforge_dir / "state" / "integrate-review-summary.json"
        self.mode_context_path = self.loopforge_dir / "state" / "mode-context.json"
        self.final_report_path = self.loopforge_dir / "reports" / "final-report.md"
        self.fallback_report_path = self.project_root / "LOOPFORGE_FINAL_REPORT.md"

    def utc_now(self) -> str:
        return datetime.now(timezone.utc).strftime(ISO_FORMAT)

    def ensure_workspace(self) -> None:
        self.loopforge_dir.mkdir(parents=True, exist_ok=True)
        for name in WORKSPACE_DIRS:
            (self.loopforge_dir / name).mkdir(parents=True, exist_ok=True)

    def load_state(self) -> Dict[str, object]:
        if self.state_path.exists():
            try:
                state = json.loads(self.state_path.read_text(encoding="utf-8"))
                if isinstance(state, dict):
                    state["version"] = VERSION
                    return state
            except json.JSONDecodeError:
                pass
        timestamp = self.utc_now()
        return {
            "loop_id": LOOP_ID,
            "version": VERSION,
            "mode": DEFAULT_MODE,
            "project_type": "unknown",
            "phase": "BOOTSTRAP",
            "repair_round": 0,
            "result": DEFAULT_RESULT,
            "created_at": timestamp,
            "updated_at": timestamp,
        }

    def save_state(self, state: Dict[str, object]) -> None:
        state["updated_at"] = self.utc_now()
        self.state_path.write_text(
            json.dumps(state, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )

    def save_json(self, path: Path, payload: Dict[str, object]) -> None:
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )

    def load_json(self, path: Path) -> Dict[str, object]:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                return {}
        return {}

    def ensure_gate_log(self) -> None:
        if not self.gate_events_path.exists():
            self.gate_events_path.write_text(
                "# Gate Events\n\n| Phase | Gate | Status | Action | Reason |\n"
                "|---|---|---|---|---|\n",
                encoding="utf-8",
            )

    def reset_gate_log(self) -> None:
        self.gate_events_path.write_text(
            "# Gate Events\n\n| Phase | Gate | Status | Action | Reason |\n"
            "|---|---|---|---|---|\n",
            encoding="utf-8",
        )

    def record_gate_event(
        self,
        phase: str,
        gate: str,
        status: str,
        action: str,
        reason: str,
    ) -> None:
        self.ensure_gate_log()
        safe_reason = " ".join(reason.replace("|", "/").split())
        safe_action = " ".join(action.replace("|", "/").split())
        line = f"| {phase} | {gate} | {status} | {safe_action} | {safe_reason} |\n"
        with self.gate_events_path.open("a", encoding="utf-8") as handle:
            handle.write(line)

    def self_check(self) -> Dict[str, object]:
        checks = {
            "python_executable": sys.executable,
            "python_version": sys.version.split()[0],
            "project_root_exists": self.project_root.exists(),
            "loopforge_exists": self.loopforge_dir.exists(),
            "state_path": str(self.state_path),
            "git_available": shutil.which("git") is not None,
        }
        ok = all(
            [
                checks["python_executable"],
                checks["project_root_exists"],
                checks["loopforge_exists"],
            ]
        )
        return {"ok": bool(ok), "checks": checks}

    def run_command(self, command: List[str]) -> CommandResult:
        try:
            completed = subprocess.run(
                command,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=False,
            )
            return CommandResult(
                command=command,
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        except OSError as exc:
            return CommandResult(
                command=command,
                returncode=1,
                stdout="",
                stderr="",
                error=str(exc),
            )

    def command_available(self, command: str) -> bool:
        return shutil.which(command) is not None

    def list_repo_files(self) -> List[Path]:
        ignored_roots = {".git", ".loopforge"}
        files: List[Path] = []
        for path in self.project_root.rglob("*"):
            if not path.is_file():
                continue
            parts = set(path.relative_to(self.project_root).parts)
            if parts & ignored_roots:
                continue
            files.append(path)
        return files

    def select_mode(self, task_text: str) -> str:
        text = task_text.lower()
        if any(token in text for token in ["不一致", "偏差"]):
            return "spec-code-drift"
        if re.search(r"\b(drift|traceability)\b", text) or "inconsisten" in text:
            return "spec-code-drift"
        if any(token in text for token in ["测试"]):
            return "test-generation"
        if re.search(r"\b(test|tests|pytest|junit)\b", text) or "spec file" in text:
            return "test-generation"
        if any(token in text for token in ["代码质量", "修复质量"]):
            return "clean-code-repair"
        if re.search(r"\b(repair|clean code)\b", text) or "fix quality" in text:
            return "clean-code-repair"
        return "spec-implementation"

    def extract_requirements(self, task_text: str) -> List[str]:
        candidates: List[str] = []
        for raw_line in task_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            line = re.sub(r"^[\-\*\d\.\)\s]+", "", line).strip()
            if line:
                candidates.append(line)
        if not candidates:
            collapsed = " ".join(task_text.split())
            if collapsed:
                candidates.append(collapsed)
        return candidates[:5]

    def candidate_target_files(self, project_type: str) -> List[str]:
        files = self.list_repo_files()
        ranked: List[Path] = []
        disallowed_names = {"pom.xml", "build.gradle", "package-lock.json", "yarn.lock"}
        if project_type == "java-maven":
            ranked.extend(sorted([p for p in files if "src" in p.parts and p.suffix == ".java"]))
        elif project_type == "python":
            ranked.extend(sorted([p for p in files if p.suffix == ".py"]))
        elif project_type == "node":
            ranked.extend(sorted([p for p in files if p.suffix in {".js", ".ts", ".tsx", ".jsx"}]))
        elif project_type == "go":
            ranked.extend(sorted([p for p in files if p.suffix == ".go"]))
        ranked = [p for p in ranked if p.name not in disallowed_names]
        return [str(path.relative_to(self.project_root)) for path in ranked[:3]]

    def candidate_test_files(self, project_type: str) -> List[str]:
        files = self.list_repo_files()
        ranked: List[Path] = []
        if project_type == "java-maven":
            ranked.extend(sorted([p for p in files if "src" in p.parts and "test" in p.parts and p.suffix == ".java"]))
        elif project_type == "python":
            ranked.extend(sorted([p for p in files if p.name.startswith("test_") or p.name.endswith("_test.py")]))
        elif project_type == "node":
            ranked.extend(sorted([p for p in files if ".test." in p.name or ".spec." in p.name]))
        elif project_type == "go":
            ranked.extend(sorted([p for p in files if p.name.endswith("_test.go")]))
        return [str(path.relative_to(self.project_root)) for path in ranked[:3]]

    def existing_test_style(self, project_type: str, test_files: List[str]) -> str:
        if project_type == "java-maven":
            if test_files:
                return "Reuse existing Maven test layout under src/test."
            return "Prefer src/test/java with project-consistent JUnit style."
        if project_type == "python":
            if test_files:
                return "Reuse the detected pytest-style file naming."
            return "Prefer pytest-style tests in existing test directories."
        if project_type == "node":
            if test_files:
                return "Reuse the detected .test/.spec naming convention."
            return "Prefer colocated .test or .spec files."
        if project_type == "go":
            return "Prefer _test.go files beside the target package."
        return "Reuse existing repository test conventions if they exist."

    def test_target_summary(self, requirements: List[str]) -> List[str]:
        targets: List[str] = []
        for index, item in enumerate(requirements[:3], start=1):
            targets.append(f"- TT-{index:03d}: Cover behavior implied by `{item}`.")
        if not targets:
            targets.append("- TT-001: Add the smallest useful test coverage for the requested behavior.")
        return targets

    def save_mode_context(self, payload: Dict[str, object]) -> None:
        self.save_json(self.mode_context_path, payload)

    def reset_run_artifacts(self) -> None:
        self.ensure_workspace()
        self.reset_gate_log()
        paths_to_remove = [
            self.verification_path,
            self.review_path,
            self.mode_context_path,
            self.final_report_path,
            self.loopforge_dir / "task" / "task.md",
            self.loopforge_dir / "spec" / "normalized-spec.md",
            self.loopforge_dir / "spec" / "traceability-matrix.md",
            self.loopforge_dir / "brainstorm" / "brainstorm.md",
            self.loopforge_dir / "plan" / "execution-plan.md",
            self.loopforge_dir / "leases" / "lease-001.md",
            self.loopforge_dir / "subagents" / "lease-001-report.md",
            self.loopforge_dir / "snapshots" / "before-apply.diff",
            self.loopforge_dir / "snapshots" / "after-apply.diff",
            self.loopforge_dir / "snapshots" / "before-verify.diff",
            self.loopforge_dir / "snapshots" / "after-repair.diff",
        ]
        for path in paths_to_remove:
            if path.exists():
                path.unlink()

    def write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")

    def replace_markdown_section(self, path: Path, heading: str, body_lines: List[str]) -> None:
        if not path.exists():
            return
        lines = path.read_text(encoding="utf-8").splitlines()
        target = f"## {heading}"
        start_index: Optional[int] = None
        end_index: Optional[int] = None
        for index, line in enumerate(lines):
            if line.strip() == target:
                start_index = index
                continue
            if start_index is not None and line.strip().startswith("## "):
                end_index = index
                break
        if start_index is None:
            return
        if end_index is None:
            end_index = len(lines)
        replacement = [target, ""] + body_lines + [""]
        new_lines = lines[:start_index] + replacement + lines[end_index:]
        path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")

    def parse_markdown_section_lines(self, path: Path, heading: str) -> List[str]:
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        target = f"## {heading}"
        capture = False
        collected: List[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped == target:
                capture = True
                continue
            if capture and stripped.startswith("## "):
                break
            if capture:
                if stripped:
                    collected.append(stripped)
        return collected

    def parse_lease(self) -> Dict[str, object]:
        lease_path = self.loopforge_dir / "leases" / "lease-001.md"
        allowed_lines = self.parse_markdown_section_lines(lease_path, "Allowed Files")
        forbidden_lines = self.parse_markdown_section_lines(lease_path, "Forbidden Files")
        max_changed_lines = self.parse_markdown_section_lines(lease_path, "Max Changed Files")
        max_diff_lines = self.parse_markdown_section_lines(lease_path, "Max Diff Lines")
        report_lines = self.parse_markdown_section_lines(lease_path, "Required Report")
        assigned_task_lines = self.parse_markdown_section_lines(lease_path, "Assigned Task")
        return {
            "lease_path": str(lease_path),
            "allowed_files": [line[2:].strip() for line in allowed_lines if line.startswith("- ")],
            "forbidden_files": [line[2:].strip() for line in forbidden_lines if line.startswith("- ")],
            "max_changed_files": int(max_changed_lines[0]) if max_changed_lines and max_changed_lines[0].isdigit() else 3,
            "max_diff_lines": int(max_diff_lines[0]) if max_diff_lines and max_diff_lines[0].isdigit() else 250,
            "required_report": report_lines[0] if report_lines else ".loopforge/subagents/lease-001-report.md",
            "assigned_task": " ".join(assigned_task_lines).strip(),
        }

    def allowed_file_violations(self, changed_files: List[str], allowed_files: List[str]) -> List[str]:
        allowed = [item for item in allowed_files if item and not item.startswith("To be determined")]
        if not allowed:
            return []
        violations: List[str] = []
        for path in changed_files:
            if path not in allowed:
                violations.append(path)
        return violations

    def review_exempt_file(self, path_text: str) -> bool:
        normalized = path_text.replace("/", "\\")
        return normalized.startswith(".loopforge\\")

    def matches_pattern(self, path_text: str, pattern: str) -> bool:
        normalized = path_text.replace("/", "\\")
        rule = pattern.replace("/", "\\")
        if rule.endswith("\\**"):
            return normalized.startswith(rule[:-3])
        return normalized == rule

    def collect_diff_line_count(self) -> Optional[int]:
        if shutil.which("git") is None:
            return None
        probe = self.run_command(["git", "rev-parse", "--is-inside-work-tree"])
        if probe.error or probe.returncode != 0 or probe.stdout.strip().lower() != "true":
            return None
        result = self.run_command(["git", "diff", "--numstat"])
        if result.error or result.returncode != 0:
            return None
        total = 0
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) < 3:
                continue
            try:
                added = 0 if parts[0] == "-" else int(parts[0])
                deleted = 0 if parts[1] == "-" else int(parts[1])
            except ValueError:
                continue
            total += added + deleted
        return total

    def detect_project(self) -> Dict[str, object]:
        indicators: Dict[str, bool] = {
            "pom.xml": (self.project_root / "pom.xml").exists(),
            "mvnw": (self.project_root / "mvnw").exists(),
            "mvnw.cmd": (self.project_root / "mvnw.cmd").exists(),
            "pyproject.toml": (self.project_root / "pyproject.toml").exists(),
            "requirements.txt": (self.project_root / "requirements.txt").exists(),
            "pytest.ini": (self.project_root / "pytest.ini").exists(),
            "package.json": (self.project_root / "package.json").exists(),
            "go.mod": (self.project_root / "go.mod").exists(),
        }

        project_type = "unknown"
        if indicators["pom.xml"] or indicators["mvnw"] or indicators["mvnw.cmd"]:
            project_type = "java-maven"
        elif indicators["pyproject.toml"] or indicators["requirements.txt"] or indicators["pytest.ini"]:
            project_type = "python"
        elif indicators["package.json"]:
            project_type = "node"
        elif indicators["go.mod"]:
            project_type = "go"

        state = self.load_state()
        state["project_type"] = project_type
        state["phase"] = "MODE_SELECT"
        self.save_state(state)
        return {"project_type": project_type, "indicators": indicators}

    def prepare_workflow(self, task_file: str) -> Dict[str, object]:
        self.ensure_workspace()
        self.reset_run_artifacts()
        task_path = Path(task_file)
        if not task_path.is_absolute():
            task_path = (self.project_root / task_path).resolve()
        if not task_path.exists():
            return {"ok": False, "error": f"task file not found: {task_path}"}

        task_text = task_path.read_text(encoding="utf-8").strip()
        if not task_text:
            return {"ok": False, "error": f"task file is empty: {task_path}"}

        detection = self.detect_project()
        project_type = str(detection["project_type"])
        mode = self.select_mode(task_text)
        requirements = self.extract_requirements(task_text)
        confidence = "LOW" if len(requirements) <= 1 else "MEDIUM"
        target_files = self.candidate_target_files(project_type)
        test_files = self.candidate_test_files(project_type)
        test_style = self.existing_test_style(project_type, test_files)

        task_output = self.loopforge_dir / "task" / "task.md"
        spec_output = self.loopforge_dir / "spec" / "normalized-spec.md"
        traceability_output = self.loopforge_dir / "spec" / "traceability-matrix.md"
        brainstorm_output = self.loopforge_dir / "brainstorm" / "brainstorm.md"
        plan_output = self.loopforge_dir / "plan" / "execution-plan.md"
        lease_output = self.loopforge_dir / "leases" / "lease-001.md"

        self.write_text(
            task_output,
            "\n".join(
                [
                    "# Task",
                    "",
                    "## Source",
                    "",
                    str(task_path),
                    "",
                    "## Selected Mode",
                    "",
                    mode,
                    "",
                    "## Raw Task",
                    "",
                    task_text,
                ]
            ),
        )

        requirement_lines = [f"- REQ-{index:03d}: {item}" for index, item in enumerate(requirements, start=1)]
        acceptance_lines = [f"- AC-{index:03d}: Deliver an observable outcome for {item}" for index, item in enumerate(requirements[:3], start=1)]
        if not acceptance_lines:
            acceptance_lines = ["- AC-001: Produce a minimal change aligned with the provided task."]
        if mode == "test-generation":
            acceptance_lines = [f"- AC-{index:03d}: Add or update a test that exercises `{item}`." for index, item in enumerate(requirements[:3], start=1)]
            if not acceptance_lines:
                acceptance_lines = ["- AC-001: Add the smallest useful test covering the requested behavior."]
        elif mode == "spec-code-drift":
            acceptance_lines = [f"- AC-{index:03d}: Determine whether `{item}` is implemented, tested, or missing." for index, item in enumerate(requirements[:3], start=1)]
            if not acceptance_lines:
                acceptance_lines = ["- AC-001: Produce a minimal traceability and drift summary for the requested behavior."]
        self.write_text(
            spec_output,
            "\n".join(
                [
                    "# Normalized Spec",
                    "",
                    "## Mode",
                    "",
                    mode,
                    "",
                    "## Requirements",
                    "",
                    *requirement_lines,
                    "",
                    "## Acceptance Criteria",
                    "",
                    *acceptance_lines,
                    "",
                    "## Constraints",
                    "",
                    "- C-001: Prefer minimal file changes.",
                    "- C-002: Do not introduce third-party dependencies in the driver.",
                    "- C-003: Keep changes within the current work tree.",
                    "",
                    "## Unknowns",
                    "",
                    "- U-001: Exact target files may require repository inspection by the coding agent.",
                    "- U-002: Verification depth depends on detected project type and local tooling.",
                    "",
                    "## Confidence",
                    "",
                    confidence,
                ]
            ),
        )

        brainstorm_target_lines = [f"- {item}" for item in target_files] or ["- No strong target candidates detected."]
        brainstorm_test_lines = [f"- {item}" for item in test_files] or ["- No existing test candidates detected."]
        brainstorm_understanding = [
            f"- The selected mode is `{mode}`.",
            f"- The detected project type is `{project_type}`.",
        ]
        brainstorm_scope = [
            "- Normalize the task.",
            "- Inspect candidate files.",
            "- Apply the smallest change consistent with the normalized spec.",
            "- Run verification and finalize a report.",
        ]
        brainstorm_risks = [
            "- Target files may not be uniquely identifiable from deterministic heuristics.",
            "- Verification may degrade if the required toolchain is unavailable.",
        ]
        if mode == "test-generation":
            brainstorm_understanding.append("- The primary objective is to add or extend tests rather than business logic.")
            brainstorm_scope = [
                "- Identify the behavior that needs coverage.",
                "- Inspect existing test layout and naming conventions.",
                "- Add the smallest test change aligned with the normalized spec.",
                "- Run verification and finalize a report.",
            ]
            brainstorm_risks = [
                "- The behavior under test may be underspecified by the task text.",
                "- Existing test style may not be obvious if the repository has sparse coverage.",
            ]
        elif mode == "spec-code-drift":
            brainstorm_understanding.append("- The primary objective is to compare stated requirements against implementation and test evidence.")
            brainstorm_scope = [
                "- Identify requirements that need traceability.",
                "- Inspect likely implementation files and test files.",
                "- Record implemented, missing, or unverified behaviors.",
                "- Finalize a drift-oriented report.",
            ]
            brainstorm_risks = [
                "- Drift findings may be low confidence if the repository structure is sparse.",
                "- Deterministic heuristics may miss indirect implementations or implicit behavior.",
            ]
        self.write_text(
            brainstorm_output,
            "\n".join(
                [
                    "# Brainstorm",
                    "",
                    "## Task Understanding",
                    "",
                    *brainstorm_understanding,
                    "",
                    "## Key Assumptions",
                    "",
                    "- The task can be advanced with a minimal-file change set.",
                    "- Existing project conventions should be preserved.",
                    "",
                    "## Risk Areas",
                    "",
                    *brainstorm_risks,
                    "",
                    "## Candidate Target Files",
                    "",
                    *brainstorm_target_lines,
                    "",
                    "## Candidate Test Files",
                    "",
                    *brainstorm_test_lines,
                    "",
                    "## Questions Resolved by Assumption",
                    "",
                    "- Assume the smallest plausible implementation scope unless the task text clearly requires broader changes.",
                    "",
                    "## Suggested Execution Scope",
                    "",
                    *brainstorm_scope,
                ]
            ),
        )

        plan_target_lines = [f"- {item}" for item in target_files] or ["- To be determined by repository inspection."]
        plan_test_lines = [f"- {item}" for item in test_files] or ["- Reuse existing test layout if present; otherwise document the gap."]
        test_strategy_lines = [f"- {test_style}"]
        if mode == "test-generation":
            test_strategy_lines.extend(self.test_target_summary(requirements))
        plan_steps = [
            "1. Inspect the candidate files and confirm the smallest valid implementation surface.",
            "2. Apply the minimal change aligned with the normalized spec.",
            "3. Add or adjust tests when the mode and project structure require them.",
            "4. Run LoopForge verification.",
            "5. Generate the final report.",
        ]
        if mode == "test-generation":
            plan_steps = [
                "1. Inspect existing tests and infer the repository test style.",
                "2. Identify the smallest test surface that covers the requested behavior.",
                "3. Add or update tests without expanding the business requirement.",
                "4. Run LoopForge verification.",
                "5. Generate the final report with test coverage traceability.",
            ]
        elif mode == "spec-code-drift":
            plan_steps = [
                "1. Inspect candidate implementation and test files.",
                "2. Build a lightweight requirement-to-code/test traceability matrix.",
                "3. Record missing implementation, missing tests, or low-confidence coverage.",
                "4. Avoid broad repository changes unless explicitly required.",
                "5. Generate the final report with drift findings.",
            ]
        self.write_text(
            plan_output,
            "\n".join(
                [
                    "# Execution Plan",
                    "",
                    "## Objective",
                    "",
                    task_text,
                    "",
                    "## Selected Mode",
                    "",
                    mode,
                    "",
                    "## Project Type",
                    "",
                    project_type,
                    "",
                    "## Target Files",
                    "",
                    *plan_target_lines,
                    "",
                    "## Test Files",
                    "",
                    *plan_test_lines,
                    "",
                    "## Test Strategy",
                    "",
                    *test_strategy_lines,
                    "",
                    "## Steps",
                    "",
                    *plan_steps,
                    "",
                    "## Verification Plan",
                    "",
                    "- Use the runner verification sequence for the detected project type." if mode != "spec-code-drift" else "- Verification is optional for drift mode; prioritize evidence collection and traceability.",
                    "",
                    "## Rollback / Degrade Plan",
                    "",
                    "- If validation fails and no focused repair is available, finalize as DEGRADED_DONE with evidence.",
                ]
            ),
        )

        drift_findings: List[str] = []
        implementation_candidates = target_files[:3]
        test_candidates = test_files[:3]
        traceability_lines = [
            "# Traceability Matrix",
            "",
            "| Requirement | Implementation Evidence | Test Evidence | Status | Confidence |",
            "|---|---|---|---|---|",
        ]
        for item in requirements[:5]:
            impl = implementation_candidates[0] if implementation_candidates else "No clear implementation candidate"
            test = test_candidates[0] if test_candidates else "No clear test candidate"
            status = "UNVERIFIED"
            confidence_label = "LOW"
            if implementation_candidates and test_candidates:
                status = "PARTIAL"
                confidence_label = "MEDIUM"
                drift_findings.append(f"- Requirement `{item}` has candidate implementation and test evidence but remains unverified.")
            elif implementation_candidates and not test_candidates:
                status = "TEST_GAP"
                confidence_label = "MEDIUM"
                drift_findings.append(f"- Requirement `{item}` has candidate implementation evidence but no clear test evidence.")
            elif not implementation_candidates and test_candidates:
                status = "IMPLEMENTATION_GAP"
                confidence_label = "LOW"
                drift_findings.append(f"- Requirement `{item}` has candidate test evidence but no clear implementation evidence.")
            else:
                drift_findings.append(f"- Requirement `{item}` has no clear implementation or test evidence from deterministic heuristics.")
            traceability_lines.append(f"| {item} | {impl} | {test} | {status} | {confidence_label} |")
        if len(traceability_lines) == 4:
            traceability_lines.append("| No normalized requirement | No evidence | No evidence | UNVERIFIED | LOW |")
            drift_findings.append("- No normalized requirements were available for drift analysis.")
        self.write_text(traceability_output, "\n".join(traceability_lines))

        if mode == "test-generation":
            allowed_files = test_files[:]
            allowed_files.extend([item for item in target_files if item not in allowed_files])
        elif mode == "spec-code-drift":
            allowed_files = test_files[:]
            allowed_files.extend([item for item in target_files if item not in allowed_files])
        else:
            allowed_files = target_files[:]
            allowed_files.extend([item for item in test_files if item not in allowed_files])
        allowed_files = allowed_files[:3]
        allowed_file_lines = [f"- {item}" for item in allowed_files] or ["- To be determined after inspection."]
        allowed_commands = self.verification_commands_for(project_type)
        allowed_command_lines = [f"- {' '.join(command)}" for command in allowed_commands] or ["- No executable verifier for the detected project type in this milestone."]
        self.write_text(
            lease_output,
            "\n".join(
                [
                    "# Write Lease",
                    "",
                    "## Lease ID",
                    "",
                    "lease-001",
                    "",
                    "## Assigned Task",
                    "",
                    task_text,
                    "",
                    "## Allowed Files",
                    "",
                    *allowed_file_lines,
                    "",
                    "## Forbidden Files",
                    "",
                    "- pom.xml",
                    "- build.gradle",
                    "- package-lock.json",
                    "- yarn.lock",
                    "- src/main/resources/**",
                    "- .github/**",
                    "- .git/**",
                    "",
                    "## Max Changed Files",
                    "",
                    "3",
                    "",
                    "## Max Diff Lines",
                    "",
                    "250",
                    "",
                    "## Allowed Commands",
                    "",
                    *allowed_command_lines,
                    "",
                    "## Required Report",
                    "",
                    ".loopforge/subagents/lease-001-report.md",
                ]
            ),
        )

        state = self.load_state()
        state["mode"] = mode
        state["project_type"] = project_type
        state["phase"] = "PLAN"
        state["repair_round"] = 0
        state["result"] = DEFAULT_RESULT
        self.save_state(state)
        self.save_mode_context(
            {
                "mode": mode,
                "project_type": project_type,
                "requirements": requirements,
                "target_files": target_files,
                "test_files": test_files,
                "test_style": test_style,
                "traceability_matrix": str(traceability_output),
                "drift_findings": drift_findings,
            }
        )

        return {
            "ok": True,
            "mode": mode,
            "project_type": project_type,
            "outputs": {
                "task": str(task_output),
                "spec": str(spec_output),
                "traceability": str(traceability_output),
                "brainstorm": str(brainstorm_output),
                "plan": str(plan_output),
                "lease": str(lease_output),
            },
        }

    def start_apply(self) -> Dict[str, object]:
        self.ensure_workspace()
        lease = self.parse_lease()
        report_path = self.project_root / lease["required_report"]
        self.snapshot_diff("before-apply")
        self.write_text(
            report_path,
            "\n".join(
                [
                    "# Subagent Report",
                    "",
                    "## Lease ID",
                    "",
                    "lease-001",
                    "",
                    "## Assigned Task",
                    "",
                    str(lease["assigned_task"]),
                    "",
                    "## Changed Files",
                    "",
                    "- None yet.",
                    "",
                    "## Summary",
                    "",
                    "Pending implementation.",
                    "",
                    "## Verification Performed",
                    "",
                    "- None yet.",
                    "",
                    "## Known Risks",
                    "",
                    "- To be filled after apply.",
                    "",
                    "## Deviations From Lease",
                    "",
                    "None",
                ]
            ),
        )
        state = self.load_state()
        state["phase"] = "APPLY"
        self.save_state(state)
        return {
            "ok": True,
            "snapshot": str(self.loopforge_dir / "snapshots" / "before-apply.diff"),
            "subagent_report": str(report_path),
        }

    def complete_apply(self) -> Dict[str, object]:
        self.ensure_workspace()
        lease = self.parse_lease()
        report_path = self.project_root / str(lease["required_report"])
        changed_files = self.collect_changed_files()
        diff_lines = self.collect_diff_line_count()

        changed_body = [f"- {path}" for path in changed_files] or ["- No changed files detected."]
        summary_body = [
            "Applied repository changes after the apply phase."
            if changed_files
            else "No repository changes were detected after the apply phase."
        ]
        verification_body = ["- Verification not yet recorded by complete-apply."]
        risk_body = []
        if diff_lines is not None:
            risk_body.append(f"- Current diff line count: {diff_lines}.")
        else:
            risk_body.append("- Diff line count unavailable.")
        if not changed_files:
            risk_body.append("- No changed files detected; implementation may still be pending.")
        deviation_body = ["None"]

        self.replace_markdown_section(report_path, "Changed Files", changed_body)
        self.replace_markdown_section(report_path, "Summary", summary_body)
        self.replace_markdown_section(report_path, "Verification Performed", verification_body)
        self.replace_markdown_section(report_path, "Known Risks", risk_body)
        self.replace_markdown_section(report_path, "Deviations From Lease", deviation_body)

        state = self.load_state()
        state["phase"] = "APPLY"
        self.save_state(state)
        return {
            "ok": True,
            "subagent_report": str(report_path),
            "changed_files": changed_files,
            "diff_line_count": diff_lines,
        }

    def run_integrate_review(self) -> Dict[str, object]:
        self.ensure_workspace()
        lease = self.parse_lease()
        self.snapshot_diff("after-apply")
        changed_files = self.collect_changed_files()
        review_changed_files = [path for path in changed_files if not self.review_exempt_file(path)]
        diff_lines = self.collect_diff_line_count()
        allowed_violations = self.allowed_file_violations(review_changed_files, lease["allowed_files"])
        forbidden_hits = [
            path for path in review_changed_files
            if any(self.matches_pattern(path, pattern) for pattern in lease["forbidden_files"])
        ]
        exceeds_changed_files = len(review_changed_files) > int(lease["max_changed_files"])
        exceeds_diff_lines = diff_lines is not None and diff_lines > int(lease["max_diff_lines"])
        report_path = self.project_root / str(lease["required_report"])
        report_exists = report_path.exists()
        allowed_scope_unresolved = (
            not [item for item in lease["allowed_files"] if item and not item.startswith("To be determined")]
            and bool(review_changed_files)
        )

        issues: List[str] = []
        status = "PASS"
        if forbidden_hits:
            status = "BLOCK"
            issues.append("forbidden files were modified")
        if allowed_scope_unresolved:
            status = "WARN" if status == "PASS" else status
            issues.append("lease allowed file scope was unresolved while repository changes were detected")
        if allowed_violations:
            status = "WARN" if status == "PASS" else status
            issues.append("files outside allowed lease scope were modified")
        if exceeds_changed_files:
            status = "WARN" if status == "PASS" else status
            issues.append("max changed files exceeded")
        if exceeds_diff_lines:
            status = "WARN" if status == "PASS" else status
            issues.append("max diff lines exceeded")
        if not report_exists:
            status = "WARN" if status == "PASS" else status
            issues.append("subagent report missing")

        if not issues:
            issues.append("no integration review issues detected")

        summary = {
            "ok": status == "PASS",
            "status": status,
            "changed_files": changed_files,
            "changed_file_count": len(review_changed_files),
            "review_changed_files": review_changed_files,
            "diff_line_count": diff_lines,
            "allowed_scope_violations": allowed_violations,
            "allowed_scope_unresolved": allowed_scope_unresolved,
            "forbidden_hits": forbidden_hits,
            "subagent_report_exists": report_exists,
            "issues": issues,
        }
        self.save_json(self.review_path, summary)
        self.record_gate_event(
            "INTEGRATE_REVIEW",
            "lease",
            status,
            "review workspace against lease",
            "; ".join(issues),
        )
        state = self.load_state()
        state["phase"] = "INTEGRATE_REVIEW"
        if status == "BLOCK":
            state["result"] = "BLOCKED"
        elif status == "WARN" and str(state.get("result", DEFAULT_RESULT)) == DEFAULT_RESULT:
            state["result"] = "PARTIAL_DONE"
        self.save_state(state)
        return summary

    def snapshot_diff(self, name: str) -> Dict[str, object]:
        snapshot_path = self.loopforge_dir / "snapshots" / f"{name}.diff"
        if shutil.which("git") is None:
            snapshot_path.write_text(
                "git not available; snapshot could not be collected\n",
                encoding="utf-8",
            )
            self.record_gate_event(
                "SNAPSHOT",
                "git",
                "WARN",
                f"write placeholder snapshot {name}",
                "git executable not available",
            )
            return {
                "ok": False,
                "snapshot": str(snapshot_path),
                "reason": "git executable not available",
            }

        probe = self.run_command(["git", "rev-parse", "--is-inside-work-tree"])
        if probe.error or probe.returncode != 0 or probe.stdout.strip().lower() != "true":
            reason = "current directory is not a git work tree"
            snapshot_path.write_text(
                "git work tree not detected; snapshot could not be collected\n",
                encoding="utf-8",
            )
            self.record_gate_event(
                "SNAPSHOT",
                "git",
                "WARN",
                f"write placeholder snapshot {name}",
                reason,
            )
            return {
                "ok": False,
                "snapshot": str(snapshot_path),
                "reason": reason,
            }

        result = self.run_command(["git", "diff"])
        content = result.stdout
        if result.error:
            content = f"git diff execution error: {result.error}\n"
            self.record_gate_event(
                "SNAPSHOT",
                "git",
                "WARN",
                f"write error snapshot {name}",
                result.error,
            )
        elif result.returncode != 0:
            reason = result.stderr.strip().splitlines()[0] if result.stderr.strip() else f"git diff exited with {result.returncode}"
            content = f"git diff failed: {reason}\n"
            self.record_gate_event(
                "SNAPSHOT",
                "git",
                "WARN",
                f"write failed snapshot {name}",
                reason.replace("|", "/"),
            )

        snapshot_path.write_text(content, encoding="utf-8")
        return {"ok": result.returncode == 0 and not result.error, "snapshot": str(snapshot_path)}

    def init_workspace(self) -> Dict[str, object]:
        self.ensure_workspace()
        self.ensure_gate_log()
        state = self.load_state()
        state["phase"] = "BOOTSTRAP"
        self.save_state(state)
        return {
            "ok": True,
            "loopforge_dir": str(self.loopforge_dir),
            "state_path": str(self.state_path),
        }

    def verification_commands_for(self, project_type: str) -> List[List[str]]:
        if project_type != "java-maven":
            return []

        commands: List[List[str]] = []
        if os.name == "nt":
            if (self.project_root / "mvnw.cmd").exists():
                commands.append(["mvnw.cmd", "test"])
        else:
            if (self.project_root / "mvnw").exists():
                commands.append(["./mvnw", "test"])
        commands.append(["mvn", "test"])
        commands.append(["mvn", "-q", "-DskipTests", "package"])
        return commands

    def summarize_command_result(self, result: CommandResult) -> Dict[str, object]:
        return {
            "command": result.command,
            "returncode": result.returncode,
            "ok": result.returncode == 0 and result.error is None,
            "stdout_tail": result.stdout.strip().splitlines()[-20:],
            "stderr_tail": result.stderr.strip().splitlines()[-20:],
            "error": result.error,
        }

    def verify_project(self) -> Dict[str, object]:
        self.ensure_workspace()
        state = self.load_state()
        project_type = str(state.get("project_type", "unknown"))
        if project_type == "unknown":
            detection = self.detect_project()
            project_type = str(detection["project_type"])
            state = self.load_state()

        self.snapshot_diff("before-verify")
        state["phase"] = "VERIFY"
        self.save_state(state)

        commands = self.verification_commands_for(project_type)
        if not commands:
            summary = {
                "ok": False,
                "project_type": project_type,
                "commands_attempted": [],
                "status": "degraded",
                "reason": f"verification not implemented for project type: {project_type}",
                "next_step": "finalize",
            }
            self.save_json(self.verification_path, summary)
            state["result"] = "DEGRADED_DONE"
            self.save_state(state)
            self.record_gate_event(
                "VERIFY",
                "verification",
                "DEGRADE",
                "skip unsupported verifier",
                summary["reason"],
            )
            return summary

        attempted: List[Dict[str, object]] = []
        for command in commands:
            if not self.command_available(command[0]) and not Path(command[0]).exists():
                attempted.append(
                    {
                        "command": command,
                        "returncode": 127,
                        "ok": False,
                        "stdout_tail": [],
                        "stderr_tail": [],
                        "error": f"command not available: {command[0]}",
                    }
                )
                continue

            result = self.run_command(command)
            summarized = self.summarize_command_result(result)
            attempted.append(summarized)
            if summarized["ok"]:
                summary = {
                    "ok": True,
                    "project_type": project_type,
                    "commands_attempted": attempted,
                    "status": "passed",
                    "selected_command": command,
                }
                self.save_json(self.verification_path, summary)
                state["result"] = "RUNNING"
                self.save_state(state)
                self.record_gate_event(
                    "VERIFY",
                    "verification",
                    "PASS",
                    "verification command succeeded",
                    " ".join(command),
                )
                return summary

        summary = {
            "ok": False,
            "project_type": project_type,
            "commands_attempted": attempted,
            "status": "repairable" if int(state.get("repair_round", 0)) < MAX_REPAIR_ROUNDS else "degraded",
            "reason": "all verification commands failed or were unavailable",
        }
        current_round = int(state.get("repair_round", 0))
        if current_round < MAX_REPAIR_ROUNDS:
            summary["next_step"] = "repair"
            state["result"] = "RUNNING"
            gate_status = "REPAIR"
            gate_reason = f"enter repair round {current_round + 1}"
        else:
            summary["next_step"] = "finalize"
            state["result"] = "DEGRADED_DONE"
            gate_status = "DEGRADE"
            gate_reason = "repair budget exhausted"
        self.save_json(self.verification_path, summary)
        self.save_state(state)
        self.record_gate_event(
            "VERIFY",
            "verification",
            gate_status,
            "verification failed",
            gate_reason,
        )
        return summary

    def run_repair(self) -> Dict[str, object]:
        self.ensure_workspace()
        state = self.load_state()
        verification = self.load_json(self.verification_path)
        current_round = int(state.get("repair_round", 0))

        if verification.get("ok") is True:
            return {
                "ok": True,
                "status": "skipped",
                "reason": "verification already passed; repair not needed",
                "repair_round": current_round,
            }

        if verification.get("next_step") != "repair":
            return {
                "ok": False,
                "status": "skipped",
                "reason": "verification result does not allow repair progression",
                "repair_round": current_round,
            }

        if current_round >= MAX_REPAIR_ROUNDS:
            state["phase"] = "FINALIZE"
            state["result"] = "DEGRADED_DONE"
            self.save_state(state)
            self.record_gate_event(
                "REPAIR",
                "budget",
                "DEGRADE",
                "skip repair",
                "repair budget exhausted",
            )
            return {
                "ok": False,
                "status": "degraded",
                "reason": "repair budget exhausted",
                "repair_round": current_round,
            }

        next_round = current_round + 1
        state["phase"] = "REPAIR"
        state["repair_round"] = next_round
        self.save_state(state)
        self.snapshot_diff("after-repair")
        self.record_gate_event(
            "REPAIR",
            "budget",
            "REPAIR",
            "enter repair round",
            f"repair round {next_round} of {MAX_REPAIR_ROUNDS}",
        )
        return {
            "ok": True,
            "status": "repair",
            "repair_round": next_round,
            "max_repair_rounds": MAX_REPAIR_ROUNDS,
            "snapshot": str(self.loopforge_dir / "snapshots" / "after-repair.diff"),
        }

    def read_gate_events(self) -> List[str]:
        if not self.gate_events_path.exists():
            return []
        lines = self.gate_events_path.read_text(encoding="utf-8").splitlines()
        return [line for line in lines if line.startswith("| ") and not line.startswith("|---")]

    def collect_changed_files(self) -> List[str]:
        if shutil.which("git") is None:
            return []
        probe = self.run_command(["git", "rev-parse", "--is-inside-work-tree"])
        if probe.error or probe.returncode != 0 or probe.stdout.strip().lower() != "true":
            return []
        result = self.run_command(["git", "status", "--short"])
        if result.error or result.returncode != 0:
            return []
        changed: List[str] = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            path_text = line[3:] if len(line) > 3 else line
            changed.append(path_text.strip())
        return changed

    def generate_final_report(self) -> Dict[str, object]:
        self.ensure_workspace()
        state = self.load_state()
        verification = self.load_json(self.verification_path)
        review = self.load_json(self.review_path)
        mode_context = self.load_json(self.mode_context_path)
        changed_files = self.collect_changed_files()
        gate_events = self.read_gate_events()
        result_value = str(state.get("result", DEFAULT_RESULT))

        if str(state.get("result")) == "BLOCKED":
            result_value = "BLOCKED"
        elif verification.get("ok") is True:
            result_value = "DONE"
        elif verification:
            result_value = "DEGRADED_DONE"
        elif result_value == "RUNNING":
            result_value = "PARTIAL_DONE"

        state["phase"] = "FINALIZE"
        state["result"] = result_value
        self.save_state(state)

        verification_commands = verification.get("commands_attempted", [])
        verification_lines: List[str] = []
        for item in verification_commands:
            command = " ".join(item.get("command", []))
            status = "PASS" if item.get("ok") else "FAIL"
            returncode = item.get("returncode")
            verification_lines.append(f"- `{command}` -> {status} (exit={returncode})")

        if not verification_lines:
            verification_lines.append("- No verification commands were attempted.")

        gate_lines = gate_events or ["| None |"]
        changed_lines = [f"- `{path}`" for path in changed_files] or ["- No changed files detected."]
        degradation = verification.get("reason", "None recorded.") if result_value != "DONE" else "None."
        test_trace_lines: List[str] = []
        drift_trace_lines: List[str] = []
        if str(state.get("mode")) == "test-generation":
            test_style = str(mode_context.get("test_style", "No test style summary available."))
            test_trace_lines.append(f"- Style: {test_style}")
            for item in mode_context.get("requirements", [])[:3]:
                test_trace_lines.append(f"- Target behavior: {item}")
            for item in mode_context.get("test_files", [])[:3]:
                test_trace_lines.append(f"- Candidate test file: {item}")
            if len(test_trace_lines) == 1:
                test_trace_lines.append("- No candidate test files detected.")
        else:
            test_trace_lines.append("- Not a test-generation run.")
        if str(state.get("mode")) == "spec-code-drift":
            drift_trace_lines.append(f"- Traceability matrix: {mode_context.get('traceability_matrix', 'No traceability matrix recorded.')}")
            for item in mode_context.get("drift_findings", [])[:5]:
                drift_trace_lines.append(item)
            if len(drift_trace_lines) == 1:
                drift_trace_lines.append("- No drift findings were recorded.")
        else:
            drift_trace_lines.append("- Not a spec-code-drift run.")

        report = "\n".join(
            [
                "# LoopForge Final Report",
                "",
                "## Result",
                "",
                result_value,
                "",
                "## Mode",
                "",
                str(state.get("mode", DEFAULT_MODE)),
                "",
                "## Project Type",
                "",
                str(state.get("project_type", "unknown")),
                "",
                "## Summary",
                "",
                "LoopForge runner completed deterministic phases for the current milestone.",
                "",
                "## Changed Files",
                "",
                *changed_lines,
                "",
                "## Verification Commands",
                "",
                *verification_lines,
                "",
                "## Verification Results",
                "",
                json.dumps(verification, indent=2, ensure_ascii=True) if verification else "No verification summary available.",
                "",
                "## Repair Status",
                "",
                f"repair_round={state.get('repair_round', 0)} / {MAX_REPAIR_ROUNDS}",
                "",
                "## Integrate Review",
                "",
                json.dumps(review, indent=2, ensure_ascii=True) if review else "No integrate review summary available.",
                "",
                "## Test Generation Trace",
                "",
                *test_trace_lines,
                "",
                "## Drift Findings",
                "",
                *drift_trace_lines,
                "",
                "## Gate Events",
                "",
                *gate_lines,
                "",
                "## Degradation",
                "",
                degradation,
                "",
                "## Risks",
                "",
                "- Repair orchestration is not implemented in the runner yet.",
                "- Non-Java verification remains rule-defined but not executable in this milestone.",
                "",
                "## Traceability",
                "",
                "- Task mode comes from `.loopforge/state/loop-state.json`.",
                "- Verification evidence comes from `.loopforge/state/verification-summary.json`.",
                "- Gate history comes from `.loopforge/gates/gate-events.md`.",
                "",
            ]
        )

        report_path = self.final_report_path
        try:
            self.final_report_path.write_text(report, encoding="utf-8")
        except OSError:
            self.fallback_report_path.write_text(report, encoding="utf-8")
            report_path = self.fallback_report_path
        return {
            "ok": True,
            "report": str(report_path),
            "result": result_value,
        }


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LoopForge contest runner")
    parser.add_argument("--init", action="store_true", help="initialize .loopforge workspace")
    parser.add_argument("--self-check", action="store_true", help="run deterministic runtime checks")
    parser.add_argument("--detect", action="store_true", help="detect project type")
    parser.add_argument("--snapshot", metavar="NAME", help="record git diff into snapshots/NAME.diff")
    parser.add_argument("--prepare", metavar="TASK_FILE", help="generate task/spec/brainstorm/plan/lease artifacts")
    parser.add_argument("--start-apply", action="store_true", help="record pre-apply snapshot and create subagent report template")
    parser.add_argument("--complete-apply", action="store_true", help="update the subagent report with detected post-apply changes")
    parser.add_argument("--integrate-review", action="store_true", help="review changed files against the active lease")
    parser.add_argument("--verify", action="store_true", help="run project verification")
    parser.add_argument("--repair", action="store_true", help="advance the repair state machine and record repair evidence")
    parser.add_argument("--finalize", action="store_true", help="generate final report")
    return parser.parse_args(argv)


def print_json(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True))


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    if not any([args.init, args.self_check, args.detect, args.snapshot, args.prepare, args.start_apply, args.complete_apply, args.integrate_review, args.verify, args.repair, args.finalize]):
        print("No action provided. Use --init, --self-check, --detect, --snapshot NAME, --prepare TASK_FILE, --start-apply, --complete-apply, --integrate-review, --verify, --repair, or --finalize.", file=sys.stderr)
        return 2

    runner = LoopForgeRunner(Path.cwd())
    try:
        if args.init:
            print_json(runner.init_workspace())
        if args.self_check:
            runner.ensure_workspace()
            print_json(runner.self_check())
        if args.detect:
            runner.ensure_workspace()
            print_json(runner.detect_project())
        if args.snapshot:
            runner.ensure_workspace()
            print_json(runner.snapshot_diff(args.snapshot))
        if args.prepare:
            runner.ensure_workspace()
            print_json(runner.prepare_workflow(args.prepare))
        if args.start_apply:
            runner.ensure_workspace()
            print_json(runner.start_apply())
        if args.complete_apply:
            runner.ensure_workspace()
            print_json(runner.complete_apply())
        if args.integrate_review:
            runner.ensure_workspace()
            print_json(runner.run_integrate_review())
        if args.verify:
            runner.ensure_workspace()
            print_json(runner.verify_project())
        if args.repair:
            runner.ensure_workspace()
            print_json(runner.run_repair())
        if args.finalize:
            runner.ensure_workspace()
            print_json(runner.generate_final_report())
    except Exception as exc:  # pragma: no cover - defensive contest safety
        print_json({"ok": False, "error": str(exc)})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

## Extraction Rule

Copy only the Python code block into `.loopforge/runtime/loopforge_runner.py`.
