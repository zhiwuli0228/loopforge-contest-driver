#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK_DIR="${ROOT_DIR}/work"
RESULT_DIR="${ROOT_DIR}/result"
LOG_DIR="${ROOT_DIR}/logs"
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

TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

NEG_SRC="$TMP_ROOT/no-readme-source"
POS_SRC="$TMP_ROOT/with-readme-source"
mkdir -p "$NEG_SRC" "$POS_SRC"

cat > "$POS_SRC/README.md" <<'README'
# Positive Smoke Source

Task: verify the runner can discover a README from SOURCE_ROOT.
Constraint: no manual config editing is allowed.
Acceptance:
- source_readme_found should be true.
- selected_source_readme should point to this README.
README

run_case() {
  local source_root="$1"
  local expect_found="$2"
  local expect_readme="$3"
  local expect_summary="$4"

  rm -rf "${source_root}/.loopforge"
  rm -f "${RESULT_DIR}/output.md" "${RESULT_DIR}/issues/00-summary.md" "${LOG_DIR}/trace/run-summary.json"

  "$PYTHON_BIN" "${WORK_DIR}/runtime/loopforge_runner.py" \
    --work-dir "${WORK_DIR}" \
    --source-root "${source_root}" \
    --result-dir "${RESULT_DIR}" \
    --log-dir "${LOG_DIR}" \
    --run

  test -f "${RESULT_DIR}/output.md"
  test -f "${RESULT_DIR}/issues/00-summary.md"
  test -f "${LOG_DIR}/trace/run-summary.json"

  grep -q "source_readme_found: \`${expect_found}\`" "${RESULT_DIR}/output.md"
  grep -q "selected_source_readme: \`${expect_readme}\`" "${RESULT_DIR}/output.md"
  grep -q "${expect_summary}" "${RESULT_DIR}/issues/00-summary.md"
}

run_case "$NEG_SRC" "false" "missing" "source README not found"
grep -q '"found": false' "${LOG_DIR}/trace/run-summary.json"

run_case "$POS_SRC" "true" "${POS_SRC}/README.md" "no runnable verification commands were derived from source README or framework defaults"

grep -q '"found": true' "${LOG_DIR}/trace/run-summary.json"
grep -q 'README.md' "${LOG_DIR}/trace/run-summary.json"

echo "smoke test passed"
