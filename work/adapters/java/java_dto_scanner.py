from __future__ import annotations

import re
from pathlib import Path
from typing import List

from adapters.shared import build_object, find_line_number, read_text
from core.implementation_model import ImplementationObject


FIELD_RE = re.compile(r"\bprivate\s+(?P<type>[\w<>]+)\s+(?P<name>\w+)\s*;")
CLASS_RE = re.compile(r"\b(class|record)\s+(?P<name>\w+)")
DTO_SUFFIXES = ("DTO.java", "Request.java", "Response.java", "Entity.java", "VO.java")


def scan_java_data_shapes(source_root: Path) -> List[ImplementationObject]:
    objects: List[ImplementationObject] = []
    for java_file in source_root.rglob("*.java"):
        text = read_text(java_file)
        class_match = CLASS_RE.search(text)
        if not class_match:
            continue
        if not java_file.name.endswith(DTO_SUFFIXES) and not FIELD_RE.search(text):
            continue

        class_name = class_match.group("name")
        fields = [{"name": match.group("name"), "type": match.group("type")} for match in FIELD_RE.finditer(text)]
        objects.append(
            build_object(
                source_root,
                "java",
                "implementation",
                "data_shape",
                class_name,
                f"Java data shape {class_name} exposes {len(fields)} declared fields.",
                java_file,
                f"L{find_line_number(text, class_name)}",
                class_name,
                tags=["data_model"],
                attributes={"field_count": len(fields), "fields": fields},
                extensions={"java": {"file_name": java_file.name}},
            )
        )
    return objects
