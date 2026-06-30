#!/usr/bin/env bash
set -euo pipefail

WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT_DIR="$(cd "${WORK_DIR}/.." && pwd)"
SOURCE_ROOT="${ROOT_DIR}/code"
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
      ROOT_DIR="$(cd "${WORK_DIR}/.." && pwd)"
      shift 2
      ;;
    --source-root)
      SOURCE_ROOT="$2"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ ! "$SOURCE_ROOT" = /* ]]; then
  SOURCE_ROOT="${ROOT_DIR}/${SOURCE_ROOT}"
fi

ARTIFACT_DIR="$SOURCE_ROOT/.loopforge"
PARENT_ARTIFACT_DIR="${WORK_DIR}/code/.loopforge"
PARENT_ARTIFACT_PREEXISTED="false"

if [[ -e "$PARENT_ARTIFACT_DIR" ]]; then
  PARENT_ARTIFACT_PREEXISTED="true"
fi

bash "$WORK_DIR/scripts/bootstrap.sh" --source-root "$SOURCE_ROOT"
"$PYTHON_BIN" "$WORK_DIR/runtime/loopforge_runner.py" --work-dir "$WORK_DIR" --source-root "$SOURCE_ROOT" --snapshot smoke
"$PYTHON_BIN" "$WORK_DIR/runtime/loopforge_runner.py" --work-dir "$WORK_DIR" --source-root "$SOURCE_ROOT" --verify
"$PYTHON_BIN" "$WORK_DIR/runtime/loopforge_runner.py" --work-dir "$WORK_DIR" --source-root "$SOURCE_ROOT" --finalize

required_paths=(
  "$ARTIFACT_DIR"
  "$ARTIFACT_DIR/runtime/loopforge_runner.py"
  "$ARTIFACT_DIR/state/loop-state.json"
  "$ARTIFACT_DIR/state/config-check-summary.json"
  "$ARTIFACT_DIR/state/profile-check-summary.json"
  "$ARTIFACT_DIR/state/work-package-summary.json"
  "$ARTIFACT_DIR/state/verification-summary.json"
  "$ARTIFACT_DIR/gates/gate-events.md"
  "$ARTIFACT_DIR/plan/mode-artifacts.md"
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

if [[ "$PARENT_ARTIFACT_PREEXISTED" == "false" && -e "$PARENT_ARTIFACT_DIR" ]]; then
  echo "smoke test failed: runtime artifacts escaped into parent code artifact path" >&2
  exit 1
fi

if [[ -e "$WORK_DIR/work" ]]; then
  echo "smoke test failed: unexpected nested work directory created at $WORK_DIR/work" >&2
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

if ! grep -q "## Mode Artifact Summary" "$ARTIFACT_DIR/reports/final-report.md"; then
  echo "smoke test failed: final report is missing mode artifact summary section" >&2
  exit 1
fi

if ! grep -q "# Mode Artifacts" "$ARTIFACT_DIR/plan/mode-artifacts.md"; then
  echo "smoke test failed: mode artifact index was not initialized" >&2
  exit 1
fi

echo "smoke test passed"
