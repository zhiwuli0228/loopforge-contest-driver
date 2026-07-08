#!/usr/bin/env python3
"""Validate the authoritative DIC stage-package delegation contract."""

from __future__ import annotations

from pathlib import Path
import sys

import yaml


EXPECTED_STAGE_IDS = [f"dic-0{i}" for i in range(10)]


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


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
    root = Path(__file__).resolve().parents[2]
    errors: list[str] = []

    superspec_path = root / "work" / "profiles" / "superspec" / "design-implementation-consistency-stages.yaml"
    stage_map_path = root / "work" / "subagent" / "design-implementation-consistency-stage-map.yaml"
    if not superspec_path.exists():
        errors.append("missing required file: work/profiles/superspec/design-implementation-consistency-stages.yaml")
    if not stage_map_path.exists():
        errors.append("missing required file: work/subagent/design-implementation-consistency-stage-map.yaml")
    if errors:
        for item in errors:
            print(f"[FAIL] {item}", file=sys.stderr)
        return 1

    superspec = load_yaml(superspec_path)
    stage_map = load_yaml(stage_map_path)
    stages = superspec.get("stages", [])
    stage_ids = [stage.get("id") for stage in stages]
    if stage_ids != EXPECTED_STAGE_IDS:
        errors.append(f"unexpected stage ids/order: {stage_ids}")

    map_entries = stage_map.get("stage_packages", [])
    map_ids = [entry.get("stage_id") for entry in map_entries]
    if map_ids != EXPECTED_STAGE_IDS:
        errors.append(f"unexpected stage map ids/order: {map_ids}")
    map_by_id = {entry["stage_id"]: entry for entry in map_entries if "stage_id" in entry}

    for stage in stages:
        stage_id = stage["id"]
        map_entry = map_by_id.get(stage_id)
        if not map_entry:
            errors.append(f"missing stage map entry for {stage_id}")
            continue
        package_path = root / map_entry["file"]
        if not package_path.exists():
            errors.append(f"missing stage package: {map_entry['file']}")
            continue
        metadata, body = load_frontmatter(package_path)
        if metadata.get("stage_id") != stage_id:
            errors.append(f"{stage_id} metadata stage_id mismatch")
        if metadata.get("stage_name") != stage["name"]:
            errors.append(f"{stage_id} metadata stage_name mismatch")
        if metadata.get("inputs") != stage["inputs"]:
            errors.append(f"{stage_id} metadata inputs mismatch")
        if metadata.get("outputs") != stage["outputs"]:
            errors.append(f"{stage_id} metadata outputs mismatch")
        if metadata.get("success_gate") != stage["gate"]["success"]:
            errors.append(f"{stage_id} success_gate mismatch")
        if metadata.get("failure_gate") != stage["gate"]["failure"]:
            errors.append(f"{stage_id} failure_gate mismatch")
        if "## Objective" not in body or "## Handoff Rules" not in body:
            errors.append(f"{stage_id} package missing required body sections")

        writes_allowed = metadata.get("source_writes_allowed")
        if stage_id in {"dic-05", "dic-08"}:
            if writes_allowed is not True:
                errors.append(f"{stage_id} must allow source writes")
        elif writes_allowed is not False:
            errors.append(f"{stage_id} must not allow source writes")

    if errors:
        for item in errors:
            print(f"[FAIL] {item}", file=sys.stderr)
        return 1

    print("DIC subagent contract validation passed")
    print(f"Stages checked: {len(stages)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
