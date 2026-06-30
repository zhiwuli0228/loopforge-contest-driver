from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


FRAMEWORK_DEFAULTS: Dict[str, Any] = {
    "source_project_name": "source_project",
    "source_language": "c",
    "target_language": "rust",
    "output_project_name": "c_to_rust_output",
    "source_dirs": ["src", "source"],
    "test_dirs": ["tests", "test"],
    "build_commands": ["cargo build", "cargo test"],
    "unsafe_ratio_max": 0.10,
    "api_name_hints": [],
    "module_hints": [],
}

README_NAME_RE = re.compile(r"(?im)^(?:#\s+)?(?:project name|题目名称|项目名称)\s*[:：]?\s*(.+)$")
README_OUTPUT_RE = re.compile(r"(?i)\b([A-Za-z0-9][A-Za-z0-9_-]*_rust)\b")
README_COMMAND_RE = re.compile(r"(?im)^\s*(cargo\s+(?:build|test)(?:\s+[^\n`]+)?)\s*$")
README_CODE_IDENT_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`")
README_FUNCTION_HINT_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*_[A-Za-z0-9_]+)\s*\(")
README_SOURCE_LINE_RE = re.compile(r"(?im)^\s*(?:source (?:dir|dirs|directory|directories)|源码目录)\s*[:：]\s*(.+)$")
README_TEST_LINE_RE = re.compile(r"(?im)^\s*(?:test (?:dir|dirs|directory|directories)|测试目录)\s*[:：]\s*(.+)$")
README_PATH_RE = re.compile(r"`([^`]+)`|(?<![A-Za-z0-9_./-])((?:SOURCE_ROOT/)?[A-Za-z0-9_./-]+)(?![A-Za-z0-9_./-])")


def _read_text(path: Optional[Path]) -> str:
    if path is None or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        ordered.append(normalized)
        seen.add(normalized)
    return ordered


def _parse_dir_hints(readme_text: str, suffixes: List[str]) -> List[str]:
    results: List[str] = []
    for raw_match, bare_match in README_PATH_RE.findall(readme_text):
        match = (raw_match or bare_match).strip()
        if not match:
            continue
        normalized = match.replace("\\", "/").strip("./")
        if normalized.startswith("SOURCE_ROOT/"):
            normalized = normalized[len("SOURCE_ROOT/") :]
        parts = [part for part in normalized.split("/") if part]
        if not parts:
            continue
        for index, part in enumerate(parts):
            lowered = part.lower()
            if lowered not in suffixes:
                continue
            candidate_parts = parts[: index + 1]
            if candidate_parts:
                results.append("/".join(candidate_parts))
            results.append(lowered)
            break
    line_patterns = []
    if any(item in suffixes for item in ["src", "source"]):
        line_patterns.append(README_SOURCE_LINE_RE)
    if any(item in suffixes for item in ["tests", "test"]):
        line_patterns.append(README_TEST_LINE_RE)
    for pattern in line_patterns:
        for match in pattern.findall(readme_text):
            for token in re.split(r"[,\s]+", match.strip()):
                normalized = token.replace("\\", "/").strip("./")
                if normalized.lower() in suffixes:
                    results.append(normalized.lower())
                elif "/" in normalized and normalized.split("/")[-1].lower() in suffixes:
                    results.append(normalized)
    return _dedupe(results)


def _parse_project_name(readme_text: str) -> Optional[str]:
    match = README_NAME_RE.search(readme_text)
    if match:
        return match.group(1).strip("` ").strip()
    for line in readme_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            candidate = stripped.lstrip("#").strip()
            if candidate:
                return candidate
    return None


def _parse_output_project_name(readme_text: str) -> Optional[str]:
    match = README_OUTPUT_RE.search(readme_text)
    return match.group(1) if match else None


def _parse_build_commands(readme_text: str) -> List[str]:
    return _dedupe(README_COMMAND_RE.findall(readme_text))


def _parse_api_hints(readme_text: str) -> List[str]:
    hints = README_FUNCTION_HINT_RE.findall(readme_text)
    hints.extend(name for name in README_CODE_IDENT_RE.findall(readme_text) if "_" in name and not name.isupper())
    return _dedupe(hints)


def _parse_module_hints(readme_text: str) -> List[str]:
    modules: List[str] = []
    for path_text in _parse_dir_hints(readme_text, ["src", "source", "tests", "test"]):
        parts = [part for part in path_text.split("/") if part]
        if len(parts) > 1:
            modules.extend(part for part in parts[:-1] if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", part))
    return _dedupe(modules)


def _coerce_float(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def resolve_runtime_contract(
    source_root: Path,
    work_dir: Path,
    readme_candidates: List[str],
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    source_readme: Optional[Path] = None
    for name in readme_candidates:
        candidate = source_root / name
        if candidate.is_file():
            source_readme = candidate.resolve()
            break

    fallback_readme = (work_dir / "code" / "README.md").resolve()
    fallback_readme = fallback_readme if fallback_readme.is_file() else None

    source_text = _read_text(source_readme)
    fallback_text = _read_text(fallback_readme)
    profile_defaults = profile.get("migration_defaults", {})

    source_dirs = _dedupe(
        _parse_dir_hints(source_text, ["src", "source"])
        or _parse_dir_hints(fallback_text, ["src", "source"])
        or [str(item) for item in profile_defaults.get("source_dirs", [])]
        or FRAMEWORK_DEFAULTS["source_dirs"]
    )
    test_dirs = _dedupe(
        _parse_dir_hints(source_text, ["tests", "test"])
        or _parse_dir_hints(fallback_text, ["tests", "test"])
        or [str(item) for item in profile_defaults.get("test_dirs", [])]
        or FRAMEWORK_DEFAULTS["test_dirs"]
    )
    build_commands = (
        _parse_build_commands(source_text)
        or _parse_build_commands(fallback_text)
        or [str(item) for item in profile_defaults.get("build_commands", [])]
        or list(FRAMEWORK_DEFAULTS["build_commands"])
    )
    api_name_hints = _dedupe(
        _parse_api_hints(source_text)
        or _parse_api_hints(fallback_text)
        or [str(item) for item in profile_defaults.get("api_name_hints", [])]
        or list(FRAMEWORK_DEFAULTS["api_name_hints"])
    )
    module_hints = _dedupe(
        _parse_module_hints(source_text)
        or _parse_module_hints(fallback_text)
        or [str(item) for item in profile_defaults.get("module_hints", [])]
        or list(FRAMEWORK_DEFAULTS["module_hints"])
    )

    output_project_name = (
        _parse_output_project_name(source_text)
        or _parse_output_project_name(fallback_text)
        or str(profile_defaults.get("output_project_name", ""))
        or str(FRAMEWORK_DEFAULTS["output_project_name"])
    )
    source_project_name = (
        _parse_project_name(source_text)
        or _parse_project_name(fallback_text)
        or str(profile_defaults.get("source_project_name", ""))
        or str(FRAMEWORK_DEFAULTS["source_project_name"])
    )
    source_language = (
        str(profile_defaults.get("source_language", "")).strip().lower()
        or str(FRAMEWORK_DEFAULTS["source_language"])
    )
    target_language = (
        str(profile_defaults.get("target_language", "")).strip().lower()
        or str(FRAMEWORK_DEFAULTS["target_language"])
    )
    unsafe_ratio_max = _coerce_float(
        profile_defaults.get("unsafe_ratio_max", FRAMEWORK_DEFAULTS["unsafe_ratio_max"]),
        float(FRAMEWORK_DEFAULTS["unsafe_ratio_max"]),
    )

    return {
        "selected_readme_path": str(source_readme) if source_readme else "",
        "fallback_readme_path": str(fallback_readme) if fallback_readme else "",
        "source_project_name": source_project_name,
        "source_language": source_language,
        "target_language": target_language,
        "output_project_name": output_project_name,
        "source_dirs": source_dirs,
        "test_dirs": test_dirs,
        "build_commands": build_commands,
        "unsafe_ratio_max": unsafe_ratio_max,
        "api_name_hints": api_name_hints,
        "module_hints": module_hints,
    }


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
    fallback_readme_path: Optional[Path]
    project_root: Optional[Path]
    source_dirs: List[Path]
    test_dirs: List[Path]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "readme_path": str(self.readme_path) if self.readme_path else "",
            "fallback_readme_path": str(self.fallback_readme_path) if self.fallback_readme_path else "",
            "project_root": str(self.project_root) if self.project_root else "",
            "source_dirs": [str(path) for path in self.source_dirs],
            "test_dirs": [str(path) for path in self.test_dirs],
        }


@dataclass
class AgentTaskPacket:
    paths: RuntimePaths
    config: Dict[str, Any]
    profile: Dict[str, Any]
    readme_candidates: List[str]
    max_repair_rounds: int
    source_project_name: str
    source_language: str
    target_language: str
    output_project_name: str
    output_project_dir: Path
    source_dirs: List[str]
    test_dirs: List[str]
    build_commands: List[str]
    unsafe_ratio_max: float
    api_name_hints: List[str]
    module_hints: List[str]
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
        required = [
            "project_layout",
            "trace_artifacts",
            "cargo_build",
            "cargo_test",
            "unsafe",
            "semantic",
            "test_mapping",
            "repair_loop",
        ]
        return not self.issues and all(self.gates.get(name) and self.gates[name].passed for name in required)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "paths": self.paths.to_dict(),
            "source_layout": self.source_layout.to_dict() if self.source_layout else {},
            "readme_candidates": self.readme_candidates,
            "max_repair_rounds": self.max_repair_rounds,
            "source_project_name": self.source_project_name,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "output_project_name": self.output_project_name,
            "output_project_dir": str(self.output_project_dir),
            "source_dirs": self.source_dirs,
            "test_dirs": self.test_dirs,
            "build_commands": self.build_commands,
            "unsafe_ratio_max": self.unsafe_ratio_max,
            "api_name_hints": self.api_name_hints,
            "module_hints": self.module_hints,
            "issues": self.issues,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "gates": {name: gate.to_dict() for name, gate in self.gates.items()},
        }
