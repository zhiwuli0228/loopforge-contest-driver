from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from core.common import ModelEnvelope, normalize_token
from core.evidence_contract import EvidenceBundle, EvidenceRef, EvidenceSource, MissingEvidence
from core.traceability_model import CoverageStatus, TraceGap, TraceLink, TraceabilityMatrix


TOKEN_RE = re.compile(r"[a-z0-9]+")


def _load_json(path_or_payload: str | Path | Mapping[str, Any]) -> Dict[str, Any]:
    if isinstance(path_or_payload, Mapping):
        return dict(path_or_payload)
    path = Path(path_or_payload)
    return json.loads(path.read_text(encoding="utf-8"))


def _tokens(*values: str) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        if not value:
            continue
        normalized = normalize_token(value)
        tokens.update(TOKEN_RE.findall(normalized))
    return tokens


def _coerce_evidence(refs: Sequence[Mapping[str, Any]], default_source: EvidenceSource) -> List[EvidenceRef]:
    evidence: List[EvidenceRef] = []
    for item in refs:
        source_value = item.get("source") or default_source.value
        evidence.append(
            EvidenceRef(
                source=EvidenceSource(source_value),
                path=item["path"],
                locator=item["locator"],
                excerpt=item.get("excerpt", ""),
                metadata=item.get("metadata", {}),
            )
        )
    return evidence


def _score_candidate(design_object: Mapping[str, Any], implementation_object: Mapping[str, Any]) -> int:
    design_name = normalize_token(design_object["name"])
    impl_name = normalize_token(implementation_object["name"])
    if design_name == impl_name:
        return 100
    design_tokens = _tokens(design_object["name"], design_object.get("summary", ""))
    impl_tokens = _tokens(implementation_object["name"], implementation_object.get("summary", ""))
    overlap = len(design_tokens & impl_tokens)
    if overlap == 0:
        return 0
    kind_bonus = 10 if design_object.get("kind") == implementation_object.get("kind") else 0
    return overlap * 10 + kind_bonus


def build_traceability(design_model: str | Path | Mapping[str, Any], implementation_model: str | Path | Mapping[str, Any]) -> Dict[str, Any]:
    design_payload = _load_json(design_model)
    implementation_payload = _load_json(implementation_model)
    design_objects = design_payload.get("objects", [])
    implementation_objects = implementation_payload.get("objects", [])

    links: List[TraceLink] = []
    gaps: List[TraceGap] = []
    unresolved: List[str] = []
    unmatched_implementation_ids = {item["id"] for item in implementation_objects}

    for design_object in design_objects:
        ranked: List[Tuple[int, Mapping[str, Any]]] = []
        for implementation_object in implementation_objects:
            score = _score_candidate(design_object, implementation_object)
            if score > 0:
                ranked.append((score, implementation_object))
        ranked.sort(key=lambda item: (-item[0], item[1]["id"]))

        design_evidence = _coerce_evidence(design_object.get("evidence_refs", []), EvidenceSource.DESIGN)
        if not ranked:
            gaps.append(
                TraceGap(
                    design_id=design_object["id"],
                    coverage_status=CoverageStatus.MISSING_IMPLEMENTATION,
                    rationale="No implementation object shared enough normalized naming or summary tokens.",
                    evidence=EvidenceBundle(
                        design=design_evidence,
                        implementation=[],
                        missing_implementation_reason=MissingEvidence.NOT_EXTRACTED,
                    ),
                    expected_kind=design_object.get("kind", ""),
                )
            )
            continue

        if len(ranked) > 1 and ranked[0][0] == ranked[1][0]:
            unresolved.append(design_object["id"])
            gaps.append(
                TraceGap(
                    design_id=design_object["id"],
                    coverage_status=CoverageStatus.AMBIGUOUS,
                    rationale="More than one implementation candidate had the same strongest score.",
                    evidence=EvidenceBundle(
                        design=design_evidence,
                        implementation=[],
                        missing_implementation_reason=MissingEvidence.AMBIGUOUS,
                    ),
                    expected_kind=design_object.get("kind", ""),
                )
            )
            continue

        score, implementation_object = ranked[0]
        unmatched_implementation_ids.discard(implementation_object["id"])
        implementation_evidence = _coerce_evidence(
            implementation_object.get("evidence_refs", []),
            EvidenceSource.IMPLEMENTATION,
        )
        coverage_status = CoverageStatus.MATCHED if score >= 100 else CoverageStatus.PARTIAL
        rationale = (
            "Exact normalized object-name match between design and implementation."
            if coverage_status is CoverageStatus.MATCHED
            else "Implementation object shares normalized naming or summary tokens with the design object."
        )
        links.append(
            TraceLink(
                design_id=design_object["id"],
                implementation_id=implementation_object["id"],
                coverage_status=coverage_status,
                rationale=rationale,
                evidence=EvidenceBundle(design=design_evidence, implementation=implementation_evidence),
                attributes={"score": score},
            )
        )

    matrix = TraceabilityMatrix(
        envelope=ModelEnvelope(schema_version="1.0", model_name="traceability-matrix", generated_by="traceability-builder"),
        links=links,
        gaps=gaps,
        unresolved_reference_ids=unresolved,
    ).to_dict()
    matrix["unmatched_implementation_ids"] = sorted(unmatched_implementation_ids)
    matrix["coverage_summary"] = {
        "matched_links": len([item for item in links if item.coverage_status is CoverageStatus.MATCHED]),
        "partial_links": len([item for item in links if item.coverage_status is CoverageStatus.PARTIAL]),
        "gaps": len(gaps),
        "unmatched_implementation_count": len(unmatched_implementation_ids),
        "unresolved_reference_count": len(unresolved),
    }
    return matrix


def render_traceability_summary(traceability_matrix: Mapping[str, Any]) -> str:
    summary = traceability_matrix.get("coverage_summary", {})
    lines = [
        "# Traceability Summary",
        "",
        f"- Matched links: {summary.get('matched_links', 0)}",
        f"- Partial links: {summary.get('partial_links', 0)}",
        f"- Design gaps: {summary.get('gaps', 0)}",
        f"- Unmatched implementation objects: {summary.get('unmatched_implementation_count', 0)}",
        f"- Unresolved references: {summary.get('unresolved_reference_count', 0)}",
    ]
    return "\n".join(lines) + "\n"
