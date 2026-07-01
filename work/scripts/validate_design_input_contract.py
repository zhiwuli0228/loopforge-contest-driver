#!/usr/bin/env python3
"""Validate the preloaded-design contract and a package-shaped execution."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


FORBIDDEN = ("work/code/README", "SOURCE_ROOT/README", "source-readme")
PRODUCTION_AREAS = (
    "work/runtime",
    "work/rules",
    "work/skills",
    "work/subagent",
    "work/profiles",
)
TEXT_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".json"}


def digest_tree(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def forbidden_references(workspace: Path) -> list[str]:
    failures: list[str] = []
    for relative in PRODUCTION_AREAS:
        for path in (workspace / relative).rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES or "tests" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for token in FORBIDDEN:
                if token.lower() in text.lower():
                    failures.append(f"{path.relative_to(workspace)}: forbidden token {token}")
    return failures


def package_check(workspace: Path) -> list[str]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="loopforge-package-") as tmp:
        package = Path(tmp) / "submission"
        ignore = shutil.ignore_patterns("code", "output", "logs", "result", "__pycache__", "*.pyc")
        shutil.copytree(workspace / "work", package / "work", ignore=ignore)
        for name in ("README.md", "INSTRUCTION.md"):
            shutil.copy2(workspace / name, package / name)

        source = Path(tmp) / "injected-source"
        (source / "src").mkdir(parents=True)
        (source / "tests").mkdir()
        (source / "src" / "demo.h").write_text("int demo(void);\n", encoding="utf-8")
        (source / "src" / "demo.c").write_text("int demo(void) { return 1; }\n", encoding="utf-8")
        (source / "tests" / "test_demo.c").write_text("int main(void) { return demo() != 1; }\n", encoding="utf-8")
        before = digest_tree(source)

        command = [
            sys.executable,
            str(package / "work" / "runtime" / "loopforge_runner.py"),
            "--source-root",
            str(source),
            "--self-check",
        ]
        completed = subprocess.run(command, cwd=package, capture_output=True, text=True, timeout=60, check=False)
        if completed.returncode != 0:
            failures.append(f"package self-check exited {completed.returncode}: {completed.stderr or completed.stdout}")
        else:
            try:
                payload = json.loads(completed.stdout)
            except json.JSONDecodeError as exc:
                failures.append(f"package self-check emitted invalid JSON: {exc}")
            else:
                if not payload.get("ok"):
                    failures.append(f"package self-check blocked: {payload.get('issues', [])}")
                if len(str(payload.get("design_readme_sha256", ""))) != 64:
                    failures.append("package self-check did not record a design SHA-256 digest")
        if (package / "work" / "code").exists():
            failures.append("package unexpectedly contains work/code")
        if digest_tree(source) != before:
            failures.append("package self-check mutated SOURCE_ROOT")
    return failures


def main() -> int:
    workspace = Path(__file__).resolve().parents[2]
    design = workspace / "work" / "design" / "README.md"
    failures = []
    if not design.is_file() or not design.read_text(encoding="utf-8", errors="ignore").strip():
        failures.append("work/design/README.md is missing or empty")
    failures.extend(forbidden_references(workspace))
    failures.extend(package_check(workspace))
    if failures:
        print("\n".join(f"FAIL: {item}" for item in failures))
        return 1
    print("preloaded design input contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
