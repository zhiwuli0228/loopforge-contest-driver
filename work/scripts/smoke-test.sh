#!/usr/bin/env bash
set -euo pipefail

WORK_DIR="work"
CODE_DIR="code"
ARTIFACT_DIR=""
PYTHON_BIN="${PYTHON_BIN:-}"

if [[ -z "$PYTHON_BIN" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "python interpreter not found" >&2
    exit 1
  fi
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --work-dir)
      WORK_DIR="$2"
      shift 2
      ;;
    --code-dir)
      CODE_DIR="$2"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

ARTIFACT_DIR="$CODE_DIR/.loopforge"

bash "$WORK_DIR/scripts/bootstrap.sh" --work-dir "$WORK_DIR" --code-dir "$CODE_DIR"
"$PYTHON_BIN" "$WORK_DIR/runtime/loopforge_runner.py" --work-dir "$WORK_DIR" --code-dir "$CODE_DIR" --snapshot smoke
"$PYTHON_BIN" "$WORK_DIR/runtime/loopforge_runner.py" --work-dir "$WORK_DIR" --code-dir "$CODE_DIR" --verify
"$PYTHON_BIN" "$WORK_DIR/runtime/loopforge_runner.py" --work-dir "$WORK_DIR" --code-dir "$CODE_DIR" --finalize

required_paths=(
  "$ARTIFACT_DIR"
  "$ARTIFACT_DIR/runtime/loopforge_runner.py"
  "$ARTIFACT_DIR/state/loop-state.json"
  "$ARTIFACT_DIR/state/config-check-summary.json"
  "$ARTIFACT_DIR/state/profile-check-summary.json"
  "$ARTIFACT_DIR/state/work-package-summary.json"
  "$ARTIFACT_DIR/state/verification-summary.json"
  "$ARTIFACT_DIR/gates/gate-events.md"
  "$ARTIFACT_DIR/snapshots/smoke.diff"
  "$ARTIFACT_DIR/reports/final-report.md"
)

for path in "${required_paths[@]}"; do
  if [[ ! -e "$path" ]]; then
    echo "smoke test failed: missing required artifact: $path" >&2
    exit 1
  fi
done

if [[ -e "$WORK_DIR/.loopforge" ]]; then
  echo "smoke test failed: runtime artifacts escaped into $WORK_DIR/.loopforge" >&2
  exit 1
fi

if ! grep -q "FINALIZE" "$ARTIFACT_DIR/gates/gate-events.md"; then
  echo "smoke test failed: gate log does not contain FINALIZE event" >&2
  exit 1
fi

if ! grep -q "## Contract Validation" "$ARTIFACT_DIR/reports/final-report.md"; then
  echo "smoke test failed: final report is missing contract validation section" >&2
  exit 1
fi

if ! grep -q "BLOCKED_WITH_REPORT" "$ARTIFACT_DIR/reports/final-report.md"; then
  echo "smoke test failed: final report did not record blocked verification" >&2
  exit 1
fi

echo "smoke test passed"
