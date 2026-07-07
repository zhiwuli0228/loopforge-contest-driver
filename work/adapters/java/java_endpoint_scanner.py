from __future__ import annotations

import re
from pathlib import Path
from typing import List

from adapters.shared import build_object, find_line_number, read_text
from core.implementation_model import ImplementationObject


REQUEST_ANNOTATION_RE = re.compile(r"@(?P<verb>Get|Post|Put|Delete|Patch|Request)Mapping\s*\((?P<args>[^)]*)\)")
CLASS_RE = re.compile(r"\bclass\s+(?P<name>\w+)")
METHOD_RE = re.compile(
    r"\b(public|protected|private)\s+(?:static\s+)?[\w<>\[\], ?]+\s+(?P<name>\w+)\s*\("
)


def _extract_path(arguments: str) -> str:
    match = re.search(r'(?:"|\')(?P<path>/[^"\']*)(?:"|\')', arguments)
    if match:
        return match.group("path")
    named = re.search(r"(?:path|value)\s*=\s*(?P<quote>['\"])(?P<path>/[^'\"]*)(?P=quote)", arguments)
    if named:
        return named.group("path")
    return "/"


def scan_java_endpoints(source_root: Path) -> List[ImplementationObject]:
    objects: List[ImplementationObject] = []

    for java_file in source_root.rglob("*.java"):
        text = read_text(java_file)
        if "@RequestMapping" not in text and "Mapping(" not in text and not java_file.name.endswith(("Controller.java", "Resource.java")):
            continue

        class_match = CLASS_RE.search(text)
        class_name = class_match.group("name") if class_match else java_file.stem
        class_path = ""
        class_request = re.search(r"@RequestMapping\s*\((?P<args>[^)]*)\)\s*public\s+class", text)
        if class_request:
            class_path = _extract_path(class_request.group("args"))

        pending_annotations: List[tuple[str, str]] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            annotation_match = REQUEST_ANNOTATION_RE.search(line)
            if annotation_match:
                pending_annotations.append((annotation_match.group("verb").lower(), _extract_path(annotation_match.group("args"))))
                continue

            method_match = METHOD_RE.search(line)
            if not method_match:
                continue
            if not pending_annotations and not java_file.name.endswith(("Controller.java", "Resource.java")):
                continue

            method_name = method_match.group("name")
            http_method, route = pending_annotations[-1] if pending_annotations else ("request", "/")
            route = f"{class_path.rstrip('/')}{route}" if class_path and route != "/" else route if route != "/" else class_path or "/"
            excerpt = line.strip()
            objects.append(
                build_object(
                    source_root,
                    "java",
                    "implementation",
                    "entrypoint",
                    method_name,
                    f"Java HTTP entrypoint {method_name} handles {http_method.upper()} {route}.",
                    java_file,
                    f"L{line_number}",
                    excerpt,
                    tags=["api_contract"],
                    attributes={"http_method": http_method.upper(), "path": route, "class_name": class_name},
                    extensions={"java": {"class_name": class_name, "annotations": [item[0] for item in pending_annotations]}},
                )
            )
            pending_annotations = []

    return objects
