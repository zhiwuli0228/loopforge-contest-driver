"""Project-neutral, non-failing Linux submission acceptance primitives."""

from __future__ import annotations

import hashlib
import ast
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from timeout_policy import JUDGING_PLATFORM_TIMEOUT_SECONDS


SCHEMA_VERSION = "1.0"
FINAL_RETRY_LIMIT = 1
NORMALIZED_FIELDS = frozenset({"run_id", "created_at", "temporary_root"})
SUBMISSION_SUFFIXES = frozenset({".py", ".sh", ".ps1", ".md", ".yaml", ".yml", ".json", ".toml"})
ASSET_KINDS = frozenset({"code", "scripts", "rules", "skills", "prompts", "config", "templates", "fixtures", "tests", "paths"})
SCHEMAS: dict[str, dict[str, Any]] = {
    "linux-run-manifest": {"required": ["schema_version", "run_id", "source_root", "workspace", "created_at"]},
    "stage-outcome": {"required": ["schema_version", "run_id", "stage", "status", "inputs", "outputs", "writable_roots", "timeout_seconds"]},
    "exception-ledger": {"required": ["schema_version", "run_id", "entries"]},
    "customization-audit": {"required": ["schema_version", "run_id", "manifest", "findings", "status"]},
    "repeatability": {"required": ["schema_version", "left_run_id", "right_run_id", "differences", "status"]},
    "final-verification": {"required": ["schema_version", "run_id", "execution_status", "compliance_status", "checks", "exceptions"]},
}
PIPELINE_BLUEPRINT: tuple[dict[str, Any], ...] = (
    {"name": "source-analysis", "dependencies": (), "inputs": ("SOURCE_ROOT",), "outputs": ("source-inventory.json",)},
    {"name": "semantic-planning", "dependencies": ("source-analysis",), "inputs": ("source-inventory.json",), "outputs": ("migration-plan.json",)},
    {"name": "rust-generation", "dependencies": ("semantic-planning",), "inputs": ("migration-plan.json",), "outputs": ("implementation-map.json",)},
    {"name": "test-migration", "dependencies": ("rust-generation",), "inputs": ("implementation-map.json",), "outputs": ("source-test-map.json",)},
    {"name": "differential-validation", "dependencies": ("test-migration",), "inputs": ("source-test-map.json",), "outputs": ("differential-test-report.json",)},
    {"name": "repair", "dependencies": ("rust-generation",), "inputs": ("implementation-map.json",), "outputs": ("repair-integrity-report.json",)},
    {"name": "cargo-build", "dependencies": ("rust-generation",), "inputs": ("Cargo.lock",), "outputs": ("cargo-build.log",)},
    {"name": "cargo-test", "dependencies": ("cargo-build", "test-migration"), "inputs": ("Cargo.lock",), "outputs": ("cargo-test.log",)},
    {"name": "unsafe-audit", "dependencies": ("rust-generation",), "inputs": ("implementation-map.json",), "outputs": ("unsafe-ratio.json",)},
    {"name": "acceptance", "dependencies": ("differential-validation", "repair", "cargo-test", "unsafe-audit"), "inputs": ("current-run-evidence",), "outputs": ("final-verification.json",)},
)


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def validate_schema(name: str, payload: Mapping[str, Any]) -> list[str]:
    schema = SCHEMAS[name]
    return [f"missing:{key}" for key in schema["required"] if key not in payload]


@dataclass(frozen=True)
class AcceptanceWorkspace:
    run_id: str
    root: Path
    output: Path
    logs: Path
    result: Path
    temporary: Path
    cargo_target: Path

    @classmethod
    def create(cls, base: Path, source_root: Path, run_id: str | None = None) -> "AcceptanceWorkspace":
        run_id = run_id or f"linux-{uuid.uuid4().hex}"
        root = base.resolve() / run_id
        if root.exists():
            raise ValueError(f"run workspace already exists: {root}")
        paths = [root / name for name in ("output", "logs", "result", "temporary", "cargo-target")]
        for path in paths:
            path.mkdir(parents=True, exist_ok=False)
        resolved_source = source_root.resolve()
        if root == resolved_source or root in resolved_source.parents or resolved_source in root.parents:
            raise ValueError("acceptance workspace and source_root must not overlap")
        return cls(run_id, root, *paths)

    def manifest(self, source_root: Path, submission_root: Path) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "source_root": str(source_root.resolve()),
            "workspace": str(self.root),
            "temporary_root": str(self.temporary),
            "created_at": now(),
            "writable_roots": [str(item) for item in (self.output, self.logs, self.result, self.temporary, self.cargo_target)],
            "source_mode": "read-only-contract",
            "submission_digest": tree_digest(submission_root),
        }


def assert_clean_workspace(workspace: AcceptanceWorkspace) -> list[str]:
    findings: list[str] = []
    for root in (workspace.output, workspace.logs, workspace.result, workspace.temporary, workspace.cargo_target):
        if any(root.iterdir()):
            findings.append(f"stale-artifact:{root.name}")
    return findings


def environment_evidence(run_id: str, submission_root: Path) -> dict[str, Any]:
    def version(command: Sequence[str]) -> str:
        try:
            result = subprocess.run(command, text=True, capture_output=True, timeout=10, check=False)
            return (result.stdout or result.stderr).strip().splitlines()[0]
        except (OSError, subprocess.TimeoutExpired, IndexError):
            return "unavailable"
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "kernel": platform.release(),
        "system": platform.system(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "rustc": version(["rustc", "--version"]),
        "cargo": version(["cargo", "--version"]),
        "locale": os.environ.get("LC_ALL") or os.environ.get("LANG", ""),
        "timezone": os.environ.get("TZ", "system"),
        "environment": {key: os.environ[key] for key in sorted(os.environ) if key in {"CI", "LANG", "LC_ALL", "TZ"}},
        "submission_digest": tree_digest(submission_root),
    }


def path_manifest(root: Path) -> dict[str, dict[str, Any]]:
    root = root.resolve()
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        info = path.lstat()
        item: dict[str, Any] = {"mode": stat.S_IMODE(info.st_mode), "type": "other"}
        if path.is_symlink():
            item.update(type="symlink", target=os.readlink(path))
        elif path.is_file():
            item.update(type="file", size=info.st_size, sha256=digest_file(path))
        elif path.is_dir():
            item["type"] = "directory"
        result[relative] = item
    return result


def tree_digest(root: Path) -> str:
    payload = json.dumps(path_manifest(root), sort_keys=True, separators=(",", ":")).encode()
    return digest_bytes(payload)


def compare_manifests(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
    before_keys, after_keys = set(before), set(after)
    changed = sorted(key for key in before_keys & after_keys if before[key] != after[key])
    return {
        "added": sorted(after_keys - before_keys),
        "removed": sorted(before_keys - after_keys),
        "changed": changed,
        "status": "passed" if before == after else "failed",
    }


def publish_source_integrity(trace: Path, run_id: str, before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
    trace.mkdir(parents=True, exist_ok=True)
    before_digest = digest_bytes(json.dumps(before, sort_keys=True).encode())
    after_digest = digest_bytes(json.dumps(after, sort_keys=True).encode())
    (trace / "source-before.sha256").write_text(before_digest + "\n", encoding="utf-8")
    (trace / "source-after.sha256").write_text(after_digest + "\n", encoding="utf-8")
    report = {"schema_version": SCHEMA_VERSION, "run_id": run_id, **compare_manifests(before, after)}
    atomic_json(trace / "source-integrity.json", report)
    return report


@dataclass
class ExceptionRecord:
    exception_id: str
    stage: str
    kind: str
    detail: str
    status: str = "deferred"
    caused_by: str = ""
    attempts: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


class AcceptanceLedger:
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self.entries: list[ExceptionRecord] = []

    def add(self, stage: str, kind: str, detail: str, *, status: str = "deferred", caused_by: str = "", evidence: Iterable[str] = ()) -> ExceptionRecord:
        record = ExceptionRecord(f"acceptance-{len(self.entries) + 1:04d}", stage, kind, detail, status, caused_by, [], list(evidence))
        self.entries.append(record)
        return record

    def payload(self) -> dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, "run_id": self.run_id, "entries": [asdict(item) for item in self.entries]}


@dataclass(frozen=True)
class Stage:
    name: str
    action: Callable[[], Any]
    dependencies: tuple[str, ...] = ()
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    writable_roots: tuple[str, ...] = ()
    timeout_seconds: int = JUDGING_PLATFORM_TIMEOUT_SECONDS


class StageDag:
    def __init__(self, run_id: str, ledger: AcceptanceLedger) -> None:
        self.run_id, self.ledger = run_id, ledger
        self.stages: list[Stage] = []
        self.outcomes: dict[str, dict[str, Any]] = {}

    def add(self, stage: Stage) -> None:
        if stage.name in {item.name for item in self.stages}:
            raise ValueError(f"duplicate stage: {stage.name}")
        self.stages.append(stage)

    def run(self) -> dict[str, dict[str, Any]]:
        for stage in self.stages:
            failed = [name for name in stage.dependencies if self.outcomes.get(name, {}).get("status") != "completed"]
            base = {"schema_version": SCHEMA_VERSION, "run_id": self.run_id, "stage": stage.name, "inputs": list(stage.inputs), "outputs": list(stage.outputs), "writable_roots": list(stage.writable_roots), "timeout_seconds": stage.timeout_seconds}
            if failed:
                root = self.ledger.add(stage.name, "dependency", f"blocked by {','.join(failed)}", status="skipped_dependency", caused_by=failed[0])
                self.outcomes[stage.name] = {**base, "status": "skipped_dependency", "exception_id": root.exception_id}
                continue
            try:
                value = stage.action()
                self.outcomes[stage.name] = {**base, "status": "completed", "result": value}
            except BaseException as exc:  # protocol boundary must converge to reporting
                record = self.ledger.add(stage.name, type(exc).__name__, str(exc))
                self.outcomes[stage.name] = {**base, "status": "exception", "exception_id": record.exception_id}
        return self.outcomes


def build_pipeline_dag(run_id: str, ledger: AcceptanceLedger, actions: Mapping[str, Callable[[], Any]], writable_roots: Sequence[Path], timeout_seconds: int = JUDGING_PLATFORM_TIMEOUT_SECONDS) -> StageDag:
    dag = StageDag(run_id, ledger)
    roots = tuple(str(path.resolve()) for path in writable_roots)
    for item in PIPELINE_BLUEPRINT:
        dag.add(Stage(item["name"], actions.get(item["name"], lambda: None), item["dependencies"], item["inputs"], item["outputs"], roots, timeout_seconds))
    return dag


def final_retry(ledger: AcceptanceLedger, retry: Callable[[ExceptionRecord], tuple[bool, Mapping[str, Any]]]) -> None:
    for record in list(ledger.entries):
        if record.status != "deferred":
            continue
        try:
            repaired, evidence = retry(record)
            record.attempts.append({"number": 2, "final_retry": True, **dict(evidence)})
            record.status = "final_retry_repaired" if repaired else "unresolved"
        except BaseException as exc:
            record.attempts.append({"number": 2, "final_retry": True, "error": f"{type(exc).__name__}:{exc}"})
            record.status = "unresolved"


def submission_manifest(root: Path) -> list[dict[str, Any]]:
    root = root.resolve()
    entries = []
    for path in sorted(root.rglob("*")):
        relative_path = path.relative_to(root)
        relative = relative_path.as_posix()
        excluded_prefix = relative.startswith(("work/code/", "work/references/design/", "openspec/", "docs/")) or relative == "c-to-rust-subagent-source-analysis-verify-design.md"
        if path.is_file() and not path.is_symlink() and path.suffix.lower() in SUBMISSION_SUFFIXES and not excluded_prefix and not any(part in {".git", "target", "output", "logs", "result"} for part in relative_path.parts):
            entries.append({"path": relative, "sha256": digest_file(path), "kind": classify_asset(relative)})
    return entries


def classify_asset(relative: str) -> str:
    lowered = relative.lower()
    for marker, kind in (("test", "tests"), ("fixture", "fixtures"), ("template", "templates"), ("skill", "skills"), ("rule", "rules"), ("script", "scripts"), ("prompt", "prompts"), ("config", "config")):
        if marker in lowered:
            return kind
    return "code"


def customization_audit(root: Path, run_id: str, forbidden_terms: Iterable[str], *, injected_control_flows: Iterable[str] = ()) -> dict[str, Any]:
    manifest = submission_manifest(root)
    terms = sorted({term.lower() for term in forbidden_terms if term.strip()}, key=len, reverse=True)
    findings: list[dict[str, Any]] = []
    for entry in manifest:
        path = root / entry["path"]
        text = path.read_text(encoding="utf-8", errors="ignore")
        input_contract = entry["path"] in {"INSTRUCTION.md", "INSTRUCTION.linux.md", "README.md", "work/design/README.md"}
        haystacks = (("path", entry["path"].lower()), ("content", text.lower()))
        for location, haystack in haystacks:
            for term in terms:
                if term in haystack and not input_contract:
                    findings.append({"path": entry["path"], "location": location, "category": "target-term", "term": term, "disposition": "unresolved"})
        if path.suffix.lower() == ".py":
            try:
                tree = ast.parse(text)
                for node in ast.walk(tree):
                    if not isinstance(node, ast.If):
                        continue
                    names = {item.id.lower() for item in ast.walk(node.test) if isinstance(item, ast.Name)}
                    names.update(item.attr.lower() for item in ast.walk(node.test) if isinstance(item, ast.Attribute))
                    if any(any(marker in name for marker in ("project_name", "project_identity", "profile_identity")) for name in names):
                        findings.append({"path": entry["path"], "location": f"control-flow:{node.lineno}", "category": "identity-dispatch", "disposition": "unresolved"})
            except SyntaxError:
                findings.append({"path": entry["path"], "location": "parse", "category": "scanner-parse-error", "disposition": "unresolved"})
    for value in injected_control_flows:
        findings.append({"path": "<injected>", "location": "control-flow", "category": value, "disposition": "unresolved"})
    kinds = {item["kind"] for item in manifest}
    missing_scope = sorted(ASSET_KINDS - kinds - {"paths"})
    return {"schema_version": SCHEMA_VERSION, "run_id": run_id, "manifest": manifest, "manifest_hash": digest_bytes(json.dumps(manifest, sort_keys=True).encode()), "covered_kinds": sorted(kinds), "missing_scope": missing_scope, "findings": findings, "status": "failed" if findings else "passed", "direct_disqualification": bool(findings)}


def record_decision(run_id: str, decision: str, sources: Iterable[Mapping[str, Any]], outcome: str) -> dict[str, Any]:
    items = [dict(item) for item in sources]
    tainted = [item for item in items if item.get("tainted") and item.get("usage") in {"branch", "strategy", "expectation", "verdict"}]
    return {"schema_version": SCHEMA_VERSION, "run_id": run_id, "decision": decision, "sources": items, "outcome": outcome, "status": "rejected" if tainted else "accepted", "tainted_flows": tainted}


def normalized(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: normalized(item) for key, item in sorted(value.items()) if key not in NORMALIZED_FIELDS}
    if isinstance(value, list):
        return [normalized(item) for item in value]
    return value


def repeatability_report(left_id: str, right_id: str, left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    lhs, rhs = normalized(left), normalized(right)
    differences = [] if lhs == rhs else [{"path": "$", "left_hash": digest_bytes(json.dumps(lhs, sort_keys=True).encode()), "right_hash": digest_bytes(json.dumps(rhs, sort_keys=True).encode())}]
    return {"schema_version": SCHEMA_VERSION, "left_run_id": left_id, "right_run_id": right_id, "normalization_whitelist": sorted(NORMALIZED_FIELDS), "differences": differences, "status": "passed" if not differences else "failed"}


NONZERO_COUNTS = ("source_file_count", "public_api_count", "source_test_count", "semantic_invariant_count", "differential_scenario_count", "executed_rust_test_count")
BOOLEAN_GATES = ("api_mapping_complete", "source_test_mapping_complete", "unsupported_functions_empty", "cargo_build_passed", "cargo_test_passed", "differential_passed", "mutation_passed", "repair_integrity_passed", "source_integrity_passed", "layouts_passed", "repeatability_passed", "customization_audit_passed")


def validate_artifact_references(run_id: str, artifacts: Iterable[Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    seen = 0
    for seen, item in enumerate(artifacts, 1):
        path = Path(str(item.get("path", "")))
        if item.get("run_id") != run_id:
            failures.append(f"artifact-{seen}:stale-run")
        if not path.is_file() or path.stat().st_size == 0:
            failures.append(f"artifact-{seen}:missing-or-empty")
        elif item.get("sha256") != digest_file(path):
            failures.append(f"artifact-{seen}:hash-mismatch")
        if item.get("schema_valid") is not True:
            failures.append(f"artifact-{seen}:schema-invalid")
    if seen == 0:
        failures.append("artifacts:empty")
    return failures


def final_verification(run_id: str, evidence: Mapping[str, Any], ledger: AcceptanceLedger) -> dict[str, Any]:
    checks: dict[str, bool] = {name: isinstance(evidence.get(name), int) and evidence[name] > 0 for name in NONZERO_COUNTS}
    checks.update({name: evidence.get(name) is True for name in BOOLEAN_GATES})
    checks["unsafe_ratio_strict"] = isinstance(evidence.get("unsafe_ratio"), (int, float)) and 0 <= evidence["unsafe_ratio"] < 0.10
    checks["current_run_only"] = evidence.get("run_id") == run_id
    unresolved = [asdict(item) for item in ledger.entries if item.status == "unresolved"]
    compliant = all(checks.values()) and not unresolved
    return {"schema_version": SCHEMA_VERSION, "run_id": run_id, "execution_status": "COMPLETED" if not ledger.entries else "COMPLETED_WITH_EXCEPTIONS", "compliance_status": "READY_FOR_EVALUATION" if compliant else "NOT_READY", "checks": checks, "exceptions": unresolved, "evidence": dict(evidence)}


def publish_reports(result_dir: Path, trace_dir: Path, verification: Mapping[str, Any], ledger: AcceptanceLedger) -> None:
    trace_dir.mkdir(parents=True, exist_ok=True)
    result_dir.mkdir(parents=True, exist_ok=True)
    (result_dir / "issues").mkdir(parents=True, exist_ok=True)
    atomic_json(trace_dir / "exception-ledger.json", ledger.payload())
    atomic_json(trace_dir / "final-verification.json", verification)
    exceptions = verification.get("exceptions", [])
    lines = ["# Submission Acceptance", "", f"- execution_status: `{verification['execution_status']}`", f"- compliance_status: `{verification['compliance_status']}`", f"- unresolved: `{len(exceptions)}`", "", "## Residual Exceptions", ""]
    lines.extend(f"- `{item['exception_id']}` stage={item['stage']} cause={item['kind']} detail={item['detail']} attempts={len(item['attempts'])} evidence={','.join(item['evidence']) or 'none'}" for item in exceptions)
    if not exceptions:
        lines.append("- none")
    rendered = "\n".join(lines) + "\n"
    for path in (result_dir / "output.md", result_dir / "issues" / "00-summary.md"):
        path.write_text(rendered, encoding="utf-8")


def validate_report_coherence(result_dir: Path, verification: Mapping[str, Any]) -> list[str]:
    paths = (result_dir / "output.md", result_dir / "issues" / "00-summary.md")
    failures: list[str] = []
    try:
        texts = [path.read_text(encoding="utf-8") for path in paths]
    except OSError as exc:
        return [f"report-missing:{exc}"]
    if texts[0] != texts[1]:
        failures.append("human-reports-conflict")
    for status in (verification.get("execution_status", ""), verification.get("compliance_status", "")):
        if status and any(status not in text for text in texts):
            failures.append(f"report-status-missing:{status}")
    return failures


def fallback_report(result_dir: Path, run_id: str, exc: BaseException) -> dict[str, Any]:
    payload = {"schema_version": SCHEMA_VERSION, "run_id": run_id, "execution_status": "COMPLETED_WITH_EXCEPTIONS", "compliance_status": "NOT_READY", "checks": {}, "exceptions": [{"exception_id": "fallback-0001", "stage": "reporting", "kind": type(exc).__name__, "detail": str(exc), "attempts": [], "evidence": []}]}
    try:
        result_dir.mkdir(parents=True, exist_ok=True)
        atomic_json(result_dir / "fallback-report.json", payload)
    except OSError:
        pass
    return payload


def remove_workspace(workspace: AcceptanceWorkspace) -> None:
    shutil.rmtree(workspace.root, ignore_errors=True)
