from __future__ import annotations

from pathlib import Path
from typing import List

from adapters.shared import build_object, read_text
from core.implementation_model import ImplementationObject


def scan_generic_text_evidence(source_root: Path, limit: int = 20) -> List[ImplementationObject]:
    objects: List[ImplementationObject] = []
    count = 0
    for path in sorted(source_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".rst"}:
            continue
        text = read_text(path)
        preview = next((line.strip() for line in text.splitlines() if line.strip()), path.name)
        objects.append(
            build_object(
                source_root,
                "generic",
                "implementation",
                "symbol",
                path.stem,
                f"Generic adapter retained supporting text evidence from {path.name}.",
                path,
                "L1",
                preview,
                confidence="low",
                normalization_status="partial",
                tags=["inventory"],
                extensions={"generic": {"inventory_kind": "text_evidence"}},
            )
        )
        count += 1
        if count >= limit:
            break
    return objects
