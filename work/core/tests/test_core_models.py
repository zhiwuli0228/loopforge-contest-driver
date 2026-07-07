import sys
import unittest
from pathlib import Path


CORE_ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = CORE_ROOT.parent
sys.path.insert(0, str(WORK_ROOT))

from core.common import FORBIDDEN_REQUIRED_TERMS, ModelEnvelope, stable_id  # noqa: E402
from core.design_model import DesignModel, DesignObject, DesignRelationship  # noqa: E402
from core.drift_taxonomy import DriftCategory, DriftStatus, TaxonomyEntry  # noqa: E402
from core.evidence_contract import EvidenceBundle, EvidenceRef, EvidenceSource, MissingEvidence  # noqa: E402
from core.implementation_model import (  # noqa: E402
    ImplementationModel,
    ImplementationObject,
    ImplementationRelationship,
)
from core.report_model import ConsistencyReport, DriftFinding, ReportSummary, RiskRollup  # noqa: E402
from core.severity_policy import RiskLevel, SeverityAssessment, SeverityLevel  # noqa: E402
from core.traceability_model import CoverageStatus, TraceGap, TraceLink, TraceabilityMatrix  # noqa: E402


def design_ref() -> EvidenceRef:
    return EvidenceRef(
        source=EvidenceSource.DESIGN,
        path="work/design/README.md",
        locator="L10-L18",
        excerpt="Order placement shall validate stock.",
    )


def implementation_ref() -> EvidenceRef:
    return EvidenceRef(
        source=EvidenceSource.IMPLEMENTATION,
        path="SOURCE_ROOT/src/order_flow.py",
        locator="OrderFlow.validate_inventory",
        excerpt="validate_inventory()",
    )


class CoreModelsTests(unittest.TestCase):
    def test_design_and_implementation_models_serialize_with_neutral_kinds(self):
        envelope = ModelEnvelope(schema_version="1.0", model_name="design-model", generated_by="unit-test")
        design = DesignModel(
            envelope=envelope,
            objects=[
                DesignObject(
                    id=stable_id("design", "component", "order orchestration"),
                    kind="component",
                    name="Order Orchestration",
                    summary="Coordinates order validation and submission.",
                    evidence_refs=[design_ref()],
                    tags=["business_rule"],
                    relationships=[DesignRelationship(relation="depends_on", target_id="design:interface:inventory_port")],
                )
            ],
        )
        implementation = ImplementationModel(
            envelope=ModelEnvelope(schema_version="1.0", model_name="implementation-model", generated_by="unit-test"),
            objects=[
                ImplementationObject(
                    id=stable_id("implementation", "entrypoint", "submit order"),
                    kind="entrypoint",
                    name="submit_order",
                    summary="Accepts an order request and dispatches validation.",
                    evidence_refs=[implementation_ref()],
                    adapter_id="generic",
                    normalization_status="canonical",
                    confidence="high",
                    tags=["api_contract"],
                    relationships=[
                        ImplementationRelationship(relation="calls", target_id="implementation:module:inventory_validation")
                    ],
                )
            ],
        )
        self.assertEqual(design.to_dict()["objects"][0]["kind"], "component")
        self.assertEqual(implementation.to_dict()["objects"][0]["kind"], "entrypoint")
        self.assertEqual(implementation.to_dict()["objects"][0]["adapter_id"], "generic")

    def test_traceability_gap_captures_missing_implementation_reason(self):
        bundle = EvidenceBundle(
            design=[design_ref()],
            implementation=[],
            missing_implementation_reason=MissingEvidence.NOT_EXTRACTED,
        )
        gap = TraceGap(
            design_id="design:component:order_orchestration",
            coverage_status=CoverageStatus.MISSING_IMPLEMENTATION,
            rationale="No implementation object matched the design component.",
            evidence=bundle,
            expected_kind="component",
        )
        matrix = TraceabilityMatrix(
            envelope=ModelEnvelope(schema_version="1.0", model_name="traceability", generated_by="unit-test"),
            gaps=[gap],
        )
        self.assertEqual(matrix.to_dict()["gaps"][0]["coverage_status"], "missing_implementation")

    def test_report_finding_requires_auditable_evidence_and_assessment(self):
        evidence = EvidenceBundle(design=[design_ref()], implementation=[implementation_ref()])
        finding = DriftFinding(
            id="finding-1",
            title="Inventory validation drift",
            summary="Implementation skips the required inventory validation path.",
            category=DriftCategory.BUSINESS_RULE,
            status=DriftStatus.CONFIRMED,
            traceability_ref="trace-001",
            evidence=evidence,
            assessment=SeverityAssessment(
                severity=SeverityLevel.HIGH,
                risk=RiskLevel.HIGH,
                rationale="Orders can be accepted without enforced stock checks.",
                categories=[DriftCategory.BUSINESS_RULE],
            ),
        )
        report = ConsistencyReport(
            envelope=ModelEnvelope(schema_version="1.0", model_name="report", generated_by="unit-test"),
            summary=ReportSummary(total_findings=1, confirmed_findings=1, severe_findings=1, status="FINALIZED_WITH_FINDINGS"),
            risk_rollup=RiskRollup(
                highest_severity=SeverityLevel.HIGH,
                highest_risk=RiskLevel.HIGH,
                rationale="Confirmed business-rule drift is user-visible.",
            ),
            findings=[finding],
        )
        self.assertEqual(report.to_dict()["findings"][0]["assessment"]["severity"], "high")

    def test_forbidden_terms_are_rejected_from_required_kinds(self):
        with self.assertRaises(ValueError):
            DesignObject(
                id="design:controller:orders",
                kind="controller",
                name="Orders Controller",
                summary="Should be rejected because the kind is framework-specific.",
                evidence_refs=[design_ref()],
            )
        self.assertIn("controller", FORBIDDEN_REQUIRED_TERMS)

    def test_taxonomy_entry_uses_shared_category_names(self):
        taxonomy = TaxonomyEntry(
            category=DriftCategory.API_CONTRACT,
            kind="signature_mismatch",
            summary="Declared API differs from implementation.",
            guidance="Review the design contract and implementation signature mapping.",
        )
        self.assertEqual(taxonomy.to_dict()["category"], "api_contract")

    def test_trace_links_can_record_partial_coverage(self):
        evidence = EvidenceBundle(design=[design_ref()], implementation=[implementation_ref()])
        link = TraceLink(
            design_id="design:interface:inventory_port",
            implementation_id="implementation:symbol:inventory_adapter",
            coverage_status=CoverageStatus.PARTIAL,
            rationale="Validation exists but misses one exceptional branch.",
            evidence=evidence,
        )
        matrix = TraceabilityMatrix(
            envelope=ModelEnvelope(schema_version="1.0", model_name="traceability", generated_by="unit-test"),
            links=[link],
            unresolved_reference_ids=["design:constraint:stock_timeout"],
        )
        self.assertEqual(matrix.to_dict()["links"][0]["coverage_status"], "partial")


if __name__ == "__main__":
    unittest.main()
