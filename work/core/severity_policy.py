from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

from .common import ensure_identifier
from .drift_taxonomy import DriftCategory


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    BLOCKING = "blocking"


@dataclass(frozen=True)
class SeverityAssessment:
    severity: SeverityLevel
    risk: RiskLevel
    rationale: str
    categories: List[DriftCategory] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ensure_identifier(self.rationale, "rationale")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity.value,
            "risk": self.risk.value,
            "rationale": self.rationale,
            "categories": [item.value for item in self.categories],
            "attributes": self.attributes,
        }
