from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping

from .generic.adapter import GenericAdapter
from .java.adapter import JavaAdapter
from .shared import AdapterScanResult, AdapterSelection, DetectionSignal, SourceAdapter


@dataclass
class AdapterRegistry:
    adapters: Dict[str, SourceAdapter]

    def get(self, adapter_id: str) -> SourceAdapter:
        if adapter_id not in self.adapters:
            raise KeyError(f"unknown adapter: {adapter_id}")
        return self.adapters[adapter_id]

    def select(self, source_root: Path, profile: Mapping[str, Any]) -> AdapterSelection:
        task_language = profile.get("task", {}).get("language", {})
        default_id = task_language.get("default_adapter", "java")
        fallback_id = task_language.get("fallback_adapter", "generic")

        primary = self.get(default_id)
        primary_selection = primary.detect(source_root, profile)
        if primary_selection.selected:
            return primary_selection

        fallback = self.get(fallback_id)
        fallback_selection = fallback.detect(source_root, profile)
        fallback_reasons = list(primary_selection.reasons) + [f"fell back from {default_id}"]
        fallback_signals = list(fallback_selection.signals)
        fallback_signals.append(
            DetectionSignal(kind="fallback_reason", value="primary_adapter_rejected", detail="; ".join(primary_selection.reasons))
        )
        return AdapterSelection(
            adapter_id=fallback_selection.adapter_id,
            selected=True,
            fallback_used=True,
            confidence=fallback_selection.confidence,
            reasons=fallback_reasons,
            signals=fallback_signals,
        )

    def extract(self, source_root: Path, profile: Mapping[str, Any], adapter_id: str | None = None) -> AdapterScanResult:
        selection = self.select(source_root, profile) if adapter_id is None else AdapterSelection(
            adapter_id=adapter_id,
            selected=True,
            fallback_used=False,
            confidence="high",
            reasons=["adapter override"],
            signals=[DetectionSignal(kind="override", value=adapter_id)],
        )
        return self.get(selection.adapter_id).extract(source_root, profile, selection)


def build_default_registry() -> AdapterRegistry:
    return AdapterRegistry(adapters={"java": JavaAdapter(), "generic": GenericAdapter()})
