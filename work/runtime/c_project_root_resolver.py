"""Resolve an evaluator input path to one unambiguous C project layout."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


README_NAMES = ("README.md", "README", "READNE.md", "READNE", "readme.md", "Readme.md")
SOURCE_NAMES = ("src", "source")
TEST_NAMES = ("tests", "test")
EXCLUDED_NAMES = {"runtime", "scripts", "skills", "result", "logs", "output"}
PATH_RE = re.compile(r"`([^`]+)`|(?<![A-Za-z0-9_./-])([A-Za-z0-9_.-]+(?:[/\\][A-Za-z0-9_.-]+)+)")
SOURCE_LINE_RE = re.compile(r"(?im)^\s*(?:source(?:_dirs?|\s+dirs?|\s+directories?)|源码目录)\s*[:：]\s*(.+)$")
TEST_LINE_RE = re.compile(r"(?im)^\s*(?:tests?(?:_dirs?|\s+dirs?|\s+directories?)|测试目录)\s*[:：]\s*(.+)$")
PUBLIC_DECL_RE = re.compile(
    r"(?m)^\s*(?!static\b)(?:extern\s+)?[A-Za-z_][\w\s*]*\s+[A-Za-z_]\w*\s*\([^;{}]*\)\s*;"
)


def _files(root: Path, suffixes: Iterable[str]) -> List[Path]:
    wanted = {item.lower() for item in suffixes}
    if not root.is_dir():
        return []
    return [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in wanted]


def _readme(root: Path) -> Optional[Path]:
    return next((root / name for name in README_NAMES if (root / name).is_file()), None)


def _path_hints(readmes: Iterable[Path]) -> tuple[List[str], List[str]]:
    source_hints: List[str] = []
    test_hints: List[str] = []
    for readme in readmes:
        text = readme.read_text(encoding="utf-8", errors="ignore")
        for pattern, target in ((SOURCE_LINE_RE, source_hints), (TEST_LINE_RE, test_hints)):
            for value in pattern.findall(text):
                for token in re.split(r"[,\s]+", value):
                    normalized = token.strip("` ./").replace("\\", "/")
                    if normalized and normalized not in target:
                        target.append(normalized)
        for quoted, bare in PATH_RE.findall(text):
            value = (quoted or bare).replace("\\", "/").strip(" ./")
            parts = [part for part in value.split("/") if part and part != "SOURCE_ROOT"]
            if not parts:
                continue
            lowered = [part.lower() for part in parts]
            target = test_hints if any(part in TEST_NAMES for part in lowered) else source_hints
            if any(part in SOURCE_NAMES + TEST_NAMES for part in lowered):
                normalized = "/".join(parts)
                if normalized not in target:
                    target.append(normalized)
    return source_hints, test_hints


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


def _score_candidate(root: Path, inherited_readmes: List[Path]) -> Dict[str, Any]:
    own_readme = _readme(root)
    readmes = ([own_readme] if own_readme else []) + inherited_readmes
    source_hints, test_hints = _path_hints(readmes)
    source_dirs = _resolve_dirs(root, source_hints, SOURCE_NAMES, (".c", ".h"))
    test_dirs = _resolve_dirs(root, test_hints, TEST_NAMES, (".c",))
    source_files = [path for directory in source_dirs for path in _files(directory, (".c", ".h"))]
    test_files = [path for directory in test_dirs for path in _files(directory, (".c",))]
    headers = [path for path in source_files if path.suffix.lower() == ".h"]
    public_api = any(PUBLIC_DECL_RE.search(path.read_text(encoding="utf-8", errors="ignore")) for path in headers)
    score = 0
    score += 5 if own_readme else 0
    score += 5 if (root / "src").is_dir() else 0
    score += 5 if (root / "tests").is_dir() else 0
    score += 5 if source_files else 0
    score += 3 if test_files else 0
    score += 3 if public_api else 0
    score -= 10 if own_readme and not source_files else 0
    score -= 10 if root.name.lower() in EXCLUDED_NAMES else 0
    return {
        "root": str(root),
        "score": score,
        "readme": str(own_readme) if own_readme else "",
        "source_dirs": [str(path) for path in source_dirs],
        "test_dirs": [str(path) for path in test_dirs],
        "usable": bool(source_files and test_files),
        "public_api_declarations": public_api,
    }


def resolve_c_project_root(input_root: Path, max_depth: int = 3) -> Dict[str, Any]:
    input_root = input_root.resolve()
    input_readme = _readme(input_root)
    inherited = [input_readme] if input_readme else []
    candidates = [_score_candidate(root, inherited if root != input_root else []) for root in _candidate_dirs(input_root, max_depth)]
    viable = [item for item in candidates if item["usable"]]
    best_score = max((item["score"] for item in viable), default=None)
    winners = [item for item in viable if item["score"] == best_score]
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
        "selected_readme_path": (winner["readme"] or (str(input_readme) if input_readme else "")) if winner else "",
        "source_dirs": winner["source_dirs"] if winner else [],
        "test_dirs": winner["test_dirs"] if winner else [],
        "candidate_roots": candidates,
        "resolution_strategy": f"bounded scan max_depth={max_depth}; require one highest-scoring usable candidate",
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
        f"- selected_readme_path: `{payload['selected_readme_path'] or 'none'}`",
        f"- source_dirs: `{', '.join(payload['source_dirs']) or 'none'}`",
        f"- test_dirs: `{', '.join(payload['test_dirs']) or 'none'}`",
        f"- resolution_strategy: `{payload['resolution_strategy']}`",
        f"- reason: `{payload['reason']}`", "", "## Candidates", "",
        "| Root | Score | Usable |", "|---|---:|---|",
    ]
    lines.extend(f"| {item['root']} | {item['score']} | {item['usable']} |" for item in payload["candidate_roots"])
    (trace_dir / "00-input-layout-resolution.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
