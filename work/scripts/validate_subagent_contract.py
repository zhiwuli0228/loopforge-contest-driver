#!/usr/bin/env python3
"""Validate the LoopForge delegated subagent execution contract."""

from __future__ import annotations

from pathlib import Path
import sys


REQUIRED_LITERALS = (
    "subagent_required: true",
    "fallback_to_main_context_allowed: false",
    'missing_subagent_policy: "BLOCKED_WITH_REPORT"',
    "parent_direct_execution_allowed: false",
    "file_handoff_required: true",
)

BANNED_PHRASES = (
    "if subagents are available",
    "subagent preferred",
    "emulate staged workers",
    "fallback to main context",
    "continue in main context",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_scalar(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'"}:
        return cleaned[1:-1]
    return cleaned


def parse_stage_contracts(path: Path) -> list[dict[str, str]]:
    stages: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw in read_text(path).splitlines():
        stripped = raw.strip()
        if stripped.startswith("- id:"):
            if current is not None:
                stages.append(current)
            current = {"id": strip_scalar(stripped.split(":", 1)[1])}
            continue
        if current is None:
            continue
        for key in (
            "subagent",
            "output",
            "success_gate",
            "failure_gate",
            "blocked_gate",
            "parent_direct_execution_allowed",
        ):
            prefix = f"{key}:"
            if stripped.startswith(prefix):
                current[key] = strip_scalar(stripped.split(":", 1)[1])
                break
    if current is not None:
        stages.append(current)
    return stages


def require_literal(errors: list[str], label: str, text: str, literal: str) -> None:
    if literal not in text:
        errors.append(f"{label}: missing {literal}")


def main() -> int:
    work_root = Path(__file__).resolve().parents[1]
    workspace_root = work_root.parent
    errors: list[str] = []

    instruction_path = workspace_root / "INSTRUCTION.md"
    readme_path = workspace_root / "README.md"
    skill_path = work_root / "skills" / "loopforge-driver" / "SKILL.md"
    subagent_root = work_root / "subagent"
    superspec_path = work_root / "profiles" / "superspec" / "consistency-check-stages.yaml"
    superpower_path = work_root / "profiles" / "superpower" / "consistency-check-guards.yaml"
    profile_path = work_root / "profiles" / "examples" / "java-consistency-check.yaml"
    delegated_rule_path = work_root / "rules" / "loopforge" / "modes" / "consistency-check" / "delegated-execution.md"
    artifact_rule_path = work_root / "rules" / "loopforge" / "modes" / "consistency-check" / "02-required-artifacts.md"
    final_report_rule_path = work_root / "rules" / "loopforge" / "core" / "05-final-report.md"
    runtime_path = work_root / "runtime" / "loopforge_runner.py"

    for path in (
        instruction_path,
        readme_path,
        skill_path,
        superspec_path,
        superpower_path,
        profile_path,
        delegated_rule_path,
        artifact_rule_path,
        final_report_rule_path,
        runtime_path,
    ):
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(workspace_root)}")

    if not subagent_root.exists():
        errors.append("missing required directory: subagent")

    if errors:
        for item in errors:
            print(f"[FAIL] {item}", file=sys.stderr)
        return 1

    instruction_text = read_text(instruction_path)
    skill_text = read_text(skill_path)
    superpower_text = read_text(superpower_path)
    profile_text = read_text(profile_path)
    superspec_text = read_text(superspec_path)
    delegated_rule_text = read_text(delegated_rule_path)
    artifact_rule_text = read_text(artifact_rule_path)
    final_report_rule_text = read_text(final_report_rule_path)
    runtime_text = read_text(runtime_path)

    for phrase in BANNED_PHRASES:
        if phrase in instruction_text.lower():
            errors.append(f"INSTRUCTION.md contains banned phrase: {phrase}")
        if phrase in skill_text.lower():
            errors.append(f"skills/loopforge-driver/SKILL.md contains banned phrase: {phrase}")

    for literal in REQUIRED_LITERALS:
        require_literal(errors, "profiles/superpower/consistency-check-guards.yaml", superpower_text, literal)
        require_literal(errors, "profiles/examples/java-consistency-check.yaml", profile_text, literal)
        require_literal(errors, "profiles/superspec/consistency-check-stages.yaml", superspec_text, literal)

    if "required subagent unavailable" not in instruction_text:
        errors.append("INSTRUCTION.md missing required subagent unavailable block")
    if "required subagent unavailable" not in skill_text:
        errors.append("skills/loopforge-driver/SKILL.md missing required subagent unavailable block")
    if "required subagent unavailable" not in delegated_rule_text:
        errors.append("delegated-execution.md missing required subagent unavailable block")

    for literal in ("executed_by_subagent", "parent_direct_execution: false"):
        require_literal(errors, "rules/loopforge/modes/consistency-check/02-required-artifacts.md", artifact_rule_text, literal)
        require_literal(errors, "rules/loopforge/modes/consistency-check/delegated-execution.md", delegated_rule_text, literal)

    require_literal(errors, "rules/loopforge/core/05-final-report.md", final_report_rule_text, "## Subagent Execution Evidence")
    require_literal(errors, "runtime/loopforge_runner.py", runtime_text, "## Subagent Execution Evidence")

    stages = parse_stage_contracts(superspec_path)
    if not stages:
        errors.append("profiles/superspec/consistency-check-stages.yaml has no stages")
    for stage in stages:
        stage_id = stage.get("id", "<unknown>")
        if not stage.get("subagent"):
            errors.append(f"stage {stage_id} missing subagent")
        elif not (subagent_root / f"{stage['subagent']}.md").exists():
            errors.append(f"stage {stage_id} missing subagent definition: subagent/{stage['subagent']}.md")
        if not stage.get("output"):
            errors.append(f"stage {stage_id} missing output")
        if stage.get("parent_direct_execution_allowed") != "false":
            errors.append(f"stage {stage_id} must set parent_direct_execution_allowed: false")
        if not (stage.get("failure_gate") == "BLOCKED_WITH_REPORT" or stage.get("blocked_gate") == "BLOCKED_WITH_REPORT"):
            errors.append(f"stage {stage_id} missing BLOCKED_WITH_REPORT failure gate")

    if errors:
        for item in errors:
            print(f"[FAIL] {item}", file=sys.stderr)
        return 1

    print("Subagent contract validation passed")
    print(f"Stages checked: {len(stages)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
