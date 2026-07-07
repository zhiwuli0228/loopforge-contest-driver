from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

from .common import ModelEnvelope, ensure_identifier
from .evidence_contract import EvidenceBundle


class CoverageStatus(str, Enum):
    MATCHED = "matched"
    PARTIAL = "partial"
    MISSING_IMPLEMENTATION = "missing_implementation"
    MISSING_DESIGN = "missing_design"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class TraceLink:
    design_id: str
    implementation_id: str
    coverage_status: CoverageStatus
    rationale: str
    evidence: EvidenceBundle
    attributes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ensure_identifier(self.design_id, "design_id")
        ensure_identifier(self.implementation_id, "implementation_id")
        ensure_identifier(self.rationale, "rationale")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "design_id": self.design_id,
            "implementation_id": self.implementation_id,
            "coverage_status": self.coverage_status.value,
            "rationale": self.rationale,
            "evidence": self.evidence.to_dict(),
            "attributes": self.attributes,
        }


@dataclass(frozen=True)
class TraceGap:
    design_id: str
    coverage_status: CoverageStatus
    rationale: str
    evidence: EvidenceBundle
    expected_kind: str = ""

    def __post_init__(self) -> None:
        ensure_identifier(self.design_id, "design_id")
        ensure_identifier(self.rationale, "rationale")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "design_id": self.design_id,
            "coverage_status": self.coverage_status.value,
            "rationale": self.rationale,
            "evidence": self.evidence.to_dict(),
            "expected_kind": self.expected_kind,
        }


@dataclass(frozen=True)
class TraceabilityMatrix:
    envelope: ModelEnvelope
    links: List[TraceLink] = field(default_factory=list)
    gaps: List[TraceGap] = field(default_factory=list)
    unresolved_reference_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "envelope": self.envelope.to_dict(),
            "links": [item.to_dict() for item in self.links],
            "gaps": [item.to_dict() for item in self.gaps],
            "unresolved_reference_ids": list(self.unresolved_reference_ids),
        }
