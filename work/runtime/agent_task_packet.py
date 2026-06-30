from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class GateRecord:
    name: str
    passed: bool
    detail: str
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "detail": self.detail,
            "payload": self.payload,
        }


@dataclass
class RuntimePaths:
    workspace_root: Path
    work_dir: Path
    source_root: Path
    result_dir: Path
    log_dir: Path
    trace_dir: Path
    artifact_dir: Path
    migration_trace_dir: Path
    project_dir: Path

    def to_dict(self) -> Dict[str, str]:
        return {
            "workspace_root": str(self.workspace_root),
            "work_dir": str(self.work_dir),
            "source_root": str(self.source_root),
            "result_dir": str(self.result_dir),
            "log_dir": str(self.log_dir),
            "trace_dir": str(self.trace_dir),
            "artifact_dir": str(self.artifact_dir),
            "migration_trace_dir": str(self.migration_trace_dir),
            "project_dir": str(self.project_dir),
        }


@dataclass
class SourceLayout:
    readme_path: Optional[Path]
    flashdb_root: Optional[Path]
    src_dir: Optional[Path]
    tests_dir: Optional[Path]

    def to_dict(self) -> Dict[str, str]:
        return {
            "readme_path": str(self.readme_path) if self.readme_path else "",
            "flashdb_root": str(self.flashdb_root) if self.flashdb_root else "",
            "src_dir": str(self.src_dir) if self.src_dir else "",
            "tests_dir": str(self.tests_dir) if self.tests_dir else "",
        }


@dataclass
class AgentTaskPacket:
    paths: RuntimePaths
    config: Dict[str, Any]
    profile: Dict[str, Any]
    readme_candidates: List[str]
    max_repair_rounds: int
    source_layout: Optional[SourceLayout] = None
    gates: Dict[str, GateRecord] = field(default_factory=dict)
    issues: List[Dict[str, str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_issue(self, code: str, detail: str) -> None:
        candidate = {"code": code, "detail": detail}
        if candidate not in self.issues:
            self.issues.append(candidate)

    def add_warning(self, detail: str) -> None:
        self.warnings.append(detail)

    def set_gate(self, name: str, passed: bool, detail: str, payload: Optional[Dict[str, Any]] = None) -> None:
        self.gates[name] = GateRecord(name=name, passed=passed, detail=detail, payload=payload or {})

    def ready(self) -> bool:
        required = ["cargo_build", "cargo_test", "unsafe", "semantic"]
        return all(self.gates.get(name) and self.gates[name].passed for name in required)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "paths": self.paths.to_dict(),
            "source_layout": self.source_layout.to_dict() if self.source_layout else {},
            "readme_candidates": self.readme_candidates,
            "max_repair_rounds": self.max_repair_rounds,
            "issues": self.issues,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "gates": {name: gate.to_dict() for name, gate in self.gates.items()},
        }
