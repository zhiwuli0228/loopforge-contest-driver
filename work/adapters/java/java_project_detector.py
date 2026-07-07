from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from adapters.shared import AdapterSelection, DetectionSignal, relative_path


JAVA_BUILD_FILES = ("pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts")


def detect_java_project(source_root: Path, profile: Mapping[str, Any]) -> AdapterSelection:
    signals: list[DetectionSignal] = []
    reasons: list[str] = []

    for name in JAVA_BUILD_FILES:
        candidate = source_root / name
        if candidate.exists():
            signals.append(DetectionSignal(kind="build_file", value=name, source_path=relative_path(source_root, candidate)))

    java_files = list(source_root.rglob("*.java"))
    if java_files:
        signals.append(DetectionSignal(kind="source_glob", value="**/*.java", source_path=relative_path(source_root, java_files[0])))

    source_layouts = [source_root / "src" / "main" / "java", source_root / "src" / "test" / "java"]
    for layout in source_layouts:
        if layout.is_dir():
            signals.append(DetectionSignal(kind="source_layout", value=relative_path(source_root, layout)))

    if not signals:
        reasons.append("no Java build files, source layout, or .java files were detected")
        return AdapterSelection(
            adapter_id="java",
            selected=False,
            fallback_used=False,
            confidence="low",
            reasons=reasons,
            signals=[],
        )

    confidence = "high" if any(signal.kind == "build_file" for signal in signals) else "medium"
    reasons.append("detected Java project signals required by the default profile")
    return AdapterSelection(
        adapter_id="java",
        selected=True,
        fallback_used=False,
        confidence=confidence,
        reasons=reasons,
        signals=signals,
    )
