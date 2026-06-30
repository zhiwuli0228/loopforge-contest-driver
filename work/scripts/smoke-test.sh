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
VALID_SRC="$TMP_ROOT/valid-source"
mkdir -p "$NEG_SRC" "$POS_SRC" "$VALID_SRC/src" "$VALID_SRC/tests"

cat > "$POS_SRC/README.md" <<'README'
# Positive Smoke Source

Task: verify README-only input is insufficient without the FlashDB source layout.
README

cat > "$VALID_SRC/README.md" <<'README'
# Valid Fallback Source

Task: migrate this FlashDB subset into Rust and pass all READY gates.
README

cat > "$VALID_SRC/src/flashdb.h" <<'README'
void flashdb_new(void);
int flashdb_set(void);
const char *flashdb_get(void);
int flashdb_delete(void);
int flashdb_count(void);
README

cat > "$VALID_SRC/src/flashdb.c" <<'README'
void flashdb_new(void) {}
int flashdb_set(void) { return 0; }
const char *flashdb_get(void) { return 0; }
int flashdb_delete(void) { return 0; }
int flashdb_count(void) { return 0; }
README

cat > "$VALID_SRC/tests/test_flashdb.c" <<'README'
/* create, set/get, overwrite, delete */
README

run_case() {
  local source_root="$1"
  local expect_status="$2"
  shift 2

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

  grep -q "status: \`${expect_status}\`" "${RESULT_DIR}/output.md"
  for issue_code in "$@"; do
    grep -q "${issue_code}" "${RESULT_DIR}/issues/00-summary.md"
  done
}

run_case "$NEG_SRC" "BLOCKED_WITH_REPORT" "readme_missing" "flashdb_layout_missing"
run_case "$POS_SRC" "BLOCKED_WITH_REPORT" "flashdb_layout_missing"
run_case "$VALID_SRC" "READY_FOR_EVALUATION" "no_blocking_issues"

echo "smoke test passed"
