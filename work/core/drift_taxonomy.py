from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict

from .common import ensure_identifier, ensure_kind, ensure_summary


class DriftCategory(str, Enum):
    API_CONTRACT = "api_contract"
    DATA_MODEL = "data_model"
    STATE_FLOW = "state_flow"
    BUSINESS_RULE = "business_rule"
    ERROR_HANDLING = "error_handling"
    CONFIG = "config"
    SECURITY = "security"
    TEST_COVERAGE = "test_coverage"


class DriftStatus(str, Enum):
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True)
class TaxonomyEntry:
    category: DriftCategory
    kind: str
    summary: str
    guidance: str
    attributes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ensure_kind(self.kind)
        ensure_summary(self.summary)
        ensure_identifier(self.guidance, "guidance")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "kind": ensure_kind(self.kind),
            "summary": self.summary,
            "guidance": self.guidance,
            "attributes": self.attributes,
        }
