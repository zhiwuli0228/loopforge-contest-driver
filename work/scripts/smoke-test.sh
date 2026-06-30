#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK_DIR="${ROOT_DIR}/work"
RESULT_DIR="${WORK_DIR}/result"
LOG_DIR="${WORK_DIR}/logs"
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

Output project: demo_rust
README

cat > "$VALID_SRC/README.md" <<'README'
# Valid Fallback Source

Project Name: Demo C Library
Output project: demo_rust
Source directories: src
Test directories: tests
README

cat > "$VALID_SRC/src/demo.h" <<'README'
void demo_init(void);
int demo_count(void);
README

cat > "$VALID_SRC/src/demo.c" <<'README'
void demo_init(void) {}
int demo_count(void) { return 0; }
README

cat > "$VALID_SRC/tests/test_demo.c" <<'README'
void test_demo_count(void) {
    demo_init();
    demo_count();
}
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

run_case "$NEG_SRC" "BLOCKED_WITH_REPORT" "readme_missing" "source_layout_missing"
run_case "$POS_SRC" "BLOCKED_WITH_REPORT" "source_layout_missing"
run_case "$VALID_SRC" "READY_FOR_EVALUATION" "no_blocking_issues"

echo "smoke test passed"
