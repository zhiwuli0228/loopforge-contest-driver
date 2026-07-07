from __future__ import annotations

from pathlib import Path
from typing import List

from adapters.shared import build_object
from core.implementation_model import ImplementationObject


def scan_generic_files(source_root: Path, limit: int = 25) -> List[ImplementationObject]:
    objects: List[ImplementationObject] = []
    candidate_files = [path for path in source_root.rglob("*") if path.is_file()]
    for path in sorted(candidate_files)[:limit]:
        objects.append(
            build_object(
                source_root,
                "generic",
                "implementation",
                "module",
                path.stem,
                f"Generic inventory captured repository file {path.name}.",
                path,
                "L1",
                path.name,
                confidence="medium",
                normalization_status="partial",
                tags=["inventory"],
                attributes={"relative_path": path.relative_to(source_root).as_posix(), "extension": path.suffix.lstrip(".")},
                extensions={"generic": {"inventory_kind": "file"}},
            )
        )
    return objects
