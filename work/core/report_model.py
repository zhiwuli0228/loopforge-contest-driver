from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .common import ModelEnvelope, ensure_identifier, ensure_summary
from .drift_taxonomy import DriftCategory, DriftStatus
from .evidence_contract import EvidenceBundle
from .severity_policy import RiskLevel, SeverityAssessment, SeverityLevel


@dataclass(frozen=True)
class DriftFinding:
    id: str
    title: str
    summary: str
    category: DriftCategory
    status: DriftStatus
    traceability_ref: str
    evidence: EvidenceBundle
    assessment: SeverityAssessment
    attributes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ensure_identifier(self.id, "id")
        ensure_identifier(self.title, "title")
        ensure_summary(self.summary)
        ensure_identifier(self.traceability_ref, "traceability_ref")
        if not self.evidence.has_both_sides() and not (
            self.evidence.missing_design_reason or self.evidence.missing_implementation_reason
        ):
            raise ValueError("findings require both evidence sides or an explicit missing reason")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "category": self.category.value,
            "status": self.status.value,
            "traceability_ref": self.traceability_ref,
            "evidence": self.evidence.to_dict(),
            "assessment": self.assessment.to_dict(),
            "attributes": self.attributes,
        }


@dataclass(frozen=True)
class ReportSummary:
    total_findings: int
    confirmed_findings: int
    severe_findings: int
    status: str

    def __post_init__(self) -> None:
        ensure_identifier(self.status, "status")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_findings": self.total_findings,
            "confirmed_findings": self.confirmed_findings,
            "severe_findings": self.severe_findings,
            "status": self.status,
        }


@dataclass(frozen=True)
class RiskRollup:
    highest_severity: SeverityLevel
    highest_risk: RiskLevel
    rationale: str

    def __post_init__(self) -> None:
        ensure_identifier(self.rationale, "rationale")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "highest_severity": self.highest_severity.value,
            "highest_risk": self.highest_risk.value,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class ConsistencyReport:
    envelope: ModelEnvelope
    summary: ReportSummary
    risk_rollup: RiskRollup
    findings: List[DriftFinding]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "envelope": self.envelope.to_dict(),
            "summary": self.summary.to_dict(),
            "risk_rollup": self.risk_rollup.to_dict(),
            "findings": [item.to_dict() for item in self.findings],
            "metadata": self.metadata,
        }
