#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK_DIR="${ROOT_DIR}/work"
RESULT_DIR="${ROOT_DIR}/result"
LOG_DIR="${ROOT_DIR}/logs"
SOURCE_ROOT_VALUE="${SOURCE_ROOT:-}"
EXTRA_ARGS=()
HAS_ACTION="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source-root)
      SOURCE_ROOT_VALUE="$2"
      shift 2
      ;;
    --run|--init|--self-check|--detect|--verify|--finalize|--snapshot)
      HAS_ACTION="true"
      EXTRA_ARGS+=("$1")
      if [[ "$1" == "--snapshot" ]]; then
        EXTRA_ARGS+=("$2")
        shift 2
      else
        shift
      fi
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

if [[ -z "$SOURCE_ROOT_VALUE" ]]; then
  PLATFORM_NAME="$(uname -s 2>/dev/null || true)"
  if [[ "$PLATFORM_NAME" == "Linux" && -d "/__CONTEST_PLATFORM_SOURCE_ROOT__/source" ]]; then
    SOURCE_ROOT_VALUE="/__CONTEST_PLATFORM_SOURCE_ROOT__/source"
  elif [[ "$PLATFORM_NAME" == "Linux" && -d "/__CONTEST_PLATFORM_SOURCE_ROOT__" ]]; then
    SOURCE_ROOT_VALUE="/__CONTEST_PLATFORM_SOURCE_ROOT__"
  elif [[ "$PLATFORM_NAME" != "Linux" && -d "${ROOT_DIR}/work/code" ]]; then
    SOURCE_ROOT_VALUE="${ROOT_DIR}/work/code"
  else
    SOURCE_ROOT_VALUE=""
  fi
fi

if [[ -n "$SOURCE_ROOT_VALUE" ]]; then
export SOURCE_ROOT="$SOURCE_ROOT_VALUE"
fi

RUNNER_SOURCE_ARGS=()
if [[ -n "$SOURCE_ROOT_VALUE" ]]; then
  RUNNER_SOURCE_ARGS=(--source-root "${SOURCE_ROOT_VALUE}")
fi

if [[ "$HAS_ACTION" == "false" && ! " ${EXTRA_ARGS[*]} " =~ " --help " && ! " ${EXTRA_ARGS[*]} " =~ " -h " ]]; then
  EXTRA_ARGS+=("--run")
fi

mkdir -p "${RESULT_DIR}/issues" "${LOG_DIR}/trace/c-to-rust"
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
  "${RUNNER_SOURCE_ARGS[@]}" \
  "${EXTRA_ARGS[@]}"
