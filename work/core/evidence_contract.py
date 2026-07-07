from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .common import ensure_identifier, serialize


class EvidenceSource(str, Enum):
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TRACEABILITY = "traceability"
    REPORT = "report"


class MissingEvidence(str, Enum):
    NOT_APPLICABLE = "not_applicable"
    NOT_EXTRACTED = "not_extracted"
    NOT_ACCESSIBLE = "not_accessible"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EvidenceRef:
    source: EvidenceSource
    path: str
    locator: str
    excerpt: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ensure_identifier(self.path, "path")
        ensure_identifier(self.locator, "locator")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source.value,
            "path": self.path,
            "locator": self.locator,
            "excerpt": self.excerpt,
            "metadata": serialize(self.metadata),
        }


@dataclass(frozen=True)
class EvidenceBundle:
    design: List[EvidenceRef] = field(default_factory=list)
    implementation: List[EvidenceRef] = field(default_factory=list)
    missing_design_reason: Optional[MissingEvidence] = None
    missing_implementation_reason: Optional[MissingEvidence] = None

    def __post_init__(self) -> None:
        if not self.design and self.missing_design_reason is None:
            raise ValueError("design evidence or missing_design_reason is required")
        if not self.implementation and self.missing_implementation_reason is None:
            raise ValueError("implementation evidence or missing_implementation_reason is required")

    def has_both_sides(self) -> bool:
        return bool(self.design) and bool(self.implementation)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "design": [item.to_dict() for item in self.design],
            "implementation": [item.to_dict() for item in self.implementation],
            "missing_design_reason": self.missing_design_reason.value if self.missing_design_reason else "",
            "missing_implementation_reason": (
                self.missing_implementation_reason.value if self.missing_implementation_reason else ""
            ),
        }
