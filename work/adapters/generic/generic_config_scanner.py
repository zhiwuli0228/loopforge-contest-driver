from __future__ import annotations

from pathlib import Path
from typing import List

from adapters.shared import build_object, read_text
from core.implementation_model import ImplementationObject


CONFIG_SUFFIXES = {".yaml", ".yml", ".json", ".properties", ".toml", ".ini", ".env"}


def scan_generic_configs(source_root: Path) -> List[ImplementationObject]:
    objects: List[ImplementationObject] = []
    for path in sorted(source_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in CONFIG_SUFFIXES:
            continue
        text = read_text(path)
        preview = next((line.strip() for line in text.splitlines() if line.strip()), path.name)
        objects.append(
            build_object(
                source_root,
                "generic",
                "implementation",
                "config_surface",
                path.stem,
                f"Generic adapter captured configuration file {path.name}.",
                path,
                "L1",
                preview,
                confidence="medium",
                normalization_status="partial",
                tags=["config"],
                attributes={"format": path.suffix.lstrip(".")},
                extensions={"generic": {"inventory_kind": "config"}},
            )
        )
    return objects
