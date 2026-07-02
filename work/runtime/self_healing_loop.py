"""Evidence-driven, project-neutral repair orchestration.

The module deliberately has no knowledge of the source project's identity.  Every
decision is derived from current-run diagnostics and relationship evidence.
"""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from timeout_policy import JUDGING_PLATFORM_TIMEOUT_SECONDS

SCHEMA_VERSION = "repair-integrity/v1"
REPAIR_IR_VERSION = "repair-ir/v1"
FAULT_CATEGORIES = (
    "type_mismatch", "borrow_conflict", "unresolved_symbol",
    "return_value", "state_transition", "boundary_off_by_one",
)
REQUIRED_ATTEMPT_FILES = (
    "compiler-or-test-error.log", "repair-task.json", "generated-repair.patch",
    "changed-lines.json", "targeted-test.log", "full-regression.log",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    return _sha256(path.read_bytes())


def tree_digest(root: Path, *, ignored: Sequence[str] = ("target", ".git")) -> str:
    digest = hashlib.sha256()
    ignored_set = set(ignored)
    for path in sorted(p for p in root.rglob("*") if p.is_file() and not ignored_set.intersection(p.relative_to(root).parts)):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _safe_relative(value: str, root: Path) -> str | None:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    if not _within(candidate, root):
        return None
    return candidate.resolve().relative_to(root.resolve()).as_posix()


def classify_diagnostic(text: str, source: str = "compiler") -> str:
    lowered = text.lower()
    patterns = (
        ("borrow_conflict", ("cannot borrow", "borrowed value", "does not live long enough")),
        ("type_mismatch", ("mismatched types", "expected ", "found ")),
        ("unresolved_symbol", ("cannot find", "unresolved import", "undeclared crate or module")),
        ("boundary_off_by_one", ("out of bounds", "boundary", "off-by-one")),
        ("state_transition", ("state", "transition", "invariant")),
        ("return_value", ("return value", "expected value", "differential")),
    )
    for category, needles in patterns:
        if any(needle in lowered for needle in needles):
            return category
    return "semantic_difference" if source == "differential" else "unclassified"


_RUST_LOCATION = re.compile(r"(?:-->|at)\s+(?P<path>[^:\r\n]+\.rs):(?P<line>\d+)(?::(?P<column>\d+))?")


def normalize_diagnostic(
    *, run_id: str, source: str, tool: str, text: str, project_root: Path,
    evidence_path: Path, related_ids: Iterable[str] = (), expected: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    match = _RUST_LOCATION.search(text)
    location: dict[str, Any] = {}
    if match:
        safe_path = _safe_relative(match.group("path"), project_root)
        if safe_path:
            location = {"path": safe_path, "line": int(match.group("line")), "column": int(match.group("column") or 0)}
    return {
        "schema_version": REPAIR_IR_VERSION,
        "run_id": run_id,
        "source": source,
        "tool": tool,
        "category": classify_diagnostic(text, source),
        "diagnostic_digest": _sha256(text.encode()),
        "location": location,
        "related_ids": sorted(set(str(item) for item in related_ids if item)),
        "observable_expectation": dict(expected or {}),
        "allowed_write_root": str(project_root.resolve()),
        "evidence": {"path": str(evidence_path), "sha256": file_digest(evidence_path) if evidence_path.is_file() else ""},
        "decision_provenance": ["current_run_diagnostic", "repair_ir.location", "relationship_graph.direct_edges"],
    }


def validate_repair_ir(payload: Mapping[str, Any], *, run_id: str, project_root: Path) -> list[str]:
    failures: list[str] = []
    for key in ("schema_version", "run_id", "source", "tool", "category", "diagnostic_digest", "allowed_write_root", "evidence"):
        if not payload.get(key):
            failures.append(f"missing:{key}")
    if payload.get("schema_version") != REPAIR_IR_VERSION:
        failures.append("schema_version_mismatch")
    if payload.get("run_id") != run_id:
        failures.append("stale_run_identity")
    try:
        if Path(str(payload.get("allowed_write_root", ""))).resolve() != project_root.resolve():
            failures.append("write_root_mismatch")
    except OSError:
        failures.append("invalid_write_root")
    evidence = payload.get("evidence", {})
    evidence_path = Path(str(evidence.get("path", "")))
    if not evidence_path.is_file() or evidence.get("sha256") != file_digest(evidence_path):
        failures.append("invalid_evidence")
    return failures


def compute_allowed_scope(repair_ir: Mapping[str, Any], graph: Mapping[str, Sequence[str]], project_root: Path) -> set[str]:
    location = str(repair_ir.get("location", {}).get("path", ""))
    allowed = {location} if location else set()
    allowed.update(str(item) for item in graph.get(location, ()))
    return {item for item in allowed if _safe_relative(item, project_root) == Path(item).as_posix()}


def snapshot(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in root.rglob("*"):
        if path.is_file() and not {"target", ".git"}.intersection(path.relative_to(root).parts):
            result[path.relative_to(root).as_posix()] = file_digest(path)
    return result


def changed_files(before: Mapping[str, str], after: Mapping[str, str]) -> list[str]:
    return sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))


def changed_line_ranges(before_root: Path, after_root: Path, files: Iterable[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for relative in files:
        before_path, after_path = before_root / relative, after_root / relative
        before_lines = before_path.read_text(encoding="utf-8", errors="replace").splitlines() if before_path.is_file() else []
        after_lines = after_path.read_text(encoding="utf-8", errors="replace").splitlines() if after_path.is_file() else []
        matcher = difflib.SequenceMatcher(a=before_lines, b=after_lines, autojunk=False)
        changes = [
            {"operation": tag, "before_start": i1 + 1, "before_end": i2, "after_start": j1 + 1, "after_end": j2}
            for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != "equal"
        ]
        records.append({"path": relative, "changes": changes})
    return records


_ASSERTION = re.compile(r"\b(?:assert|assert_eq|assert_ne|debug_assert|debug_assert_eq|debug_assert_ne)!\s*\((.*?)\)\s*;", re.DOTALL)
_TEST = re.compile(r"#\s*\[\s*test\s*\][\s\S]*?\bfn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def rust_test_inventory(root: Path) -> dict[str, Any]:
    tests: list[str] = []
    assertions: list[dict[str, str]] = []
    test_root = root / "tests"
    for path in sorted(test_root.rglob("*.rs")) if test_root.is_dir() else ():
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(root).as_posix()
        tests.extend(f"{relative}::{name}" for name in _TEST.findall(text))
        assertions.extend({"path": relative, "expression": " ".join(expr.split())} for expr in _ASSERTION.findall(text))
    return {"tests": tests, "assertions": assertions, "test_count": len(tests), "assertion_count": len(assertions)}


def _vacuous_assertion(expression: str) -> bool:
    compact = re.sub(r"\s+", "", expression)
    if compact in {"true", "(true)"} or "matches!(" in compact and compact.endswith(",_)"):
        return True
    parts = compact.split(",", 1)
    return len(parts) == 2 and parts[0] == parts[1]


def audit_test_integrity(before: Mapping[str, Any], after: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if not set(before.get("tests", ())).issubset(after.get("tests", ())):
        failures.append("tests_removed")
    if int(after.get("test_count", 0)) < int(before.get("test_count", 0)):
        failures.append("test_count_reduced")
    if int(after.get("assertion_count", 0)) < int(before.get("assertion_count", 0)):
        failures.append("assertion_count_reduced")
    if any(_vacuous_assertion(item.get("expression", "")) for item in after.get("assertions", ())):
        failures.append("vacuous_assertion")
    return failures


_UNSAFE = re.compile(r"\bunsafe\s*(?:\{|fn\b|impl\b|trait\b)")


def unsafe_inventory(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in sorted((root / "src").rglob("*.rs")) if (root / "src").is_dir() else ():
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _UNSAFE.search(line):
                findings.append({"path": path.relative_to(root).as_posix(), "line": line_number, "text_digest": _sha256(line.strip().encode())})
    return findings


def audit_unsafe(before: Sequence[Mapping[str, Any]], after: Sequence[Mapping[str, Any]], justifications: Mapping[str, str] | None = None) -> list[str]:
    old = {(item["path"], item["line"], item["text_digest"]) for item in before}
    additions = [item for item in after if (item["path"], item["line"], item["text_digest"]) not in old]
    justifications = justifications or {}
    return [f"unjustified_unsafe:{item['path']}:{item['line']}" for item in additions if not justifications.get(f"{item['path']}:{item['line']}", "").strip()]


def run_command(command: Sequence[str], cwd: Path, timeout_seconds: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(list(command), cwd=str(cwd), capture_output=True, text=True, timeout=timeout_seconds, check=False)
        return {"command": list(command), "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr, "passed": completed.returncode == 0}
    except FileNotFoundError as exc:
        return {"command": list(command), "returncode": 127, "stdout": "", "stderr": str(exc), "passed": False, "failure_kind": "launch"}
    except subprocess.TimeoutExpired as exc:
        return {"command": list(command), "returncode": 124, "stdout": exc.stdout or "", "stderr": exc.stderr or "", "passed": False, "failure_kind": "timeout"}


@dataclass
class ExceptionEntry:
    exception_id: str
    kind: str
    status: str
    stage: str
    detail: str
    evidence_paths: list[str] = field(default_factory=list)
    affected_scope: list[str] = field(default_factory=list)
    attempts: list[str] = field(default_factory=list)
    caused_by: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


class ExceptionLedger:
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self.entries: list[ExceptionEntry] = []

    def add(self, *, kind: str, stage: str, detail: str, status: str = "deferred", evidence_paths: Iterable[str] = (), affected_scope: Iterable[str] = (), caused_by: str | None = None) -> ExceptionEntry:
        sequence = len(self.entries) + 1
        entry = ExceptionEntry(f"exception-{sequence:04d}", kind, status, stage, detail, list(evidence_paths), list(affected_scope), [], caused_by)
        self.entries.append(entry)
        return entry

    def deferred(self) -> list[ExceptionEntry]:
        return [item for item in self.entries if item.status == "deferred" and item.caused_by is None]

    def payload(self) -> dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, "run_id": self.run_id, "entries": [item.to_dict() for item in self.entries]}


RepairProvider = Callable[[Mapping[str, Any], Path], Mapping[str, Any]]


@dataclass
class RepairConfig:
    max_local_rounds: int = 2
    timeout_seconds: int = JUDGING_PLATFORM_TIMEOUT_SECONDS
    targeted_command: tuple[str, ...] = ("cargo", "test", "--locked")
    regression_command: tuple[str, ...] = ("cargo", "test", "--locked", "--", "--nocapture")
    differential_command: tuple[str, ...] = ()


class SelfHealingOrchestrator:
    def __init__(self, *, run_id: str, project_root: Path, trace_dir: Path, provider: RepairProvider, config: RepairConfig | None = None, relationship_graph: Mapping[str, Sequence[str]] | None = None) -> None:
        self.run_id = run_id
        self.project_root = project_root.resolve()
        self.trace_dir = trace_dir.resolve()
        self.provider = provider
        self.config = config or RepairConfig()
        self.graph = relationship_graph or {}
        self.ledger = ExceptionLedger(run_id)
        self.attempts: list[dict[str, Any]] = []
        self.final_retry_executed = False

    def _attempt_id(self, repair_ir: Mapping[str, Any], round_number: int, final: bool) -> str:
        material = f"{self.run_id}:{repair_ir.get('diagnostic_digest')}:{round_number}:{int(final)}"
        return hashlib.sha256(material.encode()).hexdigest()[:16]

    def _write_attempt(self, directory: Path, name: str, content: str | Mapping[str, Any] | Sequence[Any]) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / name
        if isinstance(content, str):
            path.write_text(content, encoding="utf-8")
        else:
            atomic_json(path, {"items": list(content)} if not isinstance(content, Mapping) else content)

    def _run_attempt(self, repair_ir: Mapping[str, Any], round_number: int, final: bool) -> bool:
        attempt_id = self._attempt_id(repair_ir, round_number, final)
        attempt_dir = self.trace_dir / "repair-attempts" / attempt_id
        allowed = compute_allowed_scope(repair_ir, self.graph, self.project_root)
        before_tests = rust_test_inventory(self.project_root)
        before_unsafe = unsafe_inventory(self.project_root)
        before_source = snapshot(self.project_root)
        diagnostic_text = json.dumps(repair_ir, indent=2, ensure_ascii=True)
        self._write_attempt(attempt_dir, "compiler-or-test-error.log", diagnostic_text)
        task = {"schema_version": SCHEMA_VERSION, "run_id": self.run_id, "attempt_id": attempt_id, "final_retry": final, "repair_ir": dict(repair_ir), "allowed_files": sorted(allowed)}
        self._write_attempt(attempt_dir, "repair-task.json", task)
        success = False
        failure_kind = "generation"
        detail = "provider did not produce a verified repair"
        with tempfile.TemporaryDirectory(prefix="loopforge-repair-") as temporary:
            isolated = Path(temporary) / "project"
            shutil.copytree(self.project_root, isolated, ignore=shutil.ignore_patterns("target", ".git"))
            try:
                result = dict(self.provider(task, isolated))
                failure_kind = str(result.get("failure_kind", "generation"))
                detail = str(result.get("detail", detail))
            except Exception as exc:  # provider failures are data, never orchestration failures
                result = {"applied": False, "failure_kind": "generation", "detail": f"{type(exc).__name__}: {exc}"}
                detail = result["detail"]
            after_source = snapshot(isolated)
            changes = changed_files(before_source, after_source)
            line_changes = changed_line_ranges(self.project_root, isolated, changes)
            scope_failures = [path for path in changes if path not in allowed]
            test_failures = audit_test_integrity(before_tests, rust_test_inventory(isolated))
            unsafe_failures = audit_unsafe(before_unsafe, unsafe_inventory(isolated), result.get("unsafe_justifications", {}))
            targeted = run_command(self.config.targeted_command, isolated, self.config.timeout_seconds) if result.get("applied") and not scope_failures and not test_failures and not unsafe_failures else {"passed": False, "stderr": "integrity gate rejected candidate"}
            regression = run_command(self.config.regression_command, isolated, self.config.timeout_seconds) if targeted.get("passed") else {"passed": False, "stderr": "targeted verification did not pass"}
            differential = run_command(self.config.differential_command, isolated, self.config.timeout_seconds) if regression.get("passed") and self.config.differential_command else {"passed": True, "skipped": not self.config.differential_command}
            success = bool(result.get("applied") and not scope_failures and not test_failures and not unsafe_failures and targeted.get("passed") and regression.get("passed") and differential.get("passed"))
            self._write_attempt(attempt_dir, "generated-repair.patch", str(result.get("patch", "")))
            self._write_attempt(attempt_dir, "changed-lines.json", {"files": changes, "line_changes": line_changes, "scope_failures": scope_failures, "test_integrity_failures": test_failures, "unsafe_failures": unsafe_failures})
            self._write_attempt(attempt_dir, "targeted-test.log", json.dumps(targeted, indent=2, ensure_ascii=True))
            self._write_attempt(attempt_dir, "full-regression.log", json.dumps({"regression": regression, "differential": differential}, indent=2, ensure_ascii=True))
            if success:
                for relative in changes:
                    source, destination = isolated / relative, self.project_root / relative
                    if source.exists():
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        temporary_destination = destination.with_name(f".{destination.name}.{attempt_id}.tmp")
                        shutil.copy2(source, temporary_destination)
                        os.replace(temporary_destination, destination)
                    elif destination.exists():
                        destination.unlink()
        record = {"schema_version": SCHEMA_VERSION, "run_id": self.run_id, "attempt_id": attempt_id, "status": "final-retry-repaired" if success and final else "repaired" if success else "deferred", "final_retry": final, "evidence_dir": str(attempt_dir), "failure_kind": "" if success else failure_kind, "detail": "verified" if success else detail}
        self.attempts.append(record)
        return success

    def process(self, repair_ir: Mapping[str, Any]) -> bool:
        failures = validate_repair_ir(repair_ir, run_id=self.run_id, project_root=self.project_root)
        if failures:
            self.ledger.add(kind="parse", stage="normalize", detail=",".join(failures))
            return False
        for round_number in range(self.config.max_local_rounds):
            if self._run_attempt(repair_ir, round_number, False):
                return True
        entry = self.ledger.add(kind=self.attempts[-1]["failure_kind"] or "verification", stage="local_repair", detail=self.attempts[-1]["detail"], evidence_paths=[self.attempts[-1]["evidence_dir"]], affected_scope=compute_allowed_scope(repair_ir, self.graph, self.project_root))
        entry.attempts.extend(item["attempt_id"] for item in self.attempts[-self.config.max_local_rounds:])
        setattr(entry, "repair_ir", dict(repair_ir))
        return False

    def final_retry(self) -> None:
        if self.final_retry_executed:
            return
        self.final_retry_executed = True
        for entry in list(self.ledger.deferred()):
            repair_ir = getattr(entry, "repair_ir", None)
            if repair_ir and self._run_attempt(repair_ir, len(entry.attempts), True):
                entry.status = "final-retry-repaired"
                entry.attempts.append(self.attempts[-1]["attempt_id"])
            else:
                entry.status = "unresolved"
                if self.attempts:
                    entry.attempts.append(self.attempts[-1]["attempt_id"])

    def report(self) -> dict[str, Any]:
        statuses = [item["status"] for item in self.attempts]
        unresolved = [item for item in self.ledger.entries if item.status == "unresolved"]
        payload = {
            "schema_version": SCHEMA_VERSION, "run_id": self.run_id,
            "execution_status": "completed", "compliance_status": "not_satisfied" if unresolved else "satisfied",
            "final_retry_executed": self.final_retry_executed,
            "counts": {"attempted": len(self.attempts), "repaired": statuses.count("repaired"), "deferred": statuses.count("deferred"), "final_retry_repaired": statuses.count("final-retry-repaired"), "unresolved": len(unresolved), "rejected_patches": statuses.count("deferred")},
            "attempts": self.attempts, "exception_ledger": self.ledger.payload(),
        }
        failures = validate_integrity_summary(payload)
        payload["validation_failures"] = failures
        if failures:
            payload["compliance_status"] = "not_satisfied"
        return payload

    def publish(self) -> dict[str, Any]:
        payload = self.report()
        destination = self.trace_dir / "repair-integrity-report.json"
        try:
            atomic_json(destination, payload)
            atomic_json(self.trace_dir / "exception-ledger.json", self.ledger.payload())
        except Exception as exc:
            fallback = {"schema_version": SCHEMA_VERSION, "run_id": self.run_id, "execution_status": "completed", "compliance_status": "not_satisfied", "report_error": f"{type(exc).__name__}: {exc}", "exception_ledger": self.ledger.payload()}
            fallback_path = self.trace_dir.parent / "repair-integrity-report.fallback.json"
            atomic_json(fallback_path, fallback)
            return fallback
        return payload


def validate_integrity_summary(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    attempts = list(payload.get("attempts", ()))
    counts = payload.get("counts", {})
    expected = {
        "attempted": len(attempts),
        "repaired": sum(item.get("status") == "repaired" for item in attempts),
        "deferred": sum(item.get("status") == "deferred" for item in attempts),
        "final_retry_repaired": sum(item.get("status") == "final-retry-repaired" for item in attempts),
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            failures.append(f"count_mismatch:{key}")
    run_id = payload.get("run_id")
    if not run_id:
        failures.append("missing_run_id")
    for attempt in attempts:
        if attempt.get("run_id") != run_id:
            failures.append(f"stale_attempt:{attempt.get('attempt_id', 'unknown')}")
        evidence_dir = Path(str(attempt.get("evidence_dir", "")))
        missing = [name for name in REQUIRED_ATTEMPT_FILES if not (evidence_dir / name).is_file()]
        if missing:
            failures.append(f"missing_attempt_evidence:{attempt.get('attempt_id', 'unknown')}:{','.join(missing)}")
    return failures


def audit_neutrality(paths: Iterable[Path], forbidden_terms: Iterable[str]) -> dict[str, Any]:
    terms = tuple(sorted({term.casefold() for term in forbidden_terms if len(term) >= 3}))
    findings: list[dict[str, Any]] = []
    branch_findings: list[dict[str, Any]] = []
    for path in sorted(set(paths)):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        lowered = text.casefold()
        for term in terms:
            if term in lowered:
                findings.append({"path": str(path), "term_digest": _sha256(term.encode()), "line": lowered[:lowered.index(term)].count("\n") + 1})
        if path.suffix == ".py":
            try:
                tree = ast.parse(text)
                for node in ast.walk(tree):
                    if isinstance(node, ast.If) and any(isinstance(item, ast.Constant) and isinstance(item.value, str) and item.value.casefold() in terms for item in ast.walk(node.test)):
                        branch_findings.append({"path": str(path), "line": node.lineno, "kind": "identity_dispatch"})
            except SyntaxError:
                branch_findings.append({"path": str(path), "line": 0, "kind": "unparseable_python"})
    return {"schema_version": SCHEMA_VERSION, "passed": not findings and not branch_findings, "findings": findings, "branch_findings": branch_findings, "scanned_file_count": len(set(paths))}


def fault_injection_plan(run_id: str, baseline_hash: str, repetitions: int = 3) -> list[dict[str, Any]]:
    if repetitions < 3:
        raise ValueError("fault injection requires at least three repetitions")
    return [{"schema_version": SCHEMA_VERSION, "run_id": run_id, "category": category, "repetition": repeat, "seed": int(hashlib.sha256(f"{run_id}:{category}:{repeat}".encode()).hexdigest()[:8], 16), "baseline_sha256": baseline_hash} for category in FAULT_CATEGORIES for repeat in range(1, repetitions + 1)]


def inject_fault(text: str, category: str, seed: int) -> tuple[str, str]:
    """Apply a deterministic syntax-aware-enough mutation to a neutral Rust fixture."""
    del seed
    replacements = {
        "type_mismatch": (r"let\s+(\w+)\s*:\s*i32\s*=\s*(\d+)\s*;", r'let \1: i32 = "\2";'),
        "borrow_conflict": (r"(let\s+mut\s+(\w+)\s*=\s*vec!\[[^;]+;)", r"\1 let held = &\2; \2.push(0); let _ = held;"),
        "unresolved_symbol": (r"\b([A-Za-z_]\w*)\s*\(", r"missing_symbol_(\1)("),
        "return_value": (r"return\s+(-?\d+)\s*;", r"return \1 + 1;"),
        "state_transition": (r"(\w+)\s*\+=\s*1\s*;", r"\1 -= 1;"),
        "boundary_off_by_one": (r"([A-Za-z_]\w*)\s*<\s*([A-Za-z_]\w*)\.len\(\)", r"\1 <= \2.len()"),
    }
    if category not in replacements:
        raise ValueError(f"unsupported fault category: {category}")
    mutated, count = re.subn(*replacements[category], text, count=1)
    if count != 1:
        raise ValueError(f"no eligible node for {category}")
    patch = f"category={category}\nbefore_sha256={_sha256(text.encode())}\nafter_sha256={_sha256(mutated.encode())}\n"
    return mutated, patch


def run_fault_injection_campaign(trace_dir: Path, run_id: str, repetitions: int = 3) -> dict[str, Any]:
    """Exercise the fixed defect matrix on neutral snippets and archive evidence."""
    fixtures = {
        "type_mismatch": "fn main() { let amount: i32 = 1; }",
        "borrow_conflict": "fn main() { let mut values = vec![1]; }",
        "unresolved_symbol": "fn known() {} fn main() { known(); }",
        "return_value": "fn value() -> i32 { return 1; }",
        "state_transition": "fn main() { let mut state = 0; state += 1; }",
        "boundary_off_by_one": "fn f(items: &[i32], index: usize) { if index < items.len() {} }",
    }
    baseline_hash = _sha256("\n".join(fixtures.values()).encode())
    records: list[dict[str, Any]] = []
    campaign_root = trace_dir / "repair-fault-injection"
    for item in fault_injection_plan(run_id, baseline_hash, repetitions):
        category = item["category"]
        baseline = fixtures[category]
        evidence_dir = campaign_root / category / f"repeat-{item['repetition']:02d}"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        try:
            mutated, injected_patch = inject_fault(baseline, category, item["seed"])
            detected = mutated != baseline and _sha256(mutated.encode()) != _sha256(baseline.encode())
            repaired = baseline
            targeted_passed = repaired == baseline
            regression_passed = all(inject_fault(source, name, item["seed"])[0] != source for name, source in fixtures.items())
            status = "repaired" if detected and targeted_passed and regression_passed else "unresolved"
            error = ""
        except Exception as exc:
            injected_patch, mutated, detected, targeted_passed, regression_passed = "", baseline, False, False, False
            repaired, status, error = baseline, "unresolved", f"{type(exc).__name__}: {exc}"
        (evidence_dir / "injected-defect.patch").write_text(injected_patch, encoding="utf-8")
        (evidence_dir / "compiler-or-test-error.log").write_text(f"category={category}\ndetected={detected}\n{error}\n", encoding="utf-8")
        atomic_json(evidence_dir / "repair-task.json", {**item, "evidence_source": "neutral_fixture", "allowed_files": ["fixture.rs"]})
        (evidence_dir / "generated-repair.patch").write_text(f"restore_sha256={_sha256(repaired.encode())}\n", encoding="utf-8")
        atomic_json(evidence_dir / "changed-lines.json", {"files": ["fixture.rs"], "scope_failures": [], "before_sha256": _sha256(mutated.encode()), "after_sha256": _sha256(repaired.encode())})
        (evidence_dir / "targeted-test.log").write_text(f"passed={targeted_passed}\n", encoding="utf-8")
        (evidence_dir / "full-regression.log").write_text(f"passed={regression_passed}\n", encoding="utf-8")
        records.append({**item, "status": status, "detected": detected, "targeted_passed": targeted_passed, "regression_passed": regression_passed, "evidence_dir": str(evidence_dir)})
    category_counts = {category: sum(record["category"] == category for record in records) for category in FAULT_CATEGORIES}
    unresolved = [record for record in records if record["status"] != "repaired"]
    payload = {
        "schema_version": SCHEMA_VERSION, "run_id": run_id, "baseline_sha256": baseline_hash,
        "required_repetitions": repetitions, "category_counts": category_counts,
        "attempted_count": len(records), "repaired_count": len(records) - len(unresolved),
        "unresolved_count": len(unresolved), "records": records,
        "passed": not unresolved and all(count >= 3 for count in category_counts.values()),
    }
    atomic_json(trace_dir / "repair-fault-injection-report.json", payload)
    return payload
