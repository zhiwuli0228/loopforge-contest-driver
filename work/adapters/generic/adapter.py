from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

from adapters.shared import AdapterScanResult, AdapterSelection, DetectionSignal, build_model
from core.implementation_model import ImplementationObject

from .generic_config_scanner import scan_generic_configs
from .generic_file_inventory import scan_generic_files
from .generic_symbol_indexer import scan_generic_symbols
from .generic_test_detector import scan_generic_tests
from .generic_text_evidence_scanner import scan_generic_text_evidence


class GenericAdapter:
    adapter_id = "generic"

    def detect(self, source_root: Path, profile: Mapping[str, Any]) -> AdapterSelection:
        file_count = len([path for path in source_root.rglob("*") if path.is_file()])
        signals = [DetectionSignal(kind="fallback", value="generic_inventory", detail=f"file_count={file_count}")]
        return AdapterSelection(
            adapter_id=self.adapter_id,
            selected=True,
            fallback_used=True,
            confidence="medium" if file_count else "low",
            reasons=["generic fallback remains available for any repository layout"],
            signals=signals,
        )

    def extract(self, source_root: Path, profile: Mapping[str, Any], selection: AdapterSelection) -> AdapterScanResult:
        objects: list[ImplementationObject] = []
        objects.extend(scan_generic_files(source_root))
        objects.extend(scan_generic_symbols(source_root))
        objects.extend(scan_generic_configs(source_root))
        objects.extend(scan_generic_tests(source_root))
        objects.extend(scan_generic_text_evidence(source_root))
        inventory: Dict[str, Any] = {
            "adapter_id": self.adapter_id,
            "object_count": len(objects),
            "file_count": len([path for path in source_root.rglob("*") if path.is_file()]),
            "partial_mode": True,
        }
        return AdapterScanResult(
            selection=selection,
            implementation_model=build_model("generic-adapter", objects),
            inventory=inventory,
        )
