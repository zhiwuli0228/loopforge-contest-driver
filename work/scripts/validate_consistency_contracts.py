#!/usr/bin/env python3
"""Validate the authoritative design-implementation consistency contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml


EXPECTED_STAGE_IDS = [f"dic-0{i}" for i in range(10)]
ROOT = Path(__file__).resolve().parents[2]
REQUIRED_STAGE_PACKAGE_SECTIONS = (
    "## Objective",
    "## Orchestrator Boundary",
    "## Required Outputs",
    "## Gate Rules",
    "## Handoff Rules",
)


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path} missing YAML frontmatter")
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        raise ValueError(f"{path} has malformed YAML frontmatter")
    _, frontmatter, body = parts
    return yaml.safe_load(frontmatter), body


def main() -> int:
    errors: list[str] = []

    config_path = ROOT / "work" / "loopforge.config.yaml"
    skill_path = ROOT / "work" / "skills" / "design-implementation-consistency" / "SKILL.md"
    profile_path = ROOT / "work" / "profiles" / "examples" / "default-java-consistency.yaml"
    stages_path = ROOT / "work" / "profiles" / "superspec" / "design-implementation-consistency-stages.yaml"
    guards_path = ROOT / "work" / "profiles" / "superpower" / "design-implementation-consistency-guards.yaml"
    stage_map_path = ROOT / "work" / "subagent" / "design-implementation-consistency-stage-map.yaml"
    fail_soft_fixture_path = ROOT / "work" / "subagent" / "tests" / "fixtures" / "design-implementation-consistency-fail-soft-finalize.json"
    runner_path = ROOT / "work" / "runtime" / "loopforge_runner.py"
    openspec_config_path = ROOT / "openspec" / "config.yaml"

    for path in (
        config_path,
        skill_path,
        profile_path,
        stages_path,
        guards_path,
        stage_map_path,
        fail_soft_fixture_path,
        runner_path,
        openspec_config_path,
    ):
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(ROOT)}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    config = load_yaml(config_path)
    profile = load_yaml(profile_path)
    superspec = load_yaml(stages_path)
    guards = load_yaml(guards_path)
    stage_map = load_yaml(stage_map_path)
    fail_soft_fixture = load_json(fail_soft_fixture_path)
    runner_text = runner_path.read_text(encoding="utf-8")
    skill_text = skill_path.read_text(encoding="utf-8")
    openspec_config = load_yaml(openspec_config_path)

    if openspec_config.get("defaultSchema") != "spec-driven":
        errors.append("openspec/config.yaml must default to spec-driven")

    if config["execution"].get("strategy") != "repair-and-verify":
        errors.append("work/loopforge.config.yaml must set execution.strategy=repair-and-verify")
    if config["execution"].get("allow_patch") is not True:
        errors.append("work/loopforge.config.yaml must set allow_patch=true")
    if config["execution"].get("allow_code_generation") is not True:
        errors.append("work/loopforge.config.yaml must set allow_code_generation=true")

    if profile["execution"].get("strategy") != "repair-and-verify":
        errors.append("default-java-consistency.yaml must enforce repair-and-verify strategy")
    if profile["execution"].get("allow_patch") is not True:
        errors.append("default-java-consistency.yaml must set allow_patch=true")
    if profile["execution"].get("allow_code_generation") is not True:
        errors.append("default-java-consistency.yaml must set allow_code_generation=true")
    if profile["task"]["language"]["default_adapter"] != "java":
        errors.append("default-java-consistency.yaml must default to java adapter")
    if profile["task"]["language"]["fallback_adapter"] != "generic":
        errors.append("default-java-consistency.yaml must fall back to generic adapter")
    if profile["reporting"]["model_paths"].get("acceptance_baseline") != "logs/trace/consistency/01-acceptance-baseline.json":
        errors.append("default-java-consistency.yaml must expose acceptance baseline path")
    if profile["reporting"]["model_paths"].get("retry_repair") != "logs/trace/consistency/08-retry-repair.json":
        errors.append("default-java-consistency.yaml must expose retry repair path")

    if "repair-and-verify" not in skill_text:
        errors.append("SKILL.md must declare repair-and-verify execution")
    for literal in ("SUBMISSION_PASSED", "SUBMISSION_PARTIAL", "SUBMISSION_BLOCKED", "SUBMISSION_INVALID"):
        if literal not in skill_text:
            errors.append(f"SKILL.md missing final status literal: {literal}")

    stages = superspec.get("stages", [])
    stage_ids = [stage["id"] for stage in stages]
    if stage_ids != EXPECTED_STAGE_IDS:
        errors.append(f"unexpected stage ids/order: {stage_ids}")
    if superspec.get("execution_defaults", {}).get("strategy") != "repair-and-verify":
        errors.append("superspec must declare repair-and-verify strategy")

    stage_map_rows = stage_map.get("stage_packages", [])
    stage_map_ids = [row["stage_id"] for row in stage_map_rows]
    if stage_map_ids != EXPECTED_STAGE_IDS:
        errors.append(f"stage package map mismatch: {stage_map_ids}")
    stage_map_by_id = {row["stage_id"]: row for row in stage_map_rows}

    guard_rows = guards.get("stage_guards", [])
    guard_ids = [row["stage_id"] for row in guard_rows]
    if guard_ids != EXPECTED_STAGE_IDS:
        errors.append(f"guard stage coverage mismatch: {guard_ids}")
    if guards.get("execution", {}).get("strategy") != "repair-and-verify":
        errors.append("guards must declare repair-and-verify strategy")
    if "SUBMISSION_ROOT/code/**" not in guards["source_write_policy"]["mutable_targets"]:
        errors.append("guards must allow SUBMISSION_ROOT/code/** as a mutable target")
    if "SUBMISSION_ROOT/maven-settings.xml" not in guards["source_write_policy"]["mutable_targets"]:
        errors.append("guards must allow SUBMISSION_ROOT/maven-settings.xml as a mutable support asset")

    for stage in stages:
        stage_id = stage["id"]
        map_entry = stage_map_by_id.get(stage_id)
        if not map_entry:
            errors.append(f"missing stage map entry for {stage_id}")
            continue
        if map_entry["summary_output"] not in stage["outputs"]:
            errors.append(f"{stage_id} summary output missing from superspec outputs")
        if map_entry["gate_output"] not in stage["outputs"]:
            errors.append(f"{stage_id} gate output missing from superspec outputs")
        if map_entry["evidence_index"] not in stage["outputs"]:
            errors.append(f"{stage_id} evidence output missing from superspec outputs")

        package_path = ROOT / map_entry["file"]
        metadata, body = load_frontmatter(package_path)
        if metadata.get("stage_id") != stage_id:
            errors.append(f"{stage_id} package metadata stage_id mismatch")
        if metadata.get("stage_name") != stage["name"]:
            errors.append(f"{stage_id} package stage_name mismatch")
        if metadata.get("inputs") != stage["inputs"]:
            errors.append(f"{stage_id} package inputs mismatch")
        if metadata.get("outputs") != stage["outputs"]:
            errors.append(f"{stage_id} package outputs mismatch")
        if metadata.get("success_gate") != stage["gate"]["success"]:
            errors.append(f"{stage_id} package success_gate mismatch")
        if metadata.get("failure_gate") != stage["gate"]["failure"]:
            errors.append(f"{stage_id} package failure_gate mismatch")
        for section in REQUIRED_STAGE_PACKAGE_SECTIONS:
            if section not in body:
                errors.append(f"{stage_id} package missing section: {section}")

        writes_allowed = metadata.get("source_writes_allowed")
        if stage_id in {"dic-05", "dic-08"}:
            if writes_allowed is not True:
                errors.append(f"{stage_id} must allow source writes")
        elif writes_allowed is not False:
            errors.append(f"{stage_id} must forbid source writes")

    if fail_soft_fixture.get("failed_stage") != "dic-06":
        errors.append("fail-soft fixture must model dic-06 as the failed stage")
    if fail_soft_fixture.get("expected_finalize_stage") != "dic-09":
        errors.append("fail-soft fixture must finalize through dic-09")
    if fail_soft_fixture.get("source_write_forbidden_glob") != "SUBMISSION_ROOT/README.md":
        errors.append("fail-soft fixture must preserve an immutable baseline write prohibition example")

    if "LEGACY_FORBIDDEN_LITERALS" not in runner_text:
        errors.append("runtime/loopforge_runner.py must preserve a legacy denylist for self-check diagnostics")
    for literal in ("SUBMISSION_PASSED", "SUBMISSION_PARTIAL", "SUBMISSION_BLOCKED", "SUBMISSION_INVALID"):
        if literal not in runner_text:
            errors.append(f"runtime/loopforge_runner.py missing final status literal: {literal}")

    if errors:
        print("\n".join(f"FAIL: {item}" for item in errors), file=sys.stderr)
        return 1

    print("consistency contracts: PASS")
    print(f"stages checked: {len(stages)}")
    print("repair-and-verify defaults: PASS")
    print("stage packages and guards: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
