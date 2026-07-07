from __future__ import annotations

from pathlib import Path
from typing import List

from adapters.shared import build_object, read_text
from core.implementation_model import ImplementationObject


def scan_generic_tests(source_root: Path) -> List[ImplementationObject]:
    objects: List[ImplementationObject] = []
    for path in sorted(source_root.rglob("*")):
        if not path.is_file():
            continue
        lower = path.as_posix().lower()
        if "/test" not in lower and "/tests" not in lower and "test_" not in path.name.lower():
            continue
        preview = next((line.strip() for line in read_text(path).splitlines() if line.strip()), path.name)
        objects.append(
            build_object(
                source_root,
                "generic",
                "implementation",
                "test_artifact",
                path.stem,
                f"Generic adapter captured test-like artifact {path.name}.",
                path,
                "L1",
                preview,
                confidence="medium",
                normalization_status="partial",
                tags=["test_coverage"],
                extensions={"generic": {"inventory_kind": "test"}},
            )
        )
    return objects
