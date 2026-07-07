from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from adapters.registry import build_default_registry


WORK_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = WORK_ROOT / "profiles" / "examples" / "default-java-consistency.yaml"


def load_profile(path: str | Path | None = None) -> Dict[str, Any]:
    profile_path = Path(path) if path else DEFAULT_PROFILE
    with profile_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def build_source_inventory(source_root: str | Path, profile_path: str | Path | None = None) -> Dict[str, Any]:
    root = Path(source_root)
    profile = load_profile(profile_path)
    registry = build_default_registry()
    selection = registry.select(root, profile)
    files = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
    inventory = {
        "source_root": str(root),
        "selected_adapter": selection.adapter_id,
        "selection": selection.to_dict(),
        "file_count": len(files),
        "files": files,
    }
    return inventory


def extract_implementation_model(
    source_root: str | Path,
    profile_path: str | Path | None = None,
    adapter_override: str | None = None,
) -> Dict[str, Any]:
    root = Path(source_root)
    profile = load_profile(profile_path)
    registry = build_default_registry()
    result = registry.extract(root, profile, adapter_override)
    return result.to_dict()
