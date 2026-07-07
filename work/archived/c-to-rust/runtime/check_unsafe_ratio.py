#!/usr/bin/env python3
"""Check unsafe usage ratio for generated Rust project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def iter_rust_files(root: Path):
    for path in root.rglob("*.rs"):
        if "target" in path.parts:
            continue
        yield path


def count_unsafe(project_dir: Path) -> dict:
    """Return raw unsafe-usage counts and per-file breakdown.  No pass/fail judgment."""
    total_lines = 0
    unsafe_lines = 0
    files = []

    for rust_file in iter_rust_files(project_dir):
        file_total = 0
        file_unsafe = 0
        for line in rust_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue
            file_total += 1
            if "unsafe" in stripped and "unsafe_code" not in stripped:
                file_unsafe += 1
        total_lines += file_total
        unsafe_lines += file_unsafe
        files.append({
            "file": str(rust_file),
            "code_lines": file_total,
            "unsafe_lines": file_unsafe,
        })

    ratio = (unsafe_lines / total_lines) if total_lines else 0.0
    return {
        "total_files": len(files),
        "unsafe_lines": unsafe_lines,
        "total_code_lines": total_lines,
        "ratio": ratio,
        "per_file": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", help="Rust project path")
    parser.add_argument("--output", default="logs/trace/c-to-rust/unsafe-ratio.json")
    args = parser.parse_args()

    project = Path(args.project)
    report = count_unsafe(project)
    report["project"] = str(project)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
