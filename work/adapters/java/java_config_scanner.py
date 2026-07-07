from __future__ import annotations

import re
from pathlib import Path
from typing import List

from adapters.shared import build_object, find_line_number, read_text
from core.implementation_model import ImplementationObject


BUILD_FILES = ("pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts")
CONFIG_PATTERNS = ("application*.yml", "application*.yaml", "application*.properties")


def _scan_build_dependencies(source_root: Path) -> List[ImplementationObject]:
    objects: List[ImplementationObject] = []
    for build_name in BUILD_FILES:
        path = source_root / build_name
        if not path.exists():
            continue
        text = read_text(path)
        dependencies = sorted(set(re.findall(r"<artifactId>([^<]+)</artifactId>", text)))
        if not dependencies:
            dependencies = sorted(set(re.findall(r"(?:implementation|api|testImplementation)\s+[\"']([^\"']+)[\"']", text)))
        for dependency in dependencies:
            objects.append(
                build_object(
                    source_root,
                    "java",
                    "implementation",
                    "dependency",
                    dependency,
                    f"Java build dependency declared in {path.name}.",
                    path,
                    f"L{find_line_number(text, dependency)}",
                    dependency,
                    tags=["inventory"],
                    attributes={"build_file": path.name},
                    extensions={"java": {"build_system_file": path.name}},
                )
            )
    return objects


def _scan_config_surfaces(source_root: Path) -> List[ImplementationObject]:
    objects: List[ImplementationObject] = []
    for pattern in CONFIG_PATTERNS:
        for config_path in source_root.rglob(pattern):
            text = read_text(config_path)
            preview = next((line.strip() for line in text.splitlines() if line.strip()), "")
            objects.append(
                build_object(
                    source_root,
                    "java",
                    "implementation",
                    "config_surface",
                    config_path.stem,
                    f"Java configuration surface loaded from {config_path.name}.",
                    config_path,
                    "L1",
                    preview,
                    tags=["config"],
                    attributes={"format": config_path.suffix.lstrip(".")},
                    extensions={"java": {"config_file": config_path.name}},
                )
            )
    return objects


def scan_java_configs_and_dependencies(source_root: Path) -> List[ImplementationObject]:
    return _scan_build_dependencies(source_root) + _scan_config_surfaces(source_root)
