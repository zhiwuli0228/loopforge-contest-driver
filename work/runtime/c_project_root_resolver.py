"""Resolve an evaluator input path to one unambiguous C project layout."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


SOURCE_NAMES = ("src", "source")
TEST_NAMES = ("tests", "test", "testing", "checks")
EXCLUDED_NAMES = {"runtime", "scripts", "skills", "result", "logs", "output"}
DISCOVERY_EXCLUDED_NAMES = EXCLUDED_NAMES | {".git", ".github", "build", "dist", "target", "out"}
SOURCE_SUFFIXES = (".c", ".h", ".cc", ".cpp", ".cxx", ".hpp")
TEST_SOURCE_SUFFIXES = (".c", ".cc", ".cpp", ".cxx")
BUILD_MANIFESTS = ("CMakeLists.txt", "Makefile", "makefile", "meson.build", "configure.ac", "SConstruct")
import re

PUBLIC_DECL_RE = re.compile(
    r"(?m)^\s*(?!static\b)(?:extern\s+)?[A-Za-z_][\w\s*]*\s+[A-Za-z_]\w*\s*\([^;{}]*\)\s*;"
)


def _files(root: Path, suffixes: Iterable[str]) -> List[Path]:
    wanted = {item.lower() for item in suffixes}
    if not root.is_dir():
        return []
    return [
        path for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in wanted
        and not any(part.lower() in DISCOVERY_EXCLUDED_NAMES for part in path.relative_to(root).parts[:-1])
        and not _crosses_nested_project(path, root)
    ]


def _crosses_nested_project(path: Path, root: Path) -> bool:
    current = path.parent
    while current != root:
        if any((current / name).is_file() for name in BUILD_MANIFESTS):
            return True
        if current.parent == current:
            break
        current = current.parent
    return False


def _candidate_dirs(input_root: Path, max_depth: int) -> List[Path]:
    candidates: List[Path] = []
    if not input_root.is_dir():
        return candidates
    queue = [(input_root.resolve(), 0)]
    while queue:
        current, depth = queue.pop(0)
        candidates.append(current)
        if depth >= max_depth:
            continue
        try:
            children = sorted(path for path in current.iterdir() if path.is_dir() and not path.is_symlink())
        except OSError:
            continue
        queue.extend((child, depth + 1) for child in children)
    return candidates


def _resolve_dirs(root: Path, hints: List[str], defaults: tuple[str, ...], suffixes: tuple[str, ...]) -> List[Path]:
    found: List[Path] = []
    for relative in [*hints, *defaults]:
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            continue
        if candidate.is_dir() and _files(candidate, suffixes) and candidate not in found:
            found.append(candidate)
    return found


def _is_test_file(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    return any(part.lower() in TEST_NAMES for part in relative.parts[:-1]) or relative.name.lower().startswith(("test_", "tests_"))


def _discover_dirs(root: Path, suffixes: tuple[str, ...], tests: bool) -> List[Path]:
    parents: List[Path] = []
    for path in _files(root, suffixes):
        if _is_test_file(path, root) != tests:
            continue
        if path.parent not in parents:
            parents.append(path.parent)
    return parents


def _score_candidate(root: Path, input_root: Path) -> Dict[str, Any]:
    source_dirs = _resolve_dirs(root, [], SOURCE_NAMES, SOURCE_SUFFIXES) or _discover_dirs(root, SOURCE_SUFFIXES, tests=False)
    test_dirs = _resolve_dirs(root, [], TEST_NAMES, TEST_SOURCE_SUFFIXES) or _discover_dirs(root, TEST_SOURCE_SUFFIXES, tests=True)
    source_files = sorted({path for directory in source_dirs for path in _files(directory, SOURCE_SUFFIXES) if not _is_test_file(path, root)})
    test_files = sorted({path for directory in test_dirs for path in _files(directory, TEST_SOURCE_SUFFIXES) if _is_test_file(path, root)})
    translation_units = [path for path in source_files if path.suffix.lower() in TEST_SOURCE_SUFFIXES]
    headers = [path for path in source_files if path.suffix.lower() == ".h"]
    public_api = any(PUBLIC_DECL_RE.search(path.read_text(encoding="utf-8", errors="ignore")) for path in headers)
    score = 0
    score += 6 if any((root / name).is_file() for name in BUILD_MANIFESTS) else 0
    score += 5 if translation_units else 0
    score += 3 if test_files else 0
    score += 3 if public_api else 0
    score += max(0, 4 - min((len(path.relative_to(root).parts) for path in translation_units), default=4))
    score -= 10 if root.name.lower() in EXCLUDED_NAMES else 0
    has_build_manifest = any((root / name).is_file() for name in BUILD_MANIFESTS)
    return {
        "root": str(root),
        "score": score,
        "source_dirs": [str(path) for path in source_dirs],
        "test_dirs": [str(path) for path in test_dirs],
        "usable": bool(translation_units and (root == input_root or test_files or has_build_manifest)),
        "public_api_declarations": public_api,
    }


def resolve_c_project_root(input_root: Path, max_depth: int = 3) -> Dict[str, Any]:
    input_root = input_root.resolve()
    candidates = [_score_candidate(root, input_root) for root in _candidate_dirs(input_root, max_depth)]
    for candidate in candidates:
        candidate_root = Path(candidate["root"])
        viable_descendants = [
            item for item in candidates
            if item["usable"] and Path(item["root"]) != candidate_root and candidate_root in Path(item["root"]).parents
        ]
        if len(viable_descendants) > 1:
            candidate["usable"] = False
            candidate["container_only"] = True
    viable = [item for item in candidates if item["usable"]]
    def rank(item: Dict[str, Any]) -> tuple[int, int]:
        depth = len(Path(item["root"]).relative_to(input_root).parts)
        return item["score"], -depth
    best_rank = max((rank(item) for item in viable), default=None)
    winners = [item for item in viable if rank(item) == best_rank]
    if len(winners) == 1:
        winner = winners[0]
        status = "RESOLVED"
        reason = "unique highest-scoring usable C project root"
    elif len(winners) > 1:
        winner = None
        status = "BLOCKED_WITH_REPORT"
        reason = "ambiguous project roots"
    else:
        winner = None
        status = "BLOCKED_WITH_REPORT"
        reason = "unable to resolve usable C project layout from input_root"
    return {
        "input_root": str(input_root),
        "resolved_project_root": winner["root"] if winner else "",
        "source_dirs": winner["source_dirs"] if winner else [],
        "test_dirs": winner["test_dirs"] if winner else [],
        "candidate_roots": candidates,
        "resolution_strategy": f"bounded scan max_depth={max_depth}; rank by evidence score then proximity; require one winner",
        "status": status,
        "reason": reason,
    }


def write_resolution_trace(payload: Dict[str, Any], trace_dir: Path) -> None:
    trace_dir.mkdir(parents=True, exist_ok=True)
    (trace_dir / "00-input-layout-resolution.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Input Layout Resolution", "",
        f"- status: `{payload['status']}`",
        f"- input_root: `{payload['input_root']}`",
        f"- resolved_project_root: `{payload['resolved_project_root'] or 'unresolved'}`",
        f"- source_dirs: `{', '.join(payload['source_dirs']) or 'none'}`",
        f"- test_dirs: `{', '.join(payload['test_dirs']) or 'none'}`",
        f"- resolution_strategy: `{payload['resolution_strategy']}`",
        f"- reason: `{payload['reason']}`", "", "## Candidates", "",
        "| Root | Score | Usable |", "|---|---:|---|",
    ]
    lines.extend(f"| {item['root']} | {item['score']} | {item['usable']} |" for item in payload["candidate_roots"])
    (trace_dir / "00-input-layout-resolution.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
