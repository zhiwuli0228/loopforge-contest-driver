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

NEG_SRC="$TMP_ROOT/empty-source"
VALID_SRC="$TMP_ROOT/valid-source"
mkdir -p "$NEG_SRC" "$VALID_SRC/src" "$VALID_SRC/tests"

cat > "$VALID_SRC/src/demo.h" <<'README'
void demo_init(void);
int demo_count(void);
README

cat > "$VALID_SRC/src/demo.c" <<'README'
void demo_init(void) {}
int demo_count(void) { return 0; }
README

cat > "$VALID_SRC/tests/test_demo.c" <<'README'
#include <assert.h>
void test_demo_count(void) {
    demo_init();
    assert(demo_count() == 0);
}
README

run_case() {
  local source_root="$1"
  local expect_status="$2"
  shift 2

  rm -f "${RESULT_DIR}/output.md" "${RESULT_DIR}/issues/00-summary.md" "${LOG_DIR}/trace/run-summary.json" "${LOG_DIR}/trace/final-report.md"

  "$PYTHON_BIN" "${WORK_DIR}/runtime/loopforge_runner.py" \
    --work-dir "${WORK_DIR}" \
    --source-root "${source_root}" \
    --result-dir "${RESULT_DIR}" \
    --log-dir "${LOG_DIR}" \
    --run >/dev/null

  test -f "${RESULT_DIR}/output.md"
  test -f "${RESULT_DIR}/issues/00-summary.md"
  test -f "${LOG_DIR}/trace/run-summary.json"
  test -f "${LOG_DIR}/trace/final-report.md"

  grep -q "Status: ${expect_status}" "${RESULT_DIR}/output.md"
  for issue_code in "$@"; do
    grep -q "${issue_code}" "${RESULT_DIR}/issues/00-summary.md"
  done
}

check_self() {
  local source_root="$1"
  local self_check_path="${LOG_DIR}/trace/consistency/00-preflight-self-check.json"
  rm -f "$self_check_path"
  "$PYTHON_BIN" "${WORK_DIR}/runtime/loopforge_runner.py" \
    --work-dir "${WORK_DIR}" \
    --source-root "$source_root" \
    --result-dir "${RESULT_DIR}" \
    --log-dir "${LOG_DIR}" \
    --self-check >/dev/null
  "$PYTHON_BIN" -c 'import json,sys; p=json.load(open(sys.argv[1], encoding="utf-8")); assert p["ok"] and len(p["design_readme_sha256"]) == 64' "$self_check_path"
}

run_case "$NEG_SRC" "BLOCKED_WITH_REPORT" "source_root_missing"
run_case "$VALID_SRC" "DEGRADED_FINAL_REPORT_READY"
check_self "$VALID_SRC"

echo "smoke test passed"
