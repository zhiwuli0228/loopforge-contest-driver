#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK_DIR="${ROOT_DIR}/work"
RESULT_DIR="${LOOPFORGE_RESULT_DIR:-${ROOT_DIR}/result}"
LOG_DIR="${LOOPFORGE_LOG_DIR:-${ROOT_DIR}/logs}"
SUBMISSION_ROOT_VALUE="${SUBMISSION_ROOT:-${SOURCE_ROOT:-}}"
EXTRA_ARGS=()
HAS_ACTION="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --submission-root)
      SUBMISSION_ROOT_VALUE="$2"
      shift 2
      ;;
    --source-root)
      SUBMISSION_ROOT_VALUE="$2"
      shift 2
      ;;
    --run|--self-check)
      HAS_ACTION="true"
      EXTRA_ARGS+=("$1")
      shift
      ;;
    --help|-h)
      EXTRA_ARGS+=("$1")
      shift
      ;;
    *)
      EXTRA_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ -z "$SUBMISSION_ROOT_VALUE" ]]; then
  PLATFORM_NAME="$(uname -s 2>/dev/null || true)"
  if [[ "$PLATFORM_NAME" == "Linux" && -d "/__CONTEST_PLATFORM_SOURCE_ROOT__/source" ]]; then
    SUBMISSION_ROOT_VALUE="/__CONTEST_PLATFORM_SOURCE_ROOT__/source"
  elif [[ "$PLATFORM_NAME" == "Linux" && -d "/__CONTEST_PLATFORM_SOURCE_ROOT__" ]]; then
    SUBMISSION_ROOT_VALUE="/__CONTEST_PLATFORM_SOURCE_ROOT__"
  else
    SUBMISSION_ROOT_VALUE=""
  fi
fi

if [[ -n "$SUBMISSION_ROOT_VALUE" ]]; then
  export SUBMISSION_ROOT="$SUBMISSION_ROOT_VALUE"
  export SOURCE_ROOT="$SUBMISSION_ROOT_VALUE"
fi

RUNNER_SUBMISSION_ARGS=()
if [[ -n "$SUBMISSION_ROOT_VALUE" ]]; then
  RUNNER_SUBMISSION_ARGS=(--submission-root "${SUBMISSION_ROOT_VALUE}")
fi

if [[ "$HAS_ACTION" == "false" && ! " ${EXTRA_ARGS[*]} " =~ " --help " && ! " ${EXTRA_ARGS[*]} " =~ " -h " ]]; then
  EXTRA_ARGS+=("--run")
fi

mkdir -p "${RESULT_DIR}/issues" "${LOG_DIR}/trace/consistency"
if [[ ! -f "${LOG_DIR}/interaction.md" ]]; then
  printf '# Interaction Log\n\nNo manual interaction.\n' > "${LOG_DIR}/interaction.md"
fi

if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD="python"
else
  printf '[LoopForge] ERROR: Python 3 is not available.\n' >&2
  exit 1
fi

"${PYTHON_CMD}" "${WORK_DIR}/runtime/loopforge_runner.py" \
  --work-dir "${WORK_DIR}" \
  --result-dir "${RESULT_DIR}" \
  --log-dir "${LOG_DIR}" \
  "${RUNNER_SUBMISSION_ARGS[@]}" \
  "${EXTRA_ARGS[@]}"
