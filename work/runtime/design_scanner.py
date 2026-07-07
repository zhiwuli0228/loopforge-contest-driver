from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from core.common import ExtensionMap, ModelEnvelope, stable_id
from core.design_model import DesignModel, DesignObject, DesignRelationship
from core.evidence_contract import EvidenceRef, EvidenceSource


TEXT_SUFFIXES = {".md", ".markdown", ".txt", ".rst"}
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


def _relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _iter_design_files(design_root: Path) -> List[Path]:
    files = [path for path in design_root.rglob("*") if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES]
    return sorted(files)


def _evidence(root: Path, path: Path, locator: str, excerpt: str = "", **metadata: Any) -> EvidenceRef:
    return EvidenceRef(
        source=EvidenceSource.DESIGN,
        path=_relative_path(root, path),
        locator=locator,
        excerpt=excerpt,
        metadata=metadata,
    )


def _extract_summary(lines: List[str], start: int, stop: int) -> str:
    summary_lines: List[str] = []
    for line in lines[start:stop]:
        stripped = line.strip()
        if not stripped:
            if summary_lines:
                break
            continue
        if stripped.startswith("#"):
            break
        summary_lines.append(stripped.lstrip("-* ").strip())
        if len(summary_lines) >= 3:
            break
    if summary_lines:
        return " ".join(summary_lines)
    return "No explicit summary text was available in the design source."


def _parse_headings(text: str) -> List[Tuple[int, int, str]]:
    headings: List[Tuple[int, int, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = HEADING_RE.match(line)
        if match:
            headings.append((line_number, len(match.group(1)), match.group(2).strip()))
    return headings


def _heading_kind(level: int) -> str:
    if level <= 2:
        return "capability"
    if level == 3:
        return "constraint"
    return "detail"


def _document_name(path: Path, text: str) -> str:
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            return match.group(2).strip()
    return path.stem


def scan_design_root(design_root: str | Path) -> Dict[str, Any]:
    root = Path(design_root)
    if not root.is_dir():
        raise ValueError(f"design-root does not exist: {root}")

    files = _iter_design_files(root)
    if not files:
        raise ValueError(f"design-root has no supported design files: {root}")

    inventory_files: List[Dict[str, Any]] = []
    objects: List[DesignObject] = []
    evidence_index: List[Dict[str, Any]] = []

    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        rel_path = _relative_path(root, path)
        headings = _parse_headings(text)
        title = _document_name(path, text)
        doc_id = stable_id(f"design:{rel_path}", "document", title)
        doc_summary = _extract_summary(lines, 0, len(lines))
        doc_evidence = _evidence(root, path, "line:1", title, title=title)
        objects.append(
            DesignObject(
                id=doc_id,
                kind="document",
                name=title,
                summary=doc_summary,
                evidence_refs=[doc_evidence],
                tags=["design_document"],
                attributes={"path": rel_path, "heading_count": len(headings)},
                extensions=ExtensionMap({"design": {"document_path": rel_path}}),
            )
        )
        evidence_index.append({"object_id": doc_id, "evidence": [doc_evidence.to_dict()]})

        for index, (line_number, level, heading_text) in enumerate(headings):
            next_line = headings[index + 1][0] - 1 if index + 1 < len(headings) else len(lines)
            summary = _extract_summary(lines, line_number, next_line)
            heading_id = stable_id(f"design:{rel_path}", _heading_kind(level), heading_text)
            heading_evidence = _evidence(
                root,
                path,
                f"line:{line_number}",
                heading_text,
                heading_level=level,
                title=heading_text,
            )
            objects.append(
                DesignObject(
                    id=heading_id,
                    kind=_heading_kind(level),
                    name=heading_text,
                    summary=summary,
                    evidence_refs=[heading_evidence],
                    tags=["design_heading"],
                    attributes={"path": rel_path, "heading_level": level},
                    relationships=[DesignRelationship(relation="documented_in", target_id=doc_id)],
                )
            )
            evidence_index.append({"object_id": heading_id, "evidence": [heading_evidence.to_dict()]})

        inventory_files.append(
            {
                "path": rel_path,
                "title": title,
                "heading_count": len(headings),
                "line_count": len(lines),
                "byte_count": len(text.encode("utf-8")),
                "is_primary": rel_path == "README.md",
            }
        )

    model = DesignModel(
        envelope=ModelEnvelope(schema_version="1.0", model_name="design-model", generated_by="design-scanner"),
        objects=objects,
    )
    inventory = {
        "design_root": str(root),
        "primary_design_file": "README.md" if (root / "README.md").is_file() else inventory_files[0]["path"],
        "file_count": len(inventory_files),
        "files": inventory_files,
        "object_count": len(objects),
    }
    summary = {
        "design_root": str(root),
        "file_count": len(inventory_files),
        "object_count": len(objects),
        "primary_design_file": inventory["primary_design_file"],
    }
    return {
        "inventory": inventory,
        "design_model": model.to_dict(),
        "evidence_index": {"entries": evidence_index},
        "summary": summary,
    }
