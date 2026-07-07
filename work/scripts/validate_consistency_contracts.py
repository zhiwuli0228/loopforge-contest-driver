#!/usr/bin/env python3
"""Validate the authoritative design-implementation consistency contracts."""

from __future__ import annotations

import fnmatch
import json
import sys
from pathlib import Path

import yaml


EXPECTED_STAGE_IDS = [f"dic-0{i}" for i in range(10)]
ROOT = Path(__file__).resolve().parents[2]
SHARED_STAGE_ARTIFACTS = {"logs/trace/consistency/guard-denials.jsonl"}
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
    archive_manifest_path = ROOT / "work" / "archived" / "c-to-rust" / "manifest.json"
    repo_driver_skill_path = ROOT / "work" / "skills" / "loopforge-driver" / "SKILL.md"
    run_script_path = ROOT / "work" / "scripts" / "run.sh"
    runner_path = ROOT / "work" / "runtime" / "loopforge_runner.py"
    openspec_config_path = ROOT / "openspec" / "config.yaml"
    legacy_paths = [
        ROOT / "work" / "profiles" / "examples" / "consistency-check.yaml",
        ROOT / "work" / "profiles" / "examples" / "java-consistency-check.yaml",
        ROOT / "work" / "profiles" / "templates" / "consistency-check.yaml",
    ]

    for path in [
        config_path,
        skill_path,
        profile_path,
        stages_path,
        guards_path,
        stage_map_path,
        fail_soft_fixture_path,
        archive_manifest_path,
        repo_driver_skill_path,
        run_script_path,
        runner_path,
        openspec_config_path,
        *legacy_paths,
    ]:
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
    archive_manifest = load_json(archive_manifest_path)
    legacy_profiles = [load_yaml(path) for path in legacy_paths]
    skill_text = skill_path.read_text(encoding="utf-8")
    repo_driver_skill_text = repo_driver_skill_path.read_text(encoding="utf-8")
    run_script_text = run_script_path.read_text(encoding="utf-8")
    runner_text = runner_path.read_text(encoding="utf-8")
    openspec_config = load_yaml(openspec_config_path)

    if config["task"]["profile"] != "profiles/examples/default-java-consistency.yaml":
        errors.append("work/loopforge.config.yaml must point task.profile to profiles/examples/default-java-consistency.yaml")
    if config["task"]["mode"] != "consistency-check":
        errors.append("work/loopforge.config.yaml must keep consistency-check mode")
    if config["execution"].get("allow_code_generation") is not False:
        errors.append("work/loopforge.config.yaml must keep allow_code_generation=false")
    if config["execution"].get("allow_patch") is not False:
        errors.append("work/loopforge.config.yaml must set allow_patch=false")
    if openspec_config.get("defaultSchema") != "spec-driven":
        errors.append("openspec/config.yaml must default to spec-driven")

    if profile["profile"].get("authoritative") is not True:
        errors.append("default-java-consistency.yaml must be authoritative")
    if profile["task"]["language"]["default_adapter"] != "java":
        errors.append("default-java-consistency.yaml must default to java adapter")
    if profile["task"]["language"]["fallback_adapter"] != "generic":
        errors.append("default-java-consistency.yaml must fall back to generic adapter")
    if profile["execution"].get("strategy") != "analyze-only":
        errors.append("default-java-consistency.yaml must enforce analyze-only strategy")
    if profile["contracts"].get("stage_packages") != "work/subagent/design-implementation-consistency-stage-map.yaml":
        errors.append("default-java-consistency.yaml must declare contracts.stage_packages")
    selection_cfg = profile.get("language", {}).get("detection", {}).get("selection", {})
    if selection_cfg.get("require_evidence") is not True:
        errors.append("default-java-consistency.yaml must require adapter-selection evidence")
    if selection_cfg.get("selection_output") != "logs/trace/consistency/02-adapter-selection.json":
        errors.append("default-java-consistency.yaml must declare the adapter selection output path")
    model_paths = profile.get("reporting", {}).get("model_paths", {})
    if model_paths.get("adapter_selection") != "logs/trace/consistency/02-adapter-selection.json":
        errors.append("default-java-consistency.yaml must expose reporting.model_paths.adapter_selection")
    if model_paths.get("design_inventory") != "logs/trace/consistency/01-design-inventory.json":
        errors.append("default-java-consistency.yaml must expose reporting.model_paths.design_inventory")
    if model_paths.get("drift_findings") != "logs/trace/consistency/06-drift-findings.json":
        errors.append("default-java-consistency.yaml must expose reporting.model_paths.drift_findings")
    if model_paths.get("risk_classification") != "logs/trace/consistency/07-risk-classification.json":
        errors.append("default-java-consistency.yaml must expose reporting.model_paths.risk_classification")
    if model_paths.get("repair_plan") != "logs/trace/consistency/08-repair-plan.json":
        errors.append("default-java-consistency.yaml must expose reporting.model_paths.repair_plan")
    if model_paths.get("verification_results") != "logs/trace/consistency/09-verification-results.json":
        errors.append("default-java-consistency.yaml must expose reporting.model_paths.verification_results")
    if model_paths.get("final_report_input") != "logs/trace/consistency/09-final-report-input.json":
        errors.append("default-java-consistency.yaml must expose reporting.model_paths.final_report_input")

    stage_rows = superspec.get("stages", [])
    stage_ids = [row["id"] for row in stage_rows]
    if stage_ids != EXPECTED_STAGE_IDS:
        errors.append(f"unexpected stage ids/order: {stage_ids}")
    if superspec.get("execution_defaults", {}).get("handoff_mode") != "file-paths-and-summaries-only":
        errors.append("superspec must declare handoff_mode=file-paths-and-summaries-only")

    stage_outputs = {row["id"]: row.get("outputs", []) for row in stage_rows}
    known_outputs = set()
    for row in stage_rows:
        for output in row.get("outputs", []):
            known_outputs.add(output)
            if row["id"] != "dic-09" and not output.startswith("logs/trace/consistency/"):
                errors.append(f"{row['id']} output must stay under logs/trace/consistency/: {output}")

    dic02_outputs = set(stage_outputs.get("dic-02", []))
    required_dic02_outputs = {
        "logs/trace/consistency/02-source-inventory.json",
        "logs/trace/consistency/02-adapter-selection.json",
        "logs/trace/consistency/02-source-inventory-gate.json",
    }
    missing_dic02 = required_dic02_outputs - dic02_outputs
    if missing_dic02:
        errors.append(f"dic-02 is missing required machine-readable outputs: {sorted(missing_dic02)}")

    dic01_outputs = set(stage_outputs.get("dic-01", []))
    if "logs/trace/consistency/01-design-inventory.json" not in dic01_outputs:
        errors.append("dic-01 must emit logs/trace/consistency/01-design-inventory.json")

    dic09_outputs = set(stage_outputs.get("dic-09", []))
    for artifact in (
        "logs/trace/consistency/09-verification-results.json",
        "logs/trace/consistency/09-final-report-input.json",
    ):
        if artifact not in dic09_outputs:
            errors.append(f"dic-09 must emit {artifact}")

    stage_map_rows = stage_map.get("stage_packages", [])
    stage_map_ids = [row["stage_id"] for row in stage_map_rows]
    if stage_map_ids != EXPECTED_STAGE_IDS:
        errors.append(f"stage package map mismatch: {stage_map_ids}")
    stage_map_by_id = {row["stage_id"]: row for row in stage_map_rows}

    for index, row in enumerate(stage_rows):
        declared_predecessors = set(row.get("consumes_from", []))
        if index == 0 and declared_predecessors:
            errors.append("dic-00 must not declare predecessors")
        if index > 0 and not declared_predecessors:
            errors.append(f"{row['id']} must declare predecessors")
        stage_package = row.get("stage_package")
        if not stage_package:
            errors.append(f"{row['id']} must declare stage_package")
        elif stage_package != stage_map_by_id.get(row["id"], {}).get("file"):
            errors.append(f"{row['id']} stage_package does not match stage map")
        handoff = row.get("handoff", {})
        for key in ("summary", "gate", "evidence_index", "structured"):
            if key not in handoff:
                errors.append(f"{row['id']} missing handoff.{key}")
        for handoff_path in [handoff.get("summary"), handoff.get("gate"), handoff.get("evidence_index")]:
            if handoff_path and handoff_path not in row.get("outputs", []):
                errors.append(f"{row['id']} handoff artifact missing from outputs: {handoff_path}")
        for structured_path in handoff.get("structured", []):
            if structured_path not in row.get("outputs", []):
                errors.append(f"{row['id']} structured handoff artifact missing from outputs: {structured_path}")
        for source in row.get("inputs", []):
            if (
                source.startswith("logs/trace/consistency/")
                and "*" not in source
                and source not in known_outputs
                and source not in SHARED_STAGE_ARTIFACTS
            ):
                errors.append(f"{row['id']} reads undeclared stage artifact: {source}")

    guard_rows = guards.get("stage_guards", [])
    guard_ids = [row["stage_id"] for row in guard_rows]
    if guard_ids != EXPECTED_STAGE_IDS:
        errors.append(f"guard stage coverage mismatch: {guard_ids}")
    if guards.get("execution", {}).get("handoff_mode") != "file-paths-and-summaries-only":
        errors.append("guards must declare handoff_mode=file-paths-and-summaries-only")
    if guards["source_write_policy"]["required_denial_evidence"] != guards["shared_paths"]["denial_evidence"]:
        errors.append("guard denial evidence path must be consistent")
    if "SOURCE_ROOT/**" not in guards["source_write_policy"]["forbidden_paths"]:
        errors.append("SOURCE_ROOT/** must be forbidden by guard policy")

    guard_by_stage = {row["stage_id"]: row for row in guard_rows}
    for stage_id, outputs in stage_outputs.items():
        allowlist = guard_by_stage.get(stage_id, {}).get("write_allowlist", [])
        for output in outputs:
            if output not in allowlist:
                errors.append(f"{stage_id} output missing from guard write allowlist: {output}")
        read_allowlist = guard_by_stage.get(stage_id, {}).get("read_allowlist", [])
        for input_path in next(row["inputs"] for row in stage_rows if row["id"] == stage_id):
            if input_path == "SOURCE_ROOT":
                input_path = "SOURCE_ROOT/**"
            if not any(fnmatch.fnmatch(input_path, pattern) for pattern in read_allowlist):
                errors.append(f"{stage_id} input missing from guard read allowlist: {input_path}")

    for stage_id in EXPECTED_STAGE_IDS:
        map_entry = stage_map_by_id.get(stage_id)
        if not map_entry:
            continue
        package_path = ROOT / map_entry["file"]
        try:
            metadata, body = load_frontmatter(package_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        stage_row = next(row for row in stage_rows if row["id"] == stage_id)
        if metadata.get("stage_id") != stage_id:
            errors.append(f"{stage_id} package metadata stage_id mismatch")
        if metadata.get("stage_package") != map_entry["file"]:
            errors.append(f"{stage_id} package metadata stage_package mismatch")
        if metadata.get("predecessors", []) != stage_row.get("consumes_from", []):
            errors.append(f"{stage_id} package predecessors mismatch")
        if metadata.get("inputs", []) != stage_row.get("inputs", []):
            errors.append(f"{stage_id} package inputs mismatch")
        if metadata.get("outputs", []) != stage_row.get("outputs", []):
            errors.append(f"{stage_id} package outputs mismatch")
        if metadata.get("success_gate") != stage_row["gate"]["success"]:
            errors.append(f"{stage_id} package success_gate mismatch")
        if metadata.get("failure_gate") != stage_row["gate"]["failure"]:
            errors.append(f"{stage_id} package failure_gate mismatch")
        if metadata.get("when_always_finalize") != stage_row["failure_behavior"]["when_always_finalize"]:
            errors.append(f"{stage_id} package when_always_finalize mismatch")
        if metadata.get("source_writes_allowed") is not False:
            errors.append(f"{stage_id} package must keep source_writes_allowed=false")
        if stage_id == "dic-08" and metadata.get("advisory_only") is not True:
            errors.append("dic-08 package must be advisory_only=true")
        if stage_id != "dic-08" and metadata.get("advisory_only") is not False:
            errors.append(f"{stage_id} package advisory_only must be false")
        for section in REQUIRED_STAGE_PACKAGE_SECTIONS:
            if section not in body:
                errors.append(f"{stage_id} package missing section: {section}")
        if "full `SOURCE_ROOT` context" in body and stage_id not in {"dic-00", "dic-02", "dic-04"}:
            errors.append(f"{stage_id} package should not mention full SOURCE_ROOT context access")

    for case in guards.get("negative_cases", []):
        stage_guard = guard_by_stage.get(case["stage_id"])
        if not stage_guard:
            errors.append(f"negative case references unknown stage: {case['stage_id']}")
            continue
        attempted_write = case["attempted_write"]
        allowlist = stage_guard.get("write_allowlist", [])
        allowed = any(fnmatch.fnmatch(attempted_write, pattern) for pattern in allowlist)
        source_forbidden = any(fnmatch.fnmatch(attempted_write, pattern) for pattern in guards["source_write_policy"]["forbidden_paths"])
        if case["expected_result"] != "denied":
            errors.append(f"negative case must expect denial: {case['id']}")
        if allowed and not source_forbidden:
            errors.append(f"negative case unexpectedly allowed by stage guard: {case['id']}")
        if case["denial_evidence"] != guards["shared_paths"]["denial_evidence"]:
            errors.append(f"negative case denial evidence mismatch: {case['id']}")

    required_skill_literals = [
        "analyze-only",
        "design evidence",
        "implementation evidence",
        "logs/trace/consistency/",
        "FINALIZED_WITH_FINDINGS",
        "design-implementation-consistency-stage-map.yaml",
        "only declared file paths, short summaries, and guard constraints",
    ]
    for literal in required_skill_literals:
        if literal not in skill_text:
            errors.append(f"SKILL.md missing required literal: {literal}")

    legacy_forbidden_literals = (
        "c-to-rust-migration-v2",
        "c-to-rust-migration-guards",
        "c-to-rust-migration-stages",
        "logs/trace/c-to-rust",
        "work/rules/loopforge/adapters/c-to-rust",
        "work/subagent/c2r-",
    )
    authoritative_texts = {
        "design-implementation-consistency/SKILL.md": skill_text,
        "loopforge-driver/SKILL.md": repo_driver_skill_text,
        "scripts/run.sh": run_script_text,
    }
    for label, text in authoritative_texts.items():
        for literal in legacy_forbidden_literals:
            if literal in text:
                errors.append(f"{label} must not reference archived legacy path: {literal}")

    if "LEGACY_FORBIDDEN_LITERALS" not in runner_text:
        errors.append("runtime/loopforge_runner.py must preserve a legacy denylist for self-check diagnostics")

    if archive_manifest.get("status") != "non-default":
        errors.append("archive manifest must declare status=non-default")
    if archive_manifest.get("authoritative_workflow") != "design-implementation consistency":
        errors.append("archive manifest must identify the authoritative workflow")
    if not archive_manifest.get("entries"):
        errors.append("archive manifest must list migrated legacy entries")

    if fail_soft_fixture.get("failed_stage") != "dic-06":
        errors.append("fail-soft fixture must model dic-06 as the failed stage")
    if fail_soft_fixture.get("expected_finalize_stage") != "dic-09":
        errors.append("fail-soft fixture must finalize through dic-09")
    if fail_soft_fixture.get("always_finalize") is not True:
        errors.append("fail-soft fixture must set always_finalize=true")
    if fail_soft_fixture.get("handoff_mode") != superspec.get("execution_defaults", {}).get("handoff_mode"):
        errors.append("fail-soft fixture handoff mode must match superspec")
    if fail_soft_fixture.get("source_write_forbidden_glob") not in guards["source_write_policy"]["forbidden_paths"]:
        errors.append("fail-soft fixture source write policy must match guard policy")
    failed_stage_outputs = set(stage_outputs.get(fail_soft_fixture["failed_stage"], []))
    for artifact in fail_soft_fixture.get("required_preserved_artifacts", []):
        if artifact not in failed_stage_outputs:
            errors.append(f"fail-soft fixture artifact not produced by failed stage: {artifact}")
    finalize_outputs = set(stage_outputs.get(fail_soft_fixture["expected_finalize_stage"], []))
    for artifact in fail_soft_fixture.get("required_terminal_outputs", []):
        if artifact not in finalize_outputs:
            errors.append(f"fail-soft fixture artifact not produced by finalization stage: {artifact}")

    for legacy in legacy_profiles:
        role = legacy.get("profile", {}).get("role")
        authoritative = legacy.get("profile", {}).get("authoritative")
        if role not in {"compatibility-example", "non-authoritative-template"}:
            errors.append(f"legacy profile missing non-authoritative role marker: {legacy.get('profile', {}).get('name')}")
        if authoritative is not False:
            errors.append(f"legacy profile must set authoritative=false: {legacy.get('profile', {}).get('name')}")

    if errors:
        print("\n".join(f"FAIL: {item}" for item in errors), file=sys.stderr)
        return 1

    print("consistency contracts: PASS")
    print(f"stages checked: {len(stage_rows)}")
    print("java default and generic fallback: PASS")
    print("adapter selection evidence: PASS")
    print("stage packages and fail-soft fixture: PASS")
    print("guard negative cases: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
