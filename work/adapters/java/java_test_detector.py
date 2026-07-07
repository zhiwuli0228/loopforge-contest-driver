from __future__ import annotations

from pathlib import Path
from typing import List

from adapters.shared import build_object, read_text
from core.implementation_model import ImplementationObject


TEST_SUFFIXES = ("Test.java", "Tests.java")


def scan_java_tests(source_root: Path) -> List[ImplementationObject]:
    objects: List[ImplementationObject] = []
    for test_file in source_root.rglob("*.java"):
        if not test_file.name.endswith(TEST_SUFFIXES) and "src/test/java" not in test_file.as_posix():
            continue
        text = read_text(test_file)
        preview = next((line.strip() for line in text.splitlines() if line.strip()), test_file.stem)
        objects.append(
            build_object(
                source_root,
                "java",
                "implementation",
                "test_artifact",
                test_file.stem,
                f"Java test artifact discovered in {test_file.name}.",
                test_file,
                "L1",
                preview,
                tags=["test_coverage"],
                attributes={"test_framework_hint": "junit"},
                extensions={"java": {"test_file": test_file.name}},
            )
        )
    return objects
