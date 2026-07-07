from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .common import ExtensionMap, ModelEnvelope, ensure_identifier, ensure_kind, ensure_neutral_collection, ensure_summary
from .evidence_contract import EvidenceRef


@dataclass(frozen=True)
class DesignRelationship:
    relation: str
    target_id: str
    attributes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ensure_kind(self.relation, "relation")
        ensure_identifier(self.target_id, "target_id")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation": ensure_kind(self.relation, "relation"),
            "target_id": self.target_id,
            "attributes": self.attributes,
        }


@dataclass(frozen=True)
class DesignObject:
    id: str
    kind: str
    name: str
    summary: str
    evidence_refs: List[EvidenceRef]
    tags: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    relationships: List[DesignRelationship] = field(default_factory=list)
    extensions: ExtensionMap = field(default_factory=ExtensionMap)

    def __post_init__(self) -> None:
        ensure_identifier(self.id, "id")
        ensure_kind(self.kind)
        ensure_identifier(self.name, "name")
        ensure_summary(self.summary)
        if not self.evidence_refs:
            raise ValueError("design objects require evidence_refs")
        ensure_neutral_collection(self.tags, "tags")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "kind": ensure_kind(self.kind),
            "name": self.name,
            "summary": self.summary,
            "evidence_refs": [item.to_dict() for item in self.evidence_refs],
            "tags": ensure_neutral_collection(self.tags, "tags"),
            "attributes": self.attributes,
            "relationships": [item.to_dict() for item in self.relationships],
            "extensions": self.extensions.to_dict(),
        }


@dataclass(frozen=True)
class DesignModel:
    envelope: ModelEnvelope
    objects: List[DesignObject]

    def __post_init__(self) -> None:
        if not self.objects:
            raise ValueError("design model requires at least one object")

    def index_by_id(self) -> Dict[str, DesignObject]:
        return {item.id: item for item in self.objects}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "envelope": self.envelope.to_dict(),
            "objects": [item.to_dict() for item in self.objects],
        }
