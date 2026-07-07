from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.common import FORBIDDEN_REQUIRED_TERMS  # noqa: E402


CORE_FILES = [
    ROOT / "core" / "design_model.py",
    ROOT / "core" / "implementation_model.py",
    ROOT / "core" / "traceability_model.py",
    ROOT / "core" / "drift_taxonomy.py",
    ROOT / "core" / "severity_policy.py",
    ROOT / "core" / "report_model.py",
]


def main() -> int:
    violations = []
    for path in CORE_FILES:
        text = path.read_text(encoding="utf-8")
        for term in FORBIDDEN_REQUIRED_TERMS:
            token = f'kind="{term}"'
            if token in text:
                violations.append(f"{path.name}:{token}")
    if violations:
        print("adapter-neutrality violations detected:")
        for violation in violations:
            print(violation)
        return 1
    print("adapter-neutrality contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
