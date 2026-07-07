from __future__ import annotations

import re
from pathlib import Path
from typing import List

from adapters.shared import build_object, read_text
from core.implementation_model import ImplementationObject


PATTERNS = [
    re.compile(r"\bclass\s+(?P<name>[A-Z]\w*)"),
    re.compile(r"\b(?:def|function)\s+(?P<name>[A-Za-z_]\w*)\s*\("),
    re.compile(r"\b(?:public|private|protected|static|int|void|char|float|double|bool|boolean|string)\s+(?P<name>[A-Za-z_]\w*)\s*\("),
]


def scan_generic_symbols(source_root: Path, limit: int = 40) -> List[ImplementationObject]:
    objects: List[ImplementationObject] = []
    count = 0
    for path in sorted(source_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".jar", ".class"}:
            continue
        text = read_text(path)
        for pattern in PATTERNS:
            for match in pattern.finditer(text):
                name = match.group("name")
                objects.append(
                    build_object(
                        source_root,
                        "generic",
                        "implementation",
                        "symbol",
                        name,
                        f"Generic adapter indexed symbol-like construct {name}.",
                        path,
                        "L1",
                        name,
                        confidence="low",
                        normalization_status="partial",
                        tags=["inventory"],
                        attributes={"pattern": pattern.pattern},
                        extensions={"generic": {"language_specific_classification": "approximate_symbol"}},
                    )
                )
                count += 1
                if count >= limit:
                    return objects
    return objects
