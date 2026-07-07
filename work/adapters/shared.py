from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping

from core.common import ExtensionMap, ModelEnvelope, stable_id
from core.evidence_contract import EvidenceRef, EvidenceSource
from core.implementation_model import ImplementationModel, ImplementationObject


def relative_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def find_line_number(text: str, snippet: str) -> int:
    for line_number, line in enumerate(text.splitlines(), start=1):
        if snippet in line:
            return line_number
    return 1


def evidence_for_path(root: Path, path: Path, locator: str, excerpt: str = "", **metadata: Any) -> EvidenceRef:
    return EvidenceRef(
        source=EvidenceSource.IMPLEMENTATION,
        path=relative_path(root, path),
        locator=locator,
        excerpt=excerpt,
        metadata=metadata,
    )


def build_object(
    root: Path,
    adapter_id: str,
    namespace: str,
    kind: str,
    name: str,
    summary: str,
    path: Path,
    locator: str,
    excerpt: str = "",
    *,
    confidence: str = "high",
    normalization_status: str = "canonical",
    tags: List[str] | None = None,
    attributes: Dict[str, Any] | None = None,
    extensions: Dict[str, Any] | None = None,
) -> ImplementationObject:
    return ImplementationObject(
        id=stable_id(namespace, kind, name),
        kind=kind,
        name=name,
        summary=summary,
        evidence_refs=[evidence_for_path(root, path, locator, excerpt)],
        adapter_id=adapter_id,
        normalization_status=normalization_status,
        confidence=confidence,
        tags=tags or [],
        attributes=attributes or {},
        extensions=ExtensionMap(extensions or {}),
    )


@dataclass(frozen=True)
class DetectionSignal:
    kind: str
    value: str
    source_path: str = ""
    detail: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "kind": self.kind,
            "value": self.value,
            "source_path": self.source_path,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class AdapterSelection:
    adapter_id: str
    selected: bool
    fallback_used: bool
    confidence: str
    reasons: List[str] = field(default_factory=list)
    signals: List[DetectionSignal] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "selected": self.selected,
            "fallback_used": self.fallback_used,
            "confidence": self.confidence,
            "reasons": list(self.reasons),
            "signals": [signal.to_dict() for signal in self.signals],
        }


@dataclass(frozen=True)
class AdapterScanResult:
    selection: AdapterSelection
    implementation_model: ImplementationModel
    inventory: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selection": self.selection.to_dict(),
            "implementation_model": self.implementation_model.to_dict(),
            "inventory": self.inventory,
        }


class SourceAdapter(ABC):
    adapter_id: str

    @abstractmethod
    def detect(self, source_root: Path, profile: Mapping[str, Any]) -> AdapterSelection:
        raise NotImplementedError

    @abstractmethod
    def extract(self, source_root: Path, profile: Mapping[str, Any], selection: AdapterSelection) -> AdapterScanResult:
        raise NotImplementedError


def build_model(generated_by: str, objects: List[ImplementationObject]) -> ImplementationModel:
    if not objects:
        placeholder = ImplementationObject(
            id=stable_id("implementation", "module", "empty-source-root"),
            kind="module",
            name="empty-source-root",
            summary="No implementation objects were detected for the source root.",
            evidence_refs=[
                EvidenceRef(
                    source=EvidenceSource.IMPLEMENTATION,
                    path="SOURCE_ROOT",
                    locator="source-root",
                    excerpt="",
                    metadata={"generated_by": generated_by},
                )
            ],
            adapter_id="generic",
            normalization_status="partial",
            confidence="low",
            tags=["inventory"],
        )
        objects = [placeholder]
    return ImplementationModel(
        envelope=ModelEnvelope(schema_version="1.0", model_name="implementation-model", generated_by=generated_by),
        objects=objects,
    )
