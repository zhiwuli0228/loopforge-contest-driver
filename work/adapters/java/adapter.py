from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

from adapters.shared import AdapterScanResult, AdapterSelection, build_model, build_object, read_text
from core.implementation_model import ImplementationObject

from .java_config_scanner import scan_java_configs_and_dependencies
from .java_dto_scanner import scan_java_data_shapes
from .java_endpoint_scanner import scan_java_endpoints
from .java_project_detector import detect_java_project
from .java_test_detector import scan_java_tests


class JavaAdapter:
    adapter_id = "java"

    def detect(self, source_root: Path, profile: Mapping[str, Any]) -> AdapterSelection:
        return detect_java_project(source_root, profile)

    def extract(self, source_root: Path, profile: Mapping[str, Any], selection: AdapterSelection) -> AdapterScanResult:
        objects: list[ImplementationObject] = []
        module_objects = self._scan_modules(source_root)
        objects.extend(module_objects)
        objects.extend(scan_java_endpoints(source_root))
        objects.extend(scan_java_data_shapes(source_root))
        objects.extend(scan_java_configs_and_dependencies(source_root))
        objects.extend(scan_java_tests(source_root))

        inventory: Dict[str, Any] = {
            "adapter_id": self.adapter_id,
            "module_count": len(module_objects),
            "object_count": len(objects),
            "java_file_count": len(list(source_root.rglob("*.java"))),
        }
        return AdapterScanResult(
            selection=selection,
            implementation_model=build_model("java-adapter", objects),
            inventory=inventory,
        )

    def _scan_modules(self, source_root: Path) -> list[ImplementationObject]:
        objects: list[ImplementationObject] = []
        roots = [source_root / "src" / "main" / "java", source_root / "src" / "test" / "java"]
        for root in roots:
            if not root.exists():
                continue
            summary = f"Java source module rooted at {root.relative_to(source_root).as_posix()}."
            objects.append(
                build_object(
                    source_root,
                    self.adapter_id,
                    "implementation",
                    "module",
                    root.name,
                    summary,
                    root,
                    "root",
                    root.as_posix(),
                    tags=["inventory"],
                    attributes={"module_path": root.relative_to(source_root).as_posix()},
                    extensions={"java": {"module_root": root.as_posix()}},
                )
            )
        if not objects:
            preview = next(iter(source_root.glob("*")), source_root)
            objects.append(
                build_object(
                    source_root,
                    self.adapter_id,
                    "implementation",
                    "module",
                    source_root.name,
                    "Java adapter detected source evidence without conventional src/main/java layout.",
                    preview,
                    "root",
                    source_root.name,
                    confidence="medium",
                    tags=["inventory"],
                    extensions={"java": {"layout": "nonstandard"}},
                )
            )
        return objects
